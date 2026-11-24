from __future__ import annotations

import json
from io import BytesIO
from typing import Literal

import pdfplumber
from dotenv import load_dotenv
from openai import OpenAI, OpenAIError
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from prompts import SYSTEM_PROMPT, build_user_prompt


PASS_THRESHOLD = 75
MAX_DOCUMENT_CHARS = 100_000
MODEL_NAME = "gpt-6-luna"


EvidenceStatus = Literal[
    "подтверждено",
    "частично подтверждено",
    "не подтверждено",
    "недостаточно информации",
]


class EvaluationError(Exception):
    """User-facing evaluation error."""


class EvidenceItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement: str = Field(min_length=1)
    status: EvidenceStatus
    quote: str | None = None
    reasoning: str = Field(min_length=1)


class EvaluationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score: int = Field(ge=0, le=100)
    summary: str = Field(min_length=1)
    strengths: list[str]
    gaps: list[str]
    evidence: list[EvidenceItem]
    missing_information: list[str]
    interview_questions: list[str] = Field(min_length=5, max_length=10)


EVALUATION_JSON_SCHEMA = {
    "name": "resume_evaluation",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "score",
            "summary",
            "strengths",
            "gaps",
            "evidence",
            "missing_information",
            "interview_questions",
        ],
        "properties": {
            "score": {"type": "integer", "minimum": 0, "maximum": 100},
            "summary": {"type": "string"},
            "strengths": {"type": "array", "items": {"type": "string"}},
            "gaps": {"type": "array", "items": {"type": "string"}},
            "evidence": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["requirement", "status", "quote", "reasoning"],
                    "properties": {
                        "requirement": {"type": "string"},
                        "status": {
                            "type": "string",
                            "enum": [
                                "подтверждено",
                                "частично подтверждено",
                                "не подтверждено",
                                "недостаточно информации",
                            ],
                        },
                        "quote": {"type": ["string", "null"]},
                        "reasoning": {"type": "string"},
                    },
                },
            },
            "missing_information": {"type": "array", "items": {"type": "string"}},
            "interview_questions": {
                "type": "array",
                "minItems": 5,
                "maxItems": 10,
                "items": {"type": "string"},
            },
        },
    },
}


def compute_verdict(score: int) -> str:
    return "подходит" if score >= PASS_THRESHOLD else "не подходит"


def _normalize_document_text(text: str) -> str:
    text = text.replace("\x00", "").strip()
    if not text:
        raise EvaluationError("Документ пустой или не содержит извлекаемого текста.")
    if len(text) > MAX_DOCUMENT_CHARS:
        raise EvaluationError(
            f"Документ слишком большой: максимум {MAX_DOCUMENT_CHARS:,} символов."
        )
    return text


def _extract_txt(data: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1251"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise EvaluationError("Не удалось прочитать TXT-файл. Сохраните его в UTF-8.")


def _extract_pdf(data: bytes) -> str:
    try:
        with pdfplumber.open(BytesIO(data)) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
    except Exception as exc:
        raise EvaluationError(f"Не удалось прочитать PDF: {exc}") from exc

    text = "\n\n".join(page.strip() for page in pages if page.strip())
    if not text.strip():
        raise EvaluationError(
            "PDF не содержит извлекаемого текста. Загрузите текстовый PDF или TXT."
        )
    return text


def extract_text_from_upload(uploaded_file) -> str:
    file_name = getattr(uploaded_file, "name", "document")
    suffix = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""

    try:
        data = uploaded_file.getvalue()
    except Exception as exc:
        raise EvaluationError(f"Не удалось прочитать файл {file_name}: {exc}") from exc

    if not data:
        raise EvaluationError(f"Файл {file_name} пустой.")

    if suffix == "txt":
        text = _extract_txt(data)
    elif suffix == "pdf":
        text = _extract_pdf(data)
    else:
        raise EvaluationError("Поддерживаются только TXT и PDF.")

    return _normalize_document_text(text)


def _client() -> OpenAI:
    load_dotenv()
    return OpenAI()


def _message_content_to_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(part.get("text", "") for part in content if isinstance(part, dict))
    return str(content or "")


def _call_model(messages: list[dict[str, str]]) -> str:
    try:
        response = _client().chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0,
            reasoning_effort="none",
            response_format={"type": "json_schema", "json_schema": EVALUATION_JSON_SCHEMA},
        )
    except OpenAIError as exc:
        raise EvaluationError(f"Ошибка API OpenAI: {exc}") from exc
    except Exception as exc:
        raise EvaluationError(f"Не удалось вызвать модель: {exc}") from exc

    if not response.choices:
        raise EvaluationError("Модель вернула пустой ответ.")

    return _message_content_to_text(response.choices[0].message.content).strip()


def _parse_result(raw_response: str) -> EvaluationResult:
    try:
        json.loads(raw_response)
    except json.JSONDecodeError as exc:
        raise EvaluationError(f"Ответ модели не является валидным JSON: {exc}") from exc

    try:
        return EvaluationResult.model_validate_json(raw_response)
    except ValidationError as exc:
        raise EvaluationError(f"Ответ модели не соответствует схеме: {exc}") from exc


def evaluate_resume(vacancy_text: str, resume_text: str) -> EvaluationResult:
    vacancy_text = _normalize_document_text(vacancy_text)
    resume_text = _normalize_document_text(resume_text)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(vacancy_text, resume_text)},
    ]

    last_error: EvaluationError | None = None
    for attempt in range(2):
        raw_response = _call_model(messages)
        try:
            return _parse_result(raw_response)
        except EvaluationError as exc:
            last_error = exc
            if attempt == 0:
                messages.append({"role": "assistant", "content": raw_response})
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "Предыдущий ответ не прошел проверку. "
                            f"Ошибка: {exc}. Верни исправленный ответ: только JSON, строго по схеме."
                        ),
                    }
                )

    raise EvaluationError(
        f"Модель дважды вернула невалидный структурированный ответ. {last_error}"
    )

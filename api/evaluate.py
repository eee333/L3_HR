from __future__ import annotations

import base64
import binascii
import json
from http.server import BaseHTTPRequestHandler
from typing import Any

from evaluator import (
    EvaluationError,
    compute_verdict,
    evaluate_resume,
    extract_text_from_upload,
)


MAX_REQUEST_BYTES = 4_000_000


class UploadedFile:
    def __init__(self, name: str, data: bytes) -> None:
        self.name = name
        self._data = data

    def getvalue(self) -> bytes:
        return self._data


def _decode_file(payload: Any, field_name: str) -> UploadedFile:
    if not isinstance(payload, dict):
        raise EvaluationError(f"Поле {field_name} должно содержать файл.")

    name = payload.get("name")
    encoded = payload.get("content_base64")
    if not isinstance(name, str) or not name.strip():
        raise EvaluationError(f"У файла в поле {field_name} отсутствует имя.")
    if not isinstance(encoded, str) or not encoded:
        raise EvaluationError(f"Файл в поле {field_name} пустой.")

    try:
        data = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise EvaluationError(f"Не удалось прочитать файл {name}.") from exc

    return UploadedFile(name, data)


def _read_json(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    raw_length = handler.headers.get("Content-Length", "0")
    try:
        content_length = int(raw_length)
    except ValueError as exc:
        raise EvaluationError("Некорректный размер запроса.") from exc

    if content_length <= 0:
        raise EvaluationError("Пустой запрос.")
    if content_length > MAX_REQUEST_BYTES:
        raise EvaluationError("Файл слишком большой для загрузки. Уменьшите размер файла.")

    try:
        payload = json.loads(handler.rfile.read(content_length))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EvaluationError("Запрос должен содержать валидный JSON.") from exc

    if not isinstance(payload, dict):
        raise EvaluationError("Некорректный формат запроса.")
    return payload


def _evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    vacancy_text = payload.get("vacancy_text")
    vacancy_file = payload.get("vacancy_file")
    if isinstance(vacancy_text, str) and vacancy_text.strip():
        vacancy = vacancy_text
    elif vacancy_file is not None:
        vacancy = extract_text_from_upload(_decode_file(vacancy_file, "vacancy_file"))
    else:
        raise EvaluationError("Добавьте описание вакансии текстом или загрузите TXT/PDF.")

    resume = extract_text_from_upload(_decode_file(payload.get("resume"), "resume"))
    result = evaluate_resume(vacancy, resume)
    return {
        "file_name": payload["resume"]["name"],
        "result": result.model_dump(),
        "verdict": compute_verdict(result.score),
    }


class handler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802 - Vercel handler API
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.end_headers()

    def do_POST(self) -> None:  # noqa: N802 - Vercel handler API
        try:
            payload = _read_json(self)
            self._send_json(200, {"ok": True, "data": _evaluate(payload)})
        except EvaluationError as exc:
            self._send_json(400, {"ok": False, "error": str(exc)})
        except Exception:
            self._send_json(500, {"ok": False, "error": "Не удалось обработать запрос."})

    def do_GET(self) -> None:  # noqa: N802 - Vercel handler API
        self._send_json(405, {"ok": False, "error": "Используйте POST-запрос."})

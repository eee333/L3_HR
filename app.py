from __future__ import annotations

import streamlit as st

from evaluator import (
    PASS_THRESHOLD,
    EvaluationError,
    compute_verdict,
    evaluate_resume,
    extract_text_from_upload,
)


st.set_page_config(page_title="AI-рекрутер", page_icon="HR", layout="wide")


def _render_list(items: list[str], empty_text: str = "Нет данных") -> None:
    if not items:
        st.write(empty_text)
        return

    for item in items:
        st.markdown(f"- {item}")


def _sync_vacancy_file() -> None:
    vacancy_file = st.session_state.get("vacancy_file")
    if not vacancy_file:
        return

    current_signature = f"{vacancy_file.name}:{vacancy_file.size}"
    if st.session_state.get("vacancy_file_signature") == current_signature:
        return

    try:
        st.session_state["vacancy_text"] = extract_text_from_upload(vacancy_file)
        st.session_state["vacancy_file_signature"] = current_signature
    except Exception as exc:
        st.session_state["vacancy_file_error"] = str(exc)


def _render_result(file_name: str, result: dict | None, error: str | None) -> None:
    with st.expander(file_name, expanded=True):
        if error:
            st.error(error)
            return

        if not result:
            st.info("Результат отсутствует.")
            return

        verdict = compute_verdict(result["score"])
        verdict_color = "#15803d" if verdict == "подходит" else "#b91c1c"

        score_col, verdict_col = st.columns([1, 3])
        with score_col:
            st.metric("Балл", f"{result['score']}/100")
        with verdict_col:
            st.markdown(
                f"""
                <div style="font-size: 1.35rem; font-weight: 700; color: {verdict_color}; padding-top: 0.55rem;">
                    {verdict}
                </div>
                <div style="color: #6b7280;">Порог: {PASS_THRESHOLD}</div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("### Краткий вывод")
        st.write(result["summary"])

        strengths_col, gaps_col = st.columns(2)
        with strengths_col:
            st.markdown("### Сильные стороны")
            _render_list(result["strengths"])
        with gaps_col:
            st.markdown("### Пробелы")
            _render_list(result["gaps"])

        st.markdown("### Подтверждающие факты")
        evidence_rows = [
            {
                "Требование": item["requirement"],
                "Статус": item["status"],
                "Цитата": item["quote"] or "",
                "Обоснование": item["reasoning"],
            }
            for item in result["evidence"]
        ]
        st.dataframe(evidence_rows, use_container_width=True, hide_index=True)

        st.markdown("### Недостающие сведения")
        _render_list(result["missing_information"])

        st.markdown("### Вопросы для интервью")
        if result["interview_questions"]:
            for index, question in enumerate(result["interview_questions"], start=1):
                st.markdown(f"{index}. {question}")
        else:
            st.write("Нет данных")


st.title("AI-рекрутер")

st.subheader("Описание вакансии")
vacancy_file = st.file_uploader(
    "Загрузите описание вакансии TXT/PDF",
    type=["txt", "pdf"],
    key="vacancy_file",
    on_change=_sync_vacancy_file,
)

if vacancy_file:
    _sync_vacancy_file()

if st.session_state.get("vacancy_file_error"):
    st.error(st.session_state.pop("vacancy_file_error"))

vacancy_text = st.text_area(
    "Текст вакансии",
    key="vacancy_text",
    height=260,
    placeholder="Вставьте или отредактируйте описание вакансии",
)

st.subheader("Резюме кандидатов")
resume_files = st.file_uploader(
    "Загрузите одно или несколько резюме TXT/PDF",
    type=["txt", "pdf"],
    accept_multiple_files=True,
)

evaluate_clicked = st.button("Оценить", type="primary")

if evaluate_clicked:
    st.session_state["results"] = []

    if not vacancy_text.strip():
        st.error("Добавьте описание вакансии текстом или загрузите TXT/PDF.")
    elif not resume_files:
        st.error("Загрузите хотя бы одно резюме.")
    else:
        progress = st.progress(0, text="Подготовка")

        for index, resume_file in enumerate(resume_files, start=1):
            progress.progress(
                (index - 1) / len(resume_files),
                text=f"Обработка: {resume_file.name}",
            )
            try:
                resume_text = extract_text_from_upload(resume_file)
                result = evaluate_resume(vacancy_text, resume_text)
                st.session_state["results"].append(
                    {"file_name": resume_file.name, "result": result.model_dump(), "error": None}
                )
            except EvaluationError as exc:
                st.session_state["results"].append(
                    {"file_name": resume_file.name, "result": None, "error": str(exc)}
                )
            except Exception as exc:
                st.session_state["results"].append(
                    {
                        "file_name": resume_file.name,
                        "result": None,
                        "error": f"Не удалось обработать резюме: {exc}",
                    }
                )

        progress.progress(1.0, text="Готово")

if st.session_state.get("results"):
    st.subheader("Результаты")
    for item in st.session_state["results"]:
        _render_result(item["file_name"], item["result"], item["error"])

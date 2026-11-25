from __future__ import annotations

import html
import json
import re
from datetime import datetime


def _text(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def _list(items: list[str], empty: str = "Нет данных") -> str:
    if not items:
        return f"<p>{_text(empty)}</p>"
    return "<ul>" + "".join(f"<li>{_text(item)}</li>" for item in items) + "</ul>"


def _safe_filename(value: str) -> str:
    stem = re.sub(r"[^\w.-]+", "_", value, flags=re.UNICODE).strip("._") or "candidate"
    return f"результат_{stem[:80]}.html"


def build_result_html(candidate: dict, *, generated_at: datetime | None = None) -> str:
    """Build a self-contained, responsive HTML report without external assets."""
    result = candidate["result"]
    score = int(result["score"])
    verdict = str(candidate.get("verdict") or ("подходит" if score >= 75 else "не подходит"))
    passed = score >= 75
    generated = (generated_at or datetime.now().astimezone()).strftime("%d.%m.%Y %H:%M")
    rows = "".join(
        "<tr>"
        f"<td>{_text(item.get('requirement'))}</td>"
        f"<td>{_text(item.get('status'))}</td>"
        f"<td>{_text(item.get('quote'))}</td>"
        f"<td>{_text(item.get('reasoning'))}</td></tr>"
        for item in result.get("evidence", [])
    ) or '<tr><td colspan="4">Нет данных</td></tr>'
    filename = _text(str(candidate.get("file_name", "резюме")))
    safe_filename = json.dumps(_safe_filename(str(candidate.get("file_name", "резюме"))), ensure_ascii=False)
    tone = "good" if passed else "bad"
    return f"""<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Результат оценки — {filename}</title><style>
:root{{font-family:Arial,Helvetica,sans-serif;color:#172033;background:#f3f6fb;font-size:16px}}*{{box-sizing:border-box}}body{{margin:0;padding:24px}}main{{max-width:1000px;margin:0 auto;background:#fff;border:1px solid #e0e6ef;border-radius:18px;padding:clamp(20px,5vw,48px);box-shadow:0 12px 36px #17203312}}h1{{font-size:clamp(1.7rem,4vw,2.5rem);margin:0 0 8px;overflow-wrap:anywhere}}h2{{font-size:1.2rem;margin:30px 0 12px}}p,li,td{{line-height:1.55}}.muted{{color:#667085}}.score{{display:flex;align-items:center;gap:16px;flex-wrap:wrap;margin:24px 0}}.number{{font-size:2.6rem;font-weight:800;letter-spacing:-.04em}}.badge{{font-weight:700;color:{'#147a4b' if passed else '#b42332'}}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:24px}}.table-wrap{{overflow-x:auto;border:1px solid #e0e6ef;border-radius:10px}}table{{width:100%;min-width:680px;border-collapse:collapse}}th,td{{padding:12px;text-align:left;vertical-align:top;border-bottom:1px solid #e0e6ef}}th{{background:#f7f9fc;color:#475467;font-size:.8rem}}tr:last-child td{{border:0}}footer{{margin-top:32px;color:#667085;font-size:.85rem}}@media(max-width:650px){{body{{padding:10px}}main{{border-radius:12px;padding:20px 16px}}.grid{{grid-template-columns:1fr;gap:0}}.number{{font-size:2.2rem}}}}
</style></head><body><main>
<p class="muted">AI-рекрутер · отчёт по кандидату</p><h1>{filename}</h1>
<div class="score"><span class="number">{score}/100</span><span class="badge">{_text(verdict)}</span><span class="muted">Порог соответствия: 75</span></div>
<h2>Краткий вывод</h2><p>{_text(result.get('summary'))}</p>
<div class="grid"><section><h2>Сильные стороны</h2>{_list(result.get('strengths', []))}</section><section><h2>Пробелы</h2>{_list(result.get('gaps', []))}</section></div>
<h2>Подтверждающие факты</h2><div class="table-wrap"><table><thead><tr><th>Требование</th><th>Статус</th><th>Цитата</th><th>Обоснование</th></tr></thead><tbody>{rows}</tbody></table></div>
<div class="grid"><section><h2>Недостающие сведения</h2>{_list(result.get('missing_information', []))}</section><section><h2>Вопросы для интервью</h2>{_list(result.get('interview_questions', []))}</section></div>
<footer>Сформировано {generated}</footer></main><script>const n={safe_filename};document.title='Результат оценки';</script></body></html>"""


def result_filename(candidate: dict) -> str:
    return _safe_filename(str(candidate.get("file_name", "резюме")))

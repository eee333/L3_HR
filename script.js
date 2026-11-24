const vacancyFileInput = document.querySelector("#vacancy-file");
const vacancyText = document.querySelector("#vacancy-text");
const vacancyFileName = document.querySelector("#vacancy-file-name");
const resumeFileInput = document.querySelector("#resume-files");
const resumeList = document.querySelector("#resume-list");
const evaluateButton = document.querySelector("#evaluate-button");
const statusElement = document.querySelector("#status");
const globalError = document.querySelector("#global-error");
const results = document.querySelector("#results");
const resultsList = document.querySelector("#results-list");
const resultsCount = document.querySelector("#results-count");

let vacancyFile = null;
let resumeFiles = [];

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#039;", '"': "&quot;" }[char]));
}

function listHtml(items, emptyText = "Нет данных") {
  if (!items || !items.length) return `<p>${emptyText}</p>`;
  return `<ul>${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`;
}

function statusClass(status) {
  if (status === "подтверждено") return "confirmed";
  if (status === "частично подтверждено") return "partial";
  if (status === "не подтверждено") return "not-confirmed";
  return "missing";
}

function resultHtml(item) {
  if (item.error) {
    return `<details class="result" open><summary>${escapeHtml(item.file_name)}<span class="summary-meta bad">Ошибка</span></summary><div class="result-body"><div class="alert error">${escapeHtml(item.error)}</div></div></details>`;
  }

  const result = item.result;
  const good = item.verdict === "подходит";
  const evidence = (result.evidence || []).map((row) => `<tr><td>${escapeHtml(row.requirement)}</td><td><span class="status-pill ${statusClass(row.status)}">${escapeHtml(row.status)}</span></td><td>${escapeHtml(row.quote || "")}</td><td>${escapeHtml(row.reasoning)}</td></tr>`).join("");
  return `<details class="result" open>
    <summary>${escapeHtml(item.file_name)}<span class="summary-meta ${good ? "good" : "bad"}">${escapeHtml(item.verdict)} · ${result.score}/100</span></summary>
    <div class="result-body">
      <div class="score-row"><span class="score">${result.score}/100</span><span class="verdict ${good ? "good" : "bad"}">${escapeHtml(item.verdict)}</span><span class="threshold">Порог: 75</span></div>
      <h3>Краткий вывод</h3><p>${escapeHtml(result.summary)}</p>
      <div class="columns"><div><h3>Сильные стороны</h3>${listHtml(result.strengths)}</div><div><h3>Пробелы</h3>${listHtml(result.gaps)}</div></div>
      <h3>Подтверждающие факты</h3>
      <div class="table-wrap"><table><thead><tr><th>Требование</th><th>Статус</th><th>Цитата</th><th>Обоснование</th></tr></thead><tbody>${evidence || "<tr><td colspan=4>Нет данных</td></tr>"}</tbody></table></div>
      <div class="columns"><div><h3>Недостающие сведения</h3>${listHtml(result.missing_information)}</div><div><h3>Вопросы для интервью</h3>${listHtml(result.interview_questions)}</div></div>
    </div>
  </details>`;
}

function bytesToBase64(buffer) {
  let binary = "";
  const bytes = new Uint8Array(buffer);
  const chunkSize = 0x8000;
  for (let i = 0; i < bytes.length; i += chunkSize) binary += String.fromCharCode(...bytes.subarray(i, i + chunkSize));
  return btoa(binary);
}

async function encodeFile(file) {
  return { name: file.name, content_base64: bytesToBase64(await file.arrayBuffer()) };
}

vacancyFileInput.addEventListener("change", async () => {
  vacancyFile = vacancyFileInput.files[0] || null;
  vacancyFileName.hidden = !vacancyFile;
  vacancyFileName.textContent = vacancyFile ? `Выбран файл: ${vacancyFile.name}` : "";
  if (vacancyFile && vacancyFile.name.toLowerCase().endsWith(".txt")) vacancyText.value = await vacancyFile.text();
});

resumeFileInput.addEventListener("change", () => {
  resumeFiles = Array.from(resumeFileInput.files || []);
  resumeList.classList.toggle("empty-state", !resumeFiles.length);
  resumeList.innerHTML = resumeFiles.length ? resumeFiles.map((file) => `<div class="file-item"><span class="file-badge">${file.name.toLowerCase().endsWith(".pdf") ? "PDF" : "TXT"}</span><span>${escapeHtml(file.name)}</span></div>`).join("") : "Файлы ещё не выбраны";
});

evaluateButton.addEventListener("click", async () => {
  globalError.hidden = true;
  results.hidden = true;
  resultsList.innerHTML = "";
  const vacancy = vacancyText.value.trim();
  if (!vacancy && !vacancyFile) { globalError.textContent = "Добавьте описание вакансии текстом или загрузите TXT/PDF."; globalError.hidden = false; return; }
  if (!resumeFiles.length) { globalError.textContent = "Загрузите хотя бы одно резюме."; globalError.hidden = false; return; }

  evaluateButton.disabled = true;
  const evaluated = [];
  for (let index = 0; index < resumeFiles.length; index += 1) {
    const file = resumeFiles[index];
    statusElement.textContent = `Обработка ${index + 1} из ${resumeFiles.length}: ${file.name}`;
    try {
      const payload = { vacancy_text: vacancy, vacancy_file: vacancy ? null : await encodeFile(vacancyFile), resume: await encodeFile(file) };
      const response = await fetch("/api", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      const body = await response.json();
      if (!response.ok || !body.ok) throw new Error(body.error || "Неизвестная ошибка API.");
      evaluated.push(body.data);
    } catch (error) {
      evaluated.push({ file_name: file.name, result: null, error: error.message || "Не удалось обработать резюме." });
    }
    resultsList.innerHTML = evaluated.map(resultHtml).join("");
    results.hidden = false;
  }
  resultsCount.textContent = `${evaluated.length} ${evaluated.length === 1 ? "результат" : "результата"}`;
  statusElement.textContent = "Готово";
  evaluateButton.disabled = false;
});

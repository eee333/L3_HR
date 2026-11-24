# AGENTS.md

## Проект

Vercel-приложение «AI-рекрутер» для оценки соответствия резюме вакансии.

Основные файлы:

- `index.html`, `styles.css`, `script.js` — статический русскоязычный интерфейс.
- `api/evaluate.py` — Vercel Python Function для обработки одного резюме.
- `evaluator.py` — извлечение текста из TXT/PDF, вызов OpenAI API, pydantic-валидация, вычисление вердикта.
- `prompts.py` — системный и пользовательский промты.
- `requirements.txt` — зависимости.
- `.github/workflows/deploy-vercel.yml` — production-деплой через GitHub Actions.
- `.env` — локальный `OPENAI_API_KEY`, не коммитить; на Vercel ключ задаётся через Environment Variables.

## Запуск

```powershell
vercel dev
```

Для публикации добавьте `OPENAI_API_KEY` в переменные окружения Vercel и выполните `vercel --prod`.

Для автоматического деплоя в GitHub должны быть настроены Secrets `VERCEL_TOKEN`, `VERCEL_ORG_ID` и `VERCEL_PROJECT_ID`.

## Проверки

Перед завершением правок запускать:

```powershell
.\.venv\Scripts\python.exe -m py_compile api/evaluate.py evaluator.py prompts.py
node --check script.js
```

Быстрая проверка зависимостей:

```powershell
.\.venv\Scripts\python.exe -c "import pdfplumber, openai, pydantic, dotenv; print('dependencies ok')"
```

## Правила реализации

- Вердикт вычисляется только в коде: `score >= PASS_THRESHOLD`.
- `PASS_THRESHOLD` хранится в `evaluator.py` и равен `75`.
- Модель не должна возвращать поле `verdict`.
- Ответ модели валидируется через pydantic.
- При невалидном JSON допускается один повторный запрос.
- Ошибка по одному резюме не должна прерывать обработку остальных.
- Поддерживаются только TXT и текстовые PDF; OCR не добавлять без отдельного требования.
- Не добавлять БД, авторизацию или сохранение истории без явного запроса.
- Не выводить дисклеймер в интерфейсе.
- API-ключ хранить только в `.env` локально или в Vercel Environment Variables; не печатать и не коммитить его.

## UI

- Интерфейс и все пользовательские сообщения держать на русском языке.
- Для каждого резюме результат выводится в отдельном раскрывающемся HTML-блоке.
- Ошибки показывать внутри блока соответствующего кандидата.
- Таблица `evidence` должна включать требование, статус, цитату и обоснование.

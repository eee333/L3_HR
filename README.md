# AI-рекрутер

Vercel-приложение для оценки одного описания вакансии и одного или нескольких резюме в TXT/PDF.

## Запуск

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Для локального API создайте `.env`:

```text
OPENAI_API_KEY=your_api_key_here
```

Запустите статический интерфейс и API через Vercel CLI:

```powershell
npm install -g vercel
vercel dev
```

Откройте адрес, который покажет Vercel CLI. Для публикации задайте секрет в Vercel:

```powershell
vercel env add OPENAI_API_KEY production
vercel --prod
```

В интерфейсе Vercel выберите репозиторий `eee333/L3_HR`, оставьте корневой каталог проекта и добавьте переменную `OPENAI_API_KEY` в разделе Environment Variables. Файл `.env` в репозиторий не добавляется.

Файл `pyproject.toml` указывает Vercel entrypoint Python Function: `api.evaluate:handler`.

## GitHub Actions

Workflow `.github/workflows/deploy-vercel.yml` автоматически выполняет production-деплой после каждого push в `main`. Его также можно запустить вручную через вкладку **Actions**.

В настройках GitHub-репозитория откройте **Settings → Secrets and variables → Actions** и добавьте Secrets:

- `VERCEL_TOKEN` — токен доступа Vercel.
- `VERCEL_ORG_ID` — идентификатор команды или аккаунта Vercel.
- `VERCEL_PROJECT_ID` — идентификатор проекта Vercel.

Значение `OPENAI_API_KEY` храните в Environment Variables проекта Vercel, а не в GitHub Actions и не в репозитории.

## Смоук-тест

1. Вставьте текст вакансии вручную или загрузите TXT/PDF с текстовым слоем.
2. Загрузите 3+ резюме в TXT/PDF.
3. Нажмите «Оценить».
4. Проверьте, что для каждого резюме появился отдельный блок с баллом, вердиктом, таблицей фактов и вопросами.
5. Загрузите скан-PDF без текстового слоя и проверьте понятную ошибку внутри блока кандидата.

# AI-рекрутер

Локальное Streamlit-приложение для оценки одного описания вакансии и одного или нескольких резюме в TXT/PDF.

## Запуск

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Заполните `.env`:

```text
OPENAI_API_KEY=your_api_key_here
```

Запустите приложение:

```powershell
.\.venv\Scripts\streamlit.exe run app.py
```

Если запускаете в среде с ограниченными правами на домашнюю папку, используйте команду из проекта:

```powershell
.\.venv\Scripts\streamlit.exe run app.py --browser.gatherUsageStats false
```

## Смоук-тест

1. Вставьте текст вакансии вручную или загрузите TXT/PDF с текстовым слоем.
2. Загрузите 3+ резюме в TXT/PDF.
3. Нажмите «Оценить».
4. Проверьте, что для каждого резюме появился отдельный блок с баллом, вердиктом, таблицей фактов и вопросами.
5. Загрузите скан-PDF без текстового слоя и проверьте понятную ошибку внутри блока кандидата.

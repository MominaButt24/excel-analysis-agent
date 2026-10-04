## Run the API

Start the application with:

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open `http://127.0.0.1:8000/docs`, upload an `.xlsx` file with `POST /upload`,
then send its `file_id` and a question to `POST /query`.

The default mode is `deterministic`. To use Deep Agents with a LangSmith
sandbox, add these values to your local `.env` file:

```dotenv
EXCEL_ANALYSIS_MODE=deep_agent
CEREBRAS_API_KEY=your-cerebras-key
LANGSMITH_API_KEY=your-langsmith-key
```

Do not commit `.env`. The Deep Agent uses the shared Cerebras model configured
by the application, uploads each workbook to a short-lived sandbox, and removes
the sandbox after the query. A live Deep Agent request requires both keys and
LangSmith sandbox access. Run `uv run pytest -q --ignore=tests/test_laya.py` to
check the local deterministic and mocked API flows without sandbox credentials.

## Run API and UI with PM2

Start both processes from the project directory:

```bash
pm2 start ecosystem.config.cjs
pm2 status
pm2 logs excel-api
pm2 logs excel-ui
```

The API is available at `http://127.0.0.1:8000`; the PM2-managed Gradio UI is at
`http://127.0.0.1:7861` (port 7860 is left available for a direct UI run). PM2
keeps separate logs for each named process. Use `pm2 restart excel-api excel-ui`
after code changes, `pm2 logs excel-api` or `pm2 logs excel-ui` to inspect logs,
and `pm2 delete excel-api excel-ui` to stop them.

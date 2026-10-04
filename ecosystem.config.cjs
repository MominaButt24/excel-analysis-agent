module.exports = {
  apps: [
    {
      name: "excel-api",
      script: "./.venv/bin/uvicorn",
      args: "app.main:app --host 0.0.0.0 --port 8000",
      cwd: __dirname,
      interpreter: "none",
      env: {
        LOG_LEVEL: "INFO",
        PYTHONUNBUFFERED: "1",
        EXCEL_ANALYSIS_MODE: "deep_agent",
      },
    },
    {
      name: "excel-ui",
      script: "./.venv/bin/python",
      args: "-m ui.gradio_app",
      cwd: __dirname,
      interpreter: "none",
      env: {
        API_URL: "http://0.0.0.0:8000",
        GRADIO_SERVER_PORT: "7861",
        GRADIO_ANALYTICS_ENABLED: "False",
        LOG_LEVEL: "INFO",
        PYTHONUNBUFFERED: "1",
      },
    },
  ],
};
import os

from dotenv import load_dotenv


load_dotenv()


def llm_config():
    return {
        "model": "gpt-oss-120b",
        "model_provider": "cerebras",
        "api_key": os.getenv("CEREBRAS_API_KEY"),
        "max_tokens": 4096,
        "timeout": 60,
        "max_retries": 2,
    }
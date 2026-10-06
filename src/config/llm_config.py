import os

from dotenv import load_dotenv


load_dotenv()


def llm_config():
    return {
        "provider": os.getenv(
            "LLM_PROVIDER",
            "groq",
        ),
        "model": os.getenv(
            "LLM_MODEL",
            "openai/gpt-oss-120b",
        ),
        "api_key": os.getenv(
            "GROQ_API_KEY"
        ),
        "base_url": os.getenv(
            "LLM_BASE_URL",
            "https://api.groq.com/openai/v1",
        ),
        "max_tokens": int(
            os.getenv(
                "LLM_MAX_TOKENS",
                "4096",
            )
        ),
        "timeout": int(
            os.getenv(
                "LLM_TIMEOUT",
                "60",
            )
        ),
        "max_retries": int(
            os.getenv(
                "LLM_MAX_RETRIES",
                "2",
            )
        ),
    }
# import os

# from dotenv import load_dotenv


# load_dotenv()


# def llm_config():
#     return {
#         "model": "gpt-oss-120b",
#         "model_provider": "cerebras",
#         "api_key": os.getenv("CEREBRAS_API_KEY"),
#         "max_tokens": 2048,
#         "timeout": 60,
#         "max_retries": 2,
#     }
# import os

# from dotenv import load_dotenv


# load_dotenv()


# def llm_config():
#     return {
#         "provider": os.getenv(
#             "LLM_PROVIDER",
#             "openai",
#         ),
#         "model": os.getenv(
#             "LLM_MODEL",
#             "qwen-3-vl-4b",
#         ),
#         "api_key": os.getenv(
#             "LLM_API_KEY"
#         ),
#         "base_url": os.getenv(
#             "LLM_BASE_URL"
#         ),
#         "max_tokens": int(
#             os.getenv(
#                 "LLM_MAX_TOKENS",
#                 "4096",
#             )
#         ),
#         "timeout": int(
#             os.getenv(
#                 "LLM_TIMEOUT",
#                 "60",
#             )
#         ),
#         "max_retries": int(
#             os.getenv(
#                 "LLM_MAX_RETRIES",
#                 "2",
#             )
#         ),
#     }
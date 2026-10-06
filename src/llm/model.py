from langchain_openai import ChatOpenAI
from langfuse.langchain import CallbackHandler

from src.config.llm_config import llm_config


_llm = None
_langfuse_handler = None


def get_langfuse_handler():
    global _langfuse_handler

    if _langfuse_handler is None:
        _langfuse_handler = CallbackHandler()

    return _langfuse_handler


def _create_model(cfg: dict):

    provider = cfg["provider"].lower()

    if provider in ("openai", "groq"):

        return ChatOpenAI(
            model=cfg["model"],
            api_key=cfg["api_key"],
            base_url=cfg["base_url"],
            max_tokens=cfg["max_tokens"],
            timeout=cfg["timeout"],
            max_retries=cfg["max_retries"],
            use_responses_api=False,
        )

    raise ValueError(
        f"Unsupported LLM provider: {provider}"
    )


def get_llm():

    global _llm

    if _llm is None:

        cfg = llm_config()

        print(
            f"[LLM] Using {cfg['provider']}: "
            f"{cfg['model']}"
        )

        _llm = _create_model(cfg)

    return _llm


def reset_llm():

    global _llm

    _llm = None


# from langchain_cerebras import ChatCerebras
# from langfuse.langchain import CallbackHandler

# from src.config.llm_config import llm_config


# _llm = None
# _langfuse_handler = None


# def get_langfuse_handler():
#     global _langfuse_handler

#     if _langfuse_handler is None:
#         _langfuse_handler = CallbackHandler()

#     return _langfuse_handler


# def _create_model(cfg: dict):
#     return ChatCerebras(
#         model=cfg["model"],
#         api_key=cfg["api_key"],
#         max_tokens=cfg["max_tokens"],
#         reasoning_effort=cfg.get("reasoning_effort", "low"),
#         timeout=cfg["timeout"],
#         max_retries=cfg["max_retries"],
#     )


# def get_llm():
#     global _llm

#     if _llm is None:
#         cfg = llm_config()

#         print(
#             f"[LLM] Using Cerebras: "
#             f"{cfg['model']}"
#         )

#         _llm = _create_model(cfg)

#     return _llm


# def reset_llm():
#     global _llm
#     _llm = None

# from langchain_openai import ChatOpenAI
# from langfuse.langchain import CallbackHandler

# from src.config.llm_config import llm_config


# _llm = None
# _langfuse_handler = None


# def get_langfuse_handler():
#     global _langfuse_handler

#     if _langfuse_handler is None:
#         _langfuse_handler = CallbackHandler()

#     return _langfuse_handler


# def _create_model(cfg: dict):

#     provider = cfg["provider"].lower()

#     if provider == "openai":

#         return ChatOpenAI(
#             model=cfg["model"],
#             api_key=cfg["api_key"],
#             base_url=cfg["base_url"],
#             max_tokens=cfg["max_tokens"],
#             timeout=cfg["timeout"],
#             max_retries=cfg["max_retries"],
#             use_responses_api=False,
#         )

#     raise ValueError(
#         f"Unsupported LLM provider: {provider}"
#     )


# def get_llm():

#     global _llm

#     if _llm is None:

#         cfg = llm_config()

#         print(
#             f"[LLM] Using {cfg['provider']}: "
#             f"{cfg['model']}"
#         )

#         _llm = _create_model(cfg)

#     return _llm


# def reset_llm():

#     global _llm

#     _llm = None
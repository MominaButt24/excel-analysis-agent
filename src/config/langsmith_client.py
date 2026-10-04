import os

from dotenv import load_dotenv
from langsmith.sandbox import SandboxClient


load_dotenv()


def create_sandbox_client() -> SandboxClient:
    api_key = os.getenv("LANGSMITH_API_KEY")
    if not api_key:
        raise RuntimeError(
            "LANGSMITH_API_KEY is required for Deep Agent sandbox mode."
        )

    return SandboxClient(api_key=api_key)
import os
import time
from urllib import response
import requests

from typing import Any, Dict
from dotenv import load_dotenv


load_dotenv(override=True)


JEV_URL = "https://ai-gateway.vercel.sh/v1/evaluate"
JEV_API_KEY = os.getenv("AI_GATEWAY_API_KEY")


def evaluate_with_jev(
    state: str,
    questions: Dict[str, Any],
) -> Dict[str, Any]:

    if not JEV_API_KEY:
        raise RuntimeError(
            "AI_GATEWAY_API_KEY is missing"
        )

    payload = {
        "model": "typesafe-ai/jev",
        "state": state,
        "questions": questions,
    }

    start = time.perf_counter()

    response = requests.post(
        JEV_URL,
        headers={
            "Authorization": f"Bearer {JEV_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=30,
    )

    latency_ms = (
        time.perf_counter() - start
    ) * 1000

    # response.raise_for_status()
    if not response.ok:
        print("STATUS:", response.status_code)
        print("RESPONSE:", response.text)

    response.raise_for_status()

    result = response.json()

    result["_lab"] = {
        "latency_ms": round(latency_ms, 2),
    }

    return result
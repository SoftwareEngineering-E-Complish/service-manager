import httpx
from app.models import LLMQuery


def fetch_json(endpoint: str, params: dict | None = None) -> dict | None:
    res = httpx.get(endpoint, params=params)

    if res.status_code != 200:
        return None

    return res.json()


def get_data_from_llm(endpoint: str, data: dict) -> tuple[int, LLMQuery | None]:
    res = httpx.post(
        endpoint,
        json=data,
    )

    llm_query = None

    if res.status_code == 200:
        llm_query = LLMQuery(**res.json())

    return res.status_code, llm_query

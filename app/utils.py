import logging
import httpx
from config import TOKEN_VERIFICATION_ENDPOINT
from fastapi import HTTPException, Request
from fastapi.responses import Response

from app.models import LLMQuery

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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


async def _reverse_proxy(call_url: str, request: Request):
    query = request.url.query.encode("utf-8")
    
    url = httpx.URL(
        path=request.url.path,
        query=query if query else None,
    )

    async with httpx.AsyncClient(base_url=f"http://{call_url}") as client:
        rp_req = client.build_request(request.method, url, headers=request.headers.raw)
        logger.info(f'Redirect URL = {rp_req}')
        rp_resp = await client.send(rp_req)

        return Response(
            rp_resp.content,
            status_code=rp_resp.status_code,
            headers=rp_resp.headers,
        )


async def _reverse_auth_proxy(call_url: str, request: Request):
    token = request.headers.get("Authorization")

    if token is None:
        raise HTTPException(
            status_code=401,
            detail="Request does not contain authorization token.",
        )

    auth_response = httpx.get(
        TOKEN_VERIFICATION_ENDPOINT, params={"accessToken": token}
    )

    if auth_response.text == "false":
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization token.",
        )

    return await _reverse_proxy(call_url, request)

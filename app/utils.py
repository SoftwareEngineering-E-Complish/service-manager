import logging

import httpx
from fastapi import HTTPException, Request
from fastapi.responses import Response

from app.config import TOKEN_VERIFICATION_ENDPOINT
from app.models import LLMQuery

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def fetch_json(endpoint: str, params: dict | None = None) -> dict | None:
    res = httpx.get(endpoint, params=params)

    if res.status_code != 200:
        return None

    return res.json()


def fetch_text(endpoint: str, params: dict | None = None) -> str | None:
    res = httpx.get(endpoint, params=params)

    if res.status_code != 200:
        return None

    return res.text


def post_data(
        endpoint: str,
        content: dict | None = None,
        params: dict | None = None,
        files: dict | None = None,
        return_json: bool = True
    ) -> dict | str | None:
    res = httpx.post(endpoint, params=params, json=content, files=files)

    logger.info(res.text)

    if res.status_code != 200:
        return None

    return res.json() if return_json else res.text

def put_data(
        endpoint: str,
        content: dict | None = None,
        params: dict | None = None,
        files: dict | None = None,
    ) -> dict | str | None:
    res = httpx.put(endpoint, params=params, json=content, files=files)

    logger.info(res.text)

    if res.status_code != 200:
        return None

    return res.text



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
        rp_req = client.build_request(
            request.method,
            url,
            headers=request.headers.raw,
            content=await request.body(),
        )
        logger.info(f"Redirect URL = {rp_req.url}")
        rp_resp = await client.send(rp_req)

        return Response(
            rp_resp.content,
            status_code=rp_resp.status_code,
            headers=rp_resp.headers,
        )


def raise_for_invalid_token(token: str | None):
    """Raise HTTPException when the token is invalid"""
    if token is None:
        raise HTTPException(
            status_code=401,
            detail="Request does not contain authorization token.",
        )

    auth_response = httpx.get(
        TOKEN_VERIFICATION_ENDPOINT, params={"accessToken": token}
    )

    if auth_response.json() is not True:
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization token.",
        )


async def _reverse_auth_proxy(call_url: str, request: Request):
    token = request.headers.get("Authorization")

    raise_for_invalid_token(token)

    return await _reverse_proxy(call_url, request)


def require_auth_token(func):
    async def wrapper(call_url: str, request: Request):
        token = request.headers.get("Authorization")

        raise_for_invalid_token(token)

        return await func(call_url, request)

    return wrapper

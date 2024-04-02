import logging
from functools import partial
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import (
    INVENTORY_SERVICE_URL,
    LLM_QUERY_ENDPOINT,
    PROPERTY_QUERY_ENDPOINT,
    QUERY_SCHEMA_ENDPOINT,
    USER_SERVICE_URL,
)
from app.models import InventoryRequest
from app.utils import _reverse_auth_proxy, _reverse_proxy, fetch_json, get_data_from_llm

LOG_CONFIG_PATH = Path(__file__).parent / "log_config.yaml"

INTERNAL_SERVER_ERROR = 500

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

app = FastAPI()


origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inventory service
app.add_route(
    "/properties",
    partial(_reverse_proxy, INVENTORY_SERVICE_URL),
    methods=["GET", "POST"],
)
app.add_route(
    "/properties/{path:path}",
    partial(_reverse_proxy, INVENTORY_SERVICE_URL),
    methods=["GET"],
)
app.add_route(
    "/queryProperties", partial(_reverse_proxy, INVENTORY_SERVICE_URL), methods=["GET"]
)

# User service without authorization
app.add_route("/loginURL", partial(_reverse_proxy, USER_SERVICE_URL), methods=["GET"])
app.add_route("/signupURL", partial(_reverse_proxy, USER_SERVICE_URL), methods=["GET"])
app.add_route("/logoutURL", partial(_reverse_proxy, USER_SERVICE_URL), methods=["GET"])
app.add_route("/session", partial(_reverse_proxy, USER_SERVICE_URL), methods=["GET"])
app.add_route(
    "/verifyAccessToken", partial(_reverse_proxy, USER_SERVICE_URL), methods=["GET"]
)
app.add_route(
    "/refreshAccessToken", partial(_reverse_proxy, USER_SERVICE_URL), methods=["GET"]
)

# User service with authorization
app.add_route(
    "/userId", partial(_reverse_auth_proxy, USER_SERVICE_URL), methods=["GET"]
)
app.add_route("/user", partial(_reverse_auth_proxy, USER_SERVICE_URL), methods=["GET"])
app.add_route(
    "/updateUser", partial(_reverse_auth_proxy, USER_SERVICE_URL), methods=["POST"]
)
app.add_route(
    "/deleteUser", partial(_reverse_auth_proxy, USER_SERVICE_URL), methods=["GET"]
)
app.add_route(
    "/changePassword", partial(_reverse_auth_proxy, USER_SERVICE_URL), methods=["POST"]
)


@app.get("/initial_query")
async def list_properties(user_query: str):
    logger.info(f"Received user query = {user_query}")

    query_schema = fetch_json(QUERY_SCHEMA_ENDPOINT)

    if query_schema is None:
        raise HTTPException(
            status_code=INTERNAL_SERVER_ERROR,
            detail="Something went wrong with the inventory service. Initial request failed.",
        )

    data = InventoryRequest(
        query=user_query, api_documentation=query_schema
    ).model_dump()

    logger.info(f"Fetched query schema from inventory = {data}")

    res_status_code, llm_query = get_data_from_llm(LLM_QUERY_ENDPOINT, data)

    if res_status_code != 200 or llm_query is None:
        raise HTTPException(
            status_code=res_status_code,
            detail="Something went wrong with the LLM service.",
        )

    inventory_res = fetch_json(
        PROPERTY_QUERY_ENDPOINT, params=llm_query.get_parsed_params()
    )

    if inventory_res is None:
        raise HTTPException(
            status_code=INTERNAL_SERVER_ERROR,
            detail="Something went wrong with the inventory service. Querying properties failed.",
        )

    logger.info(f"Fetched data from inventory = {inventory_res}")

    return inventory_res


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_config=str(LOG_CONFIG_PATH),
    )

import logging

from config import (
    LLM_QUERY_ENDPOINT_TEMPLATE,
    PROPERTY_QUERY_ENDPOINT_TEMPLATE,
    QUERY_SCHEMA_ENDPOINT_TEMPLATE,
)
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import InventoryRequest
from utils import fetch_json, get_data_from_llm

# CONSTANTS
QUERY_SCHEMA_ENDPOINT = QUERY_SCHEMA_ENDPOINT_TEMPLATE.format(
    "http://inventory-service"
)
LLM_QUERY_ENDPOINT = LLM_QUERY_ENDPOINT_TEMPLATE.format("http://llm-service:8888")
PROPERTY_QUERY_ENDPOINT = PROPERTY_QUERY_ENDPOINT_TEMPLATE.format(
    "http://inventory-service"
)
INTERNAL_SERVER_ERROR = 500

app = FastAPI()

logger = logging.getLogger(__file__)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/properties/")
async def list_properties(user_query: str):
    logging.info(f"Received user query = {user_query}")

    query_schema = fetch_json(QUERY_SCHEMA_ENDPOINT)

    if query_schema is None:
        raise HTTPException(
            status_code=INTERNAL_SERVER_ERROR,
            detail="Something went wrong with the inventory service. Initial request failed.",
        )

    data = InventoryRequest(
        query=user_query, api_documentation=query_schema
    ).model_dump()

    logging.info(f"Fetched query schema from inventory = {data}")

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

    logging.info(f"Fetched data from inventory = {inventory_res}")

    return inventory_res

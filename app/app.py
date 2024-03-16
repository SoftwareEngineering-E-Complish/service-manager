import httpx
import json

from models import InventoryRequest
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = ['*']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

INVENTORY_BASE_URL = "http://inventory-service"
LLM_BASE_URL = "http://llm-service:8888"
QUERY_SCHEMA_ENDPOINT = f"{INVENTORY_BASE_URL}/schema/propertyQuery"
PROPERTY_QUERY_ENDPOINT = f"{INVENTORY_BASE_URL}/queryProperties"
LLM_QUERY_ENDPOINT = f"{LLM_BASE_URL}/generates/query"


@app.get("/properties/")
async def list_properties(user_query: str):
    res = httpx.get(QUERY_SCHEMA_ENDPOINT)

    if res.status_code != 200:
        raise HTTPException(
            status_code=res.status_code,
            detail="Something went wrong with the inventory service. Initial request failed.",
        )

    query_schema = res.json()

    data = InventoryRequest(query=user_query, api_documentation=query_schema).model_dump()
    print(data)

    res = httpx.post(
        LLM_QUERY_ENDPOINT,
        json=data,
    )


    if res.status_code != 200:
        raise HTTPException(
            status_code=res.status_code,
            detail='Something went wrong with the LLM service.'
        )
    
    query_params = res.json().get('content')
    # Only use params which are not None
    parsed_query_params = {k: v for k, v in json.loads(query_params).items() if v is not None}
    
    res = httpx.get(PROPERTY_QUERY_ENDPOINT, params=parsed_query_params)

    if res.status_code != 200:
        raise HTTPException(
            status_code=res.status_code,
            detail='Something went wrong with the inventory service. Querying properties failed.'
        )
    
    return res.json()

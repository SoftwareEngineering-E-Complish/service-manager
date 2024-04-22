import os
import json
import logging
from functools import partial
from pathlib import Path

import uvicorn
from app.config import (IMAGE_SERVICE_URL, INVENTORY_SERVICE_URL,
                        LLM_QUERY_ENDPOINT, PROPERTIES_BY_USER_ENDPOINT,
                        PROPERTY_QUERY_ENDPOINT, QUERY_SCHEMA_ENDPOINT,
                        UPLOAD_IMAGE_ENDPOINT, USER_ID_ENDPOINT,
                        USER_SERVICE_URL, GEOLOCATION_API_URL)
from app.models import InventoryRequest
from app.utils import (_reverse_auth_proxy, _reverse_proxy, fetch_json,
                       fetch_text, get_data_from_llm, post_data,
                       raise_for_invalid_token)
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.datastructures import UploadFile

LOG_CONFIG_PATH = Path(__file__).parent / "log_config.yaml"

INTERNAL_SERVER_ERROR = 500

GEOLOCATION_API_KEY = os.environ['GEOLOCATION_API_ACCESS_KEY']

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

app = FastAPI(debug=True)


origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Inventory service without authorization
app.add_route(
    "/properties",
    partial(_reverse_proxy, INVENTORY_SERVICE_URL),
    methods=["GET"],
)
app.add_route(
    "/properties/{path:path}",
    partial(_reverse_proxy, INVENTORY_SERVICE_URL),
    methods=["GET"],
)
app.add_route(
    "/queryProperties", partial(_reverse_proxy, INVENTORY_SERVICE_URL), methods=["GET"]
)
app.add_route(
    "/declareInterest", partial(_reverse_proxy, INVENTORY_SERVICE_URL), methods=["POST", "DELETE"]
)
app.add_route(
    "/fetchInterestsByUser", partial(_reverse_proxy, INVENTORY_SERVICE_URL), methods=["GET"]
)
app.add_route(
    "/fetchInterestsByProperty", partial(_reverse_proxy, INVENTORY_SERVICE_URL), methods=["GET"]
)
# Inventory service with authorization
app.add_route(
    "/properties",
    partial(_reverse_auth_proxy, INVENTORY_SERVICE_URL),
    methods=["POST"],
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
app.add_route("/userId", partial(_reverse_auth_proxy, USER_SERVICE_URL), methods=["GET"])
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

# Image service without authorization
app.add_route(
    "/getPrimaryImageUrl", partial(_reverse_proxy, IMAGE_SERVICE_URL), methods=["GET"]
)
app.add_route(
    "/getImageUrls", partial(_reverse_proxy, IMAGE_SERVICE_URL), methods=["GET"]
)
# Image service with authorization
app.add_route(
    "/upload", partial(_reverse_auth_proxy, IMAGE_SERVICE_URL), methods=["POST"]
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

    # Add filters to the response
    inventory_res['filters'] = llm_query.get_parsed_params()

    return inventory_res


@app.get("/fetchPropertiesByUser")
def get_user_properties(request: Request):
    auth_token = request.headers.get("Authorization")

    raise_for_invalid_token(auth_token)

    user_id = fetch_text(USER_ID_ENDPOINT, dict(accessToken=auth_token))

    if user_id is None:
        raise HTTPException(
            status_code=404,
            detail="Couldn't fetch userId.",
        )

    user_properties = fetch_json(PROPERTIES_BY_USER_ENDPOINT, dict(userId=user_id))

    if user_properties is None:
        raise HTTPException(
            status_code=INTERNAL_SERVER_ERROR,
            detail="Something went wrong with the inventory service. Fetching user properties failed.",
        )

    logger.info(f"Fetched data from inventory = {user_properties}")

    return user_properties


@app.post("/createProperty")
async def post_create_property(request: Request):
    auth_token = request.headers.get("Authorization")

    raise_for_invalid_token(auth_token)

    user_id = fetch_text(USER_ID_ENDPOINT, dict(accessToken=auth_token))

    if user_id is None:
        raise HTTPException(
            status_code=404,
            detail="Couldn't fetch userId.",
        )

    form = await request.form()

    inventory_data = json.loads(str(form["content"]))
    inventory_data["owner"] = user_id
    del inventory_data["images"]

    images = form.getlist("images")

    geolocation_query = f"{inventory_data['address']} {inventory_data['location']}"

    geolocation_res = fetch_json(GEOLOCATION_API_URL, params=dict(key=GEOLOCATION_API_KEY, q=geolocation_query, format="json"))

    if geolocation_res is None:
        raise HTTPException(
            status_code=404,
            detail="Couldn't fetch coordinates of a location.",
        )
    
    coords = geolocation_res[0]
    
    inventory_data["longitude"] = float(coords["lon"])
    inventory_data["latitude"] = float(coords["lat"])

    inv_resp = post_data(f"http://{INVENTORY_SERVICE_URL}/properties/", inventory_data)

    logger.info(inv_resp)

    if inv_resp is None:
        raise HTTPException(
            status_code=INTERNAL_SERVER_ERROR,
            detail="Error when creating new property.",
        )

    assert isinstance(inv_resp, dict), f'Actual type = {type(inv_resp)}'

    for id_, img in enumerate(images):
        assert isinstance(img, UploadFile)
        res = post_data(
            UPLOAD_IMAGE_ENDPOINT,
            params=dict(propertyId=inv_resp["propertyId"], primary=id_ == 0),
            files={"file": img.file},
            return_json=False,
        )

        if res is None:
            raise HTTPException(
                status_code=INTERNAL_SERVER_ERROR,
                detail=f"Error when uploading image for a property with id = {inv_resp["propertyId"]}.",
            )

    return inv_resp

# https://us1.locationiq.com/v1/search?key=Your_API_Access_Token&q=221b%2C%20Baker%20St%2C%20London%20&format=json&    

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_config=str(LOG_CONFIG_PATH),
    )

from pydantic import BaseModel

class InventoryRequest(BaseModel):
    query: str
    api_documentation: dict

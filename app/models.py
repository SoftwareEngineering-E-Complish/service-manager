import json
from pydantic import BaseModel


class InventoryRequest(BaseModel):
    query: str
    api_documentation: dict


class LLMQuery(BaseModel):
    content: str

    def get_parsed_params(self) -> dict:
        if self.content == '':
            return {}
        
        return {k: v for k, v in json.loads(self.content).items() if v is not None}

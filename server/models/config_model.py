from pydantic import BaseModel

class LLMConfig(BaseModel):
    model: str
    base_url: str
    api_key: str
    max_tokens: int
    temperature: float

class ConfigUpdate(BaseModel):
    llm: LLMConfig 
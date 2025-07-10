from pydantic import BaseModel, Field, ConfigDict

from datetime import datetime

class BookSchema(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    author: str = Field(min_length=1, max_length=30)
    year: int = Field(ge=500, le=datetime.now().year)

    model_config = ConfigDict(extra='forbid')

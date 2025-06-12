from pydantic import BaseModel
from typing import List


class ArticleBase(BaseModel):
    username: str
    password: str
    first_name: str
    last_name: str

    class Config:
        orm_mode = True
        from_attributes = True

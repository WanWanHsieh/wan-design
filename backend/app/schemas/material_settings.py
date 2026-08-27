from typing import Literal

from pydantic import BaseModel


class MaterialSettingsUpdate(BaseModel):
    default_code_order: Literal["asc", "desc"]


class MaterialSettingsOut(BaseModel):
    default_code_order: str

    class Config:
        from_attributes = True

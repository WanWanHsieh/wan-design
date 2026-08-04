from pydantic import BaseModel


class BulkImportRowError(BaseModel):
    row: int
    message: str


class BulkImportResult(BaseModel):
    created: int
    errors: list[BulkImportRowError]

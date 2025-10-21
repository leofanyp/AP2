from typing import Any

from pydantic import BaseModel, Field


class C7Response(BaseModel):
    """Represents Checkout API response."""

    api: str = Field(
        ...,
        description=("The Checkout API endpoint."),
    )
    response: Any = Field(
        ...,
        description=("The response in JSON object"),
    )

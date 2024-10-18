from pydantic import BaseModel, Field
from typing import Annotated


class ConversionRequest(BaseModel):
    # these will come in as query parameters
    from_currency: Annotated[
        str, Field(..., min_length=3, max_length=3, examples=["USD"])
    ]
    to_currency: Annotated[
        str, Field(..., min_length=3, max_length=3, examples=["EUR"])
    ]
    amount: Annotated[float, Field(..., gt=0, examples=[100.00])]


class ConversionResponse(BaseModel):
    amount: float
    from_currency: str
    to_currency: str
    converted_amount: float

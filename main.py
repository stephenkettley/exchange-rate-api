from fastapi import FastAPI, HTTPException
from api_functions import fetch_currency_symbols, fetch_exchange_rates
from models import ConversionRequest, ConversionResponse

app = FastAPI()


@app.get("/")
async def root():
    return {"data": "welcome to the exchange rate api"}


@app.get("/currency-symbols/")
async def currency_symbols():
    currency_symbols = fetch_currency_symbols()
    return {"currency_symbols": currency_symbols}


@app.get("/exchange-rates/{base_currency}")
async def exchange_rates(base_currency: str):
    exchange_rates = fetch_exchange_rates(base_currency)
    return {"exchange_rates": exchange_rates}


@app.get(
    "/convert-currency/",
    response_model=ConversionResponse,
    status_code=200,
)
async def convert_currency(from_currency: str, to_currency: str, amount: float):
    try:
        rates = fetch_exchange_rates(from_currency.upper())
        if to_currency.upper() not in rates:
            raise HTTPException(status_code=404, detail="Currency not found")

        converted_amount = amount * rates[to_currency.upper()]

        return {
            "amount": amount,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "converted_amount": converted_amount,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

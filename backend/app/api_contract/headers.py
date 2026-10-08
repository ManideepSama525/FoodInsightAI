from fastapi import Request, Response

API_VERSION_HEADER = "X-FoodInsight-API-Version"
DEPRECATION_HEADER = "X-FoodInsight-Deprecation"

async def add_contract_headers(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers[API_VERSION_HEADER] = "v1"
    return response

from fastapi import FastAPI, Request
from starlette.responses import JSONResponse
from online_cinema.routes.cart import router as cart_router

from online_cinema.routes import movie_router, accounts_router, profiles_router

app = FastAPI()

@app.middleware("http")
async def docs_access_control(request: Request, call_next):
    protected_paths = ["/docs", "/redoc", "/openapi.json"]
    if request.url.path in protected_paths:
        token = request.headers.get("Authorization")
        if token != "Bearer secret-token":
            return JSONResponse(
                status_code=403,
                content={"detail": "Access to API docs is restricted"}
            )

    response = await call_next(request)
    return response


app.include_router(accounts_router, prefix="/accounts", tags=["accounts"])
app.include_router(profiles_router, prefix="/profiles", tags=["profiles"])
app.include_router(movie_router, prefix="/theater", tags=["theater"])
app.include_router(cart_router, prefix="/theater", tags=["cart"])

from fastapi import FastAPI
from online_cinema.routes import (
    movie_router,
    accounts_router,
    profiles_router
)

app = FastAPI()

app.include_router(accounts_router, prefix="/accounts", tags=["accounts"])
app.include_router(profiles_router, prefix="/profiles", tags=["profiles"])
app.include_router(movie_router, prefix="/theater", tags=["theater"])

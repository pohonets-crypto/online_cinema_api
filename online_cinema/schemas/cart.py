from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class CartItemMovieSchema(BaseModel):
    id: int
    name: str
    year: int
    price: Decimal
    genres: list[str] = []

    model_config = {"from_attributes": True}

    @classmethod
    def model_validate(cls, obj, *args, **kwargs):
        data = {
            "id": obj.id,
            "name": obj.name,
            "year": obj.year,
            "price": obj.price,
            "genres": [g.name for g in obj.genres] if obj.genres else [],
        }
        return cls(**data)


class CartItemSchema(BaseModel):
    id: int
    movie_id: int
    added_at: datetime
    movie: CartItemMovieSchema

    model_config = {"from_attributes": True}


class CartSchema(BaseModel):
    id: int
    user_id: int
    items: list[CartItemSchema] = []

    model_config = {"from_attributes": True}


class CartAddItemSchema(BaseModel):
    movie_id: int


class CartTotalSchema(BaseModel):
    total: Decimal
    items_count: int

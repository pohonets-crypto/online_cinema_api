import decimal
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, field_validator


class StarsSchema(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}


class GenreSchema(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True,
    }


class DirectorSchema(BaseModel):
    id: int
    name: str
    model_config = {
        "from_attributes": True,
    }


class CertificationSchema(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}


class MovieBaseSchema(BaseModel):
    name: str = Field(..., max_length=255)
    year: int = Field(...)
    time: int = Field(...)
    imdb: float = Field(...)
    votes: int = Field(...)
    meta_score: Optional[float] = None
    gross: Optional[float] = None
    description: str = Field(...)
    price: decimal.Decimal = Field(...)
    certification_id: int = Field(...)

    model_config = {
        "from_attributes": True
    }

    @field_validator("year")
    @classmethod
    def validate_year(cls, value: int):
        current_year = datetime.now().year
        if value > current_year + 1:
            raise ValueError(f"The year cannot be greater than {current_year + 1}.")
        return value


class MovieDetailSchema(MovieBaseSchema):
    id: int
    genres: List[GenreSchema]
    directors: List[DirectorSchema]
    stars: List[StarsSchema]
    certification: CertificationSchema

    model_config = {
        "from_attributes": True,
    }


class MovieListItemSchema(BaseModel):
    name: str
    year: int
    time: int
    imdb: float
    votes: int
    meta_score: Optional[float] = None
    gross: Optional[float] = None
    description: str
    price: decimal.Decimal
    certification_id: int

    model_config = {
        "from_attributes": True,
    }


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int

    model_config = {
        "from_attributes": True,
    }


class MovieCreateSchema(BaseModel):
    name: str = Field(..., max_length=255)
    year: int = Field(...)
    time: int = Field(...)
    imdb: float = Field(...)
    votes: int = Field(...)
    meta_score: float = Field(...)
    gross: float = Field(...)
    description: str = Field(...)
    price: decimal.Decimal = Field(...)
    genres_ids: List[int]
    directors_ids: List[int]
    stars_ids: List[int]
    certification_id: int

    model_config = {
        "from_attributes": True,
    }


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = None
    year: Optional[int] = None
    time: Optional[int] = None
    imdb: Optional[float] = None
    votes: Optional[int] = None
    meta_score: Optional[float] = None
    gross: Optional[float] = None
    description: Optional[str] = None
    price: Optional[decimal.Decimal] = None
    certification_id: Optional[int] = None

    model_config = {
        "from_attributes": True,
    }

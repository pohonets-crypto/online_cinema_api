import os

os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_DB_PORT", "5432")
os.environ.setdefault("POSTGRES_DB", "test_db")
os.environ.setdefault("POSTGRES_USER", "test_user")
os.environ.setdefault("POSTGRES_PASSWORD", "test_password")
os.environ.setdefault("secret_key_access", "test_access_secret")
os.environ.setdefault("secret_key_refresh", "test_refresh_secret")

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from online_cinema.database.models.base import Base
from online_cinema.database.models import accounts, movies, cart  # noqa
from online_cinema.database.engine import get_db
from online_cinema.main import app
from online_cinema.config.settings import TestingSettings
from online_cinema.security.token_manager import JWTAuthManager

# File-based DB so all connections share the same data
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_cinema.db"

settings = TestingSettings()
jwt_manager = JWTAuthManager(
    secret_key_access=settings.SECRET_KEY_ACCESS,
    secret_key_refresh=settings.SECRET_KEY_REFRESH,
    algorithm=settings.JWT_SIGNING_ALGORITHM,
)


@pytest_asyncio.fixture(scope="function")
async def db_session():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    session = async_session()

    try:
        yield session
    finally:
        await session.close()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()
        if os.path.exists("./test_cinema.db"):
            os.remove("./test_cinema.db")


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def active_user(db_session):
    from online_cinema.database.models.accounts import UserModel, UserGroupModel, UserGroupEnum
    from sqlalchemy import select

    stmt = select(UserGroupModel).where(UserGroupModel.name == UserGroupEnum.USER)
    result = await db_session.execute(stmt)
    group = result.scalars().first()
    if not group:
        group = UserGroupModel(name=UserGroupEnum.USER)
        db_session.add(group)
        await db_session.flush()

    user = UserModel.create(email="active@example.com", raw_password="Test1234!", group_id=group.id)
    user.is_active = True
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def moderator_user(db_session):
    from online_cinema.database.models.accounts import UserModel, UserGroupModel, UserGroupEnum
    from sqlalchemy import select

    stmt = select(UserGroupModel).where(UserGroupModel.name == UserGroupEnum.MODERATOR)
    result = await db_session.execute(stmt)
    group = result.scalars().first()
    if not group:
        group = UserGroupModel(name=UserGroupEnum.MODERATOR)
        db_session.add(group)
        await db_session.flush()

    user = UserModel.create(email="moderator@example.com", raw_password="Test1234!", group_id=group.id)
    user.is_active = True
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def user_token(active_user):
    return jwt_manager.create_access_token({"user_id": active_user.id})


@pytest_asyncio.fixture
async def moderator_token(moderator_user):
    return jwt_manager.create_access_token({"user_id": moderator_user.id})


@pytest_asyncio.fixture
async def sample_movie(db_session):
    from online_cinema.database.models.movies import MovieModel, CertificationModel, GenreModel
    from sqlalchemy import select

    stmt = select(CertificationModel).where(CertificationModel.name == "PG")
    result = await db_session.execute(stmt)
    cert = result.scalars().first()
    if not cert:
        cert = CertificationModel(name="PG")
        db_session.add(cert)
        await db_session.flush()

    stmt = select(GenreModel).where(GenreModel.name == "Action")
    result = await db_session.execute(stmt)
    genre = result.scalars().first()
    if not genre:
        genre = GenreModel(name="Action")
        db_session.add(genre)
        await db_session.flush()

    movie = MovieModel(
        name="Test Movie",
        year=2022,
        time=120,
        imdb=7.5,
        votes=1000,
        description="A test movie",
        price=9.99,
        certifications_id=cert.id,
        genres=[genre],
    )
    db_session.add(movie)
    await db_session.commit()
    await db_session.refresh(movie)
    return movie
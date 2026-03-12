import pytest
from sqlalchemy import select
from online_cinema.database.models.accounts import ActivationTokenModel, UserModel


@pytest.mark.asyncio
class TestRegisterUser:
    async def test_register_success(self, client):
        response = await client.post("/accounts/register/", json={
            "email": "newuser@example.com",
            "password": "Test1234!",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert "id" in data

    async def test_register_duplicate_email(self, client):
        payload = {"email": "dup@example.com", "password": "Test1234!"}
        await client.post("/accounts/register/", json=payload)
        response = await client.post("/accounts/register/", json=payload)
        assert response.status_code == 409

    async def test_register_weak_password(self, client):
        response = await client.post("/accounts/register/", json={
            "email": "weak@example.com",
            "password": "123",
        })
        assert response.status_code == 422

    async def test_register_invalid_email(self, client):
        response = await client.post("/accounts/register/", json={
            "email": "not-an-email",
            "password": "Test1234!",
        })
        assert response.status_code == 422


@pytest.mark.asyncio
class TestActivateAccount:
    async def test_activate_success(self, client, db_session):
        await client.post("/accounts/register/", json={
            "email": "activate@example.com",
            "password": "Test1234!",
        })
        stmt = select(ActivationTokenModel).join(UserModel).where(
            UserModel.email == "activate@example.com"
        )
        result = await db_session.execute(stmt)
        token_record = result.scalars().first()

        response = await client.post("/accounts/activate/", json={
            "email": "activate@example.com",
            "token": token_record.token,
        })
        assert response.status_code == 200
        assert "activated" in response.json()["message"].lower()

    async def test_activate_invalid_token(self, client):
        await client.post("/accounts/register/", json={
            "email": "badtoken@example.com",
            "password": "Test1234!",
        })
        response = await client.post("/accounts/activate/", json={
            "email": "badtoken@example.com",
            "token": "wrong_token",
        })
        assert response.status_code == 400

    async def test_activate_already_active(self, client, db_session):
        await client.post("/accounts/register/", json={
            "email": "alreadyactive@example.com",
            "password": "Test1234!",
        })
        stmt = select(ActivationTokenModel).join(UserModel).where(
            UserModel.email == "alreadyactive@example.com"
        )
        result = await db_session.execute(stmt)
        token_record = result.scalars().first()

        await client.post("/accounts/activate/", json={
            "email": "alreadyactive@example.com",
            "token": token_record.token,
        })
        # Activate again
        response = await client.post("/accounts/activate/", json={
            "email": "alreadyactive@example.com",
            "token": token_record.token,
        })
        assert response.status_code == 400


@pytest.mark.asyncio
class TestLogin:
    async def test_login_success(self, client, active_user):
        response = await client.post("/accounts/login/", json={
            "email": "active@example.com",
            "password": "Test1234!",
        })
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_login_wrong_password(self, client, active_user):
        response = await client.post("/accounts/login/", json={
            "email": "active@example.com",
            "password": "WrongPass1!",
        })
        assert response.status_code == 401

    async def test_login_inactive_user(self, client, db_session):
        from online_cinema.database.models.accounts import UserGroupModel, UserGroupEnum
        stmt = select(UserGroupModel).where(UserGroupModel.name == UserGroupEnum.USER)
        result = await db_session.execute(stmt)
        group = result.scalars().first()
        if not group:
            group = UserGroupModel(name=UserGroupEnum.USER)
            db_session.add(group)
            await db_session.flush()

        user = UserModel.create(
            email="inactive@example.com",
            raw_password="Test1234!",
            group_id=group.id
        )
        db_session.add(user)
        await db_session.commit()

        response = await client.post("/accounts/login/", json={
            "email": "inactive@example.com",
            "password": "Test1234!",
        })
        assert response.status_code == 403

    async def test_login_nonexistent_user(self, client):
        response = await client.post("/accounts/login/", json={
            "email": "ghost@example.com",
            "password": "Test1234!",
        })
        assert response.status_code == 401


@pytest.mark.asyncio
class TestRefreshToken:
    async def test_refresh_success(self, client, active_user):
        login = await client.post("/accounts/login/", json={
            "email": "active@example.com",
            "password": "Test1234!",
        })
        refresh_token = login.json()["refresh_token"]

        response = await client.post("/accounts/refresh/", json={
            "refresh_token": refresh_token,
        })
        assert response.status_code == 200
        assert "access_token" in response.json()

    async def test_refresh_invalid_token(self, client):
        response = await client.post("/accounts/refresh/", json={
            "refresh_token": "invalid.token.value",
        })
        assert response.status_code == 400


@pytest.mark.asyncio
class TestGetMovies:
    async def test_get_movies_empty(self, client):
        response = await client.get("/theater/movies/")
        assert response.status_code == 404

    async def test_get_movies_with_data(self, client, sample_movie):
        response = await client.get("/theater/movies/")
        assert response.status_code == 200
        data = response.json()
        assert data["total_items"] >= 1
        assert len(data["movies"]) >= 1

    async def test_pagination(self, client, sample_movie):
        response = await client.get("/theater/movies/?page=1&per_page=1")
        assert response.status_code == 200
        assert len(response.json()["movies"]) == 1

    async def test_invalid_page(self, client):
        response = await client.get("/theater/movies/?page=0")
        assert response.status_code == 422


@pytest.mark.asyncio
class TestGetMovieById:
    async def test_get_existing_movie(self, client, sample_movie):
        response = await client.get(f"/theater/movies/{sample_movie.id}/")
        assert response.status_code == 200
        assert response.json()["name"] == sample_movie.name

    async def test_get_nonexistent_movie(self, client):
        response = await client.get("/theater/movies/99999/")
        assert response.status_code == 404



@pytest.mark.asyncio
class TestGetCart:

    async def test_get_cart_unauthorized(self, client):
        response = await client.get("/theater/cart/")
        assert response.status_code == 401


@pytest.mark.asyncio
class TestAddToCart:

    async def test_add_to_cart_unauthorized(self, client, sample_movie):
        response = await client.post("/theater/cart/items/", json={"movie_id": sample_movie.id})
        assert response.status_code == 401

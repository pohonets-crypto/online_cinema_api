from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from online_cinema.database.engine import get_db
from online_cinema.database.models.accounts import UserModel, UserGroupEnum
from online_cinema.database.models.cart import CartModel, CartItemModel
from online_cinema.database.models.movies import MovieModel, MoviePurchaseModel
from online_cinema.routes.accounts import get_current_user
from online_cinema.schemas.cart import CartSchema, CartAddItemSchema

router = APIRouter()


async def get_or_create_cart(user: UserModel, db: AsyncSession) -> CartModel:
    stmt = (
        select(CartModel)
        .options(selectinload(CartModel.items).
                 selectinload(CartItemModel.movie))
        .where(CartModel.user_id == user.id)
    )
    result = await db.execute(stmt)
    cart = result.scalars().first()

    if not cart:
        cart = CartModel(user_id=user.id)
        db.add(cart)
        await db.commit()
        await db.refresh(cart)
        result = await db.execute(
            select(CartModel)
            .options(selectinload(CartModel.items).
                     selectinload(CartItemModel.movie))
            .where(CartModel.id == cart.id)
        )
        cart = result.scalars().first()

    return cart


@router.get(
    "/cart/",
    response_model=CartSchema,
    summary="Get current user's cart",
    description="Returns the cart with all items for the authenticated user.",
    status_code=status.HTTP_200_OK,
)
async def get_cart(
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CartSchema:
    cart = await get_or_create_cart(current_user, db)
    return CartSchema.model_validate(cart)


@router.post(
    "/cart/items/",
    response_model=CartSchema,
    summary="Add movie to cart",
    description="Adds a movie to the cart. "
                "Cannot add already purchased or duplicate movies.",
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Movie already in cart or already purchased."},
        404: {"description": "Movie not found."},
    },
)
async def add_to_cart(
    data: CartAddItemSchema,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CartSchema:
    movie = await db.get(MovieModel, data.movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found.")

    purchased = await db.scalar(
        select(MoviePurchaseModel).where(
            MoviePurchaseModel.user_id == current_user.id,
            MoviePurchaseModel.movie_id == data.movie_id,
        )
    )
    if purchased:
        raise HTTPException(
            status_code=400,
            detail="You have already purchased this movie. "
                   "Repeat purchases are not allowed.",
        )

    cart = await get_or_create_cart(current_user, db)

    already_in_cart = any(item.movie_id == data.movie_id
                          for item in cart.items)
    if already_in_cart:
        raise HTTPException(status_code=400,
                            detail="Movie is already in the cart.")

    cart_item = CartItemModel(cart_id=cart.id, movie_id=data.movie_id)
    db.add(cart_item)
    await db.commit()

    return await get_cart(current_user, db)


@router.delete(
    "/cart/items/{movie_id}/",
    response_model=CartSchema,
    summary="Remove movie from cart",
    description="Removes a specific movie from the cart.",
    status_code=status.HTTP_200_OK,
    responses={
        404: {"description": "Movie not found in cart."},
    },
)
async def remove_from_cart(
    movie_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CartSchema:
    cart = await get_or_create_cart(current_user, db)

    item = next((i for i in cart.items if i.movie_id == movie_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Movie not found in cart.")

    await db.delete(item)
    await db.commit()

    return await get_cart(current_user, db)


@router.delete(
    "/cart/",
    summary="Clear the cart",
    description="Removes all items from the cart.",
    status_code=status.HTTP_200_OK,
)
async def clear_cart(
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cart = await get_or_create_cart(current_user, db)

    for item in cart.items:
        await db.delete(item)

    await db.commit()
    return {"detail": "Cart cleared successfully."}


@router.post(
    "/cart/checkout/",
    summary="Checkout — pay for all items in cart",
    description=(
        "Purchases all movies in the cart. "
        "Skips already purchased movies and notifies the user. "
        "Clears the cart after successful payment."
    ),
    status_code=status.HTTP_200_OK,
)
async def checkout(
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cart = await get_or_create_cart(current_user, db)

    if not cart.items:
        raise HTTPException(status_code=400, detail="Cart is empty.")

    purchased = []
    skipped = []

    for item in cart.items:
        already_purchased = await db.scalar(
            select(MoviePurchaseModel).where(
                MoviePurchaseModel.user_id == current_user.id,
                MoviePurchaseModel.movie_id == item.movie_id,
            )
        )
        if already_purchased:
            skipped.append(item.movie_id)
        else:
            db.add(MoviePurchaseModel(user_id=current_user.id,
                                      movie_id=item.movie_id))
            purchased.append(item.movie_id)

    # Clear the cart
    for item in cart.items:
        await db.delete(item)

    await db.commit()

    return {
        "detail": "Checkout complete.",
        "purchased_movie_ids": purchased,
        "skipped_already_purchased": skipped,
    }


@router.get(
    "/cart/moderator/{user_id}/",
    response_model=CartSchema,
    summary="[Moderator] View user's cart",
    description="Allows moderators to view the contents of any user's cart.",
    status_code=status.HTTP_200_OK,
)
async def get_user_cart_moderator(
    user_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CartSchema:
    if not current_user.has_group(
        UserGroupEnum.MODERATOR
    ) and not current_user.has_group(UserGroupEnum.ADMIN):
        raise HTTPException(status_code=403, detail="Access forbidden.")

    user = await db.get(UserModel, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    cart = await get_or_create_cart(user, db)
    return CartSchema.model_validate(cart)

from fastapi import Depends, Query, APIRouter, Body

from app.routers.dependencies import DBManager, get_db
from app.routers.dependencies import PaginationDep
from ..schemas.categories import CategoryAdd, CategoryPatch

router = APIRouter(prefix="/category", tags=["Категории"])


@router.get("")
async def get_category(
    pagination: PaginationDep, db: DBManager = Depends(get_db), search: str = None
):
    per_page = pagination.per_page or 5
    return await db.categories.get_all(
        limit=per_page, offset=per_page * (pagination.page - 1), search=search
    )


@router.get("/{category_id}")
async def get_category(category_id: int, db: DBManager = Depends(get_db)):
    return await db.categories.get_one_or_none(id=category_id)


@router.post("")
async def create_category(
    db: DBManager = Depends(get_db),
    category_data: CategoryAdd = Body(
        openapi_examples={
            "1": {
                "summary": "Первое блюдо",
                "value": {
                    "title": "Первым блюдам относятся",
                },
            },
            "2": {
                "summary": "Кондитерские изделия",
                "value": {
                    "title": "Кондитерским изделиям относятся ",
                },
            },
        }
    ),
):
    category = await db.categories.add(category_data)
    await db.commit()

    return {"status": "OK", "data": category}


@router.put("/{category_id}")
async def edit_category(
    category_id: int, category_data: CategoryAdd, db: DBManager = Depends(get_db)
):
    await db.categories.edit(category_data, id=category_id)
    await db.commit()
    return {"status": "OK"}


@router.patch(
    "/{category_id}",
    summary="Частичное обновление данных об категории",
    description="<h1>Тут мы частично обновляем данные об категории: можно отправить name, а можно title</h1>",
)
async def partially_edit_category(
    category_id: int,
    category_data: CategoryPatch,
    db: DBManager = Depends(get_db),
):
    await db.categories.edit(category_data, exclude_unset=True, id=category_id)
    await db.commit()
    return {"status": "OK"}


@router.delete("/{category_id}")
async def delete_category(category_id: int, db: DBManager = Depends(get_db)):
    await db.categories.delete(id=category_id)
    await db.commit()
    return {"status": "OK"}

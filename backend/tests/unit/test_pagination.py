from fastapi import FastAPI
from httpx import AsyncClient

from apan.core.pagination import Page, PageParams, PageParamsDep


def test_offset_and_limit() -> None:
    params = PageParams(page=3, page_size=20)

    assert (params.offset, params.limit) == (40, 20)


async def test_page_params_are_validated(app: FastAPI, client: AsyncClient) -> None:
    @app.get("/items", response_model=Page[int])
    async def items(params: PageParamsDep) -> Page[int]:
        return Page.build([1, 2], total=2, params=params)

    ok = await client.get("/items", params={"page": 2, "pageSize": 5})
    too_big = await client.get("/items", params={"pageSize": 101})

    assert ok.json() == {"items": [1, 2], "total": 2, "page": 2, "pageSize": 5}
    assert too_big.status_code == 422
    assert too_big.json()["fieldErrors"][0]["field"] == "pageSize"

from typing import Annotated

from fastapi import Depends, Query

from apan.core.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from apan.core.schemas import ApiModel


class PageParams(ApiModel):
    page: int = 1
    page_size: int = DEFAULT_PAGE_SIZE

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


class Page[T](ApiModel):
    items: list[T]
    total: int
    page: int
    page_size: int

    @classmethod
    def build(cls, items: list[T], total: int, params: PageParams) -> "Page[T]":
        return cls(items=items, total=total, page=params.page, page_size=params.page_size)


def _page_params(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
) -> PageParams:
    return PageParams(page=page, page_size=page_size)


PageParamsDep = Annotated[PageParams, Depends(_page_params)]

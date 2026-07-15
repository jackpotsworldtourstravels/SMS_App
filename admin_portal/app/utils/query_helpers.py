from flask import request
from sqlalchemy import or_
from sqlalchemy.sql import Select

from app.extensions import db


def paginate(select_stmt: Select, default_per_page: int = 25, max_per_page: int = 100):
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", default_per_page, type=int)
    per_page = max(1, min(per_page, max_per_page))
    return db.paginate(select_stmt, page=page, per_page=per_page, error_out=False)


def apply_search(select_stmt: Select, columns: list, term: str | None) -> Select:
    if not term:
        return select_stmt
    like_term = f"%{term}%"
    conditions = [col.ilike(like_term) for col in columns]
    return select_stmt.where(or_(*conditions))


def apply_sort(
    select_stmt: Select,
    sort_map: dict,
    sort_key: str | None,
    default_key: str,
    direction: str | None,
) -> Select:
    column = sort_map.get(sort_key or default_key, sort_map[default_key])
    if direction == "desc":
        return select_stmt.order_by(column.desc())
    return select_stmt.order_by(column.asc())

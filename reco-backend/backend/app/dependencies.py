from fastapi import Request
from typing import Annotated
from functools import lru_cache

async def get_db(request: Request):
    """Dependency để lấy database pool từ request state"""
    return request.state.db

async def get_es(request: Request):
    """Dependency để lấy Elasticsearch client từ request state"""
    return request.state.es



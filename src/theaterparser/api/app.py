from typing import Annotated

from fastapi import Depends, FastAPI, Response, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from theaterparser import __version__
from theaterparser.db.session import get_session

app = FastAPI(title="theaterparser", version=__version__)

Session = Annotated[AsyncSession, Depends(get_session)]


class Health(BaseModel):
    status: str
    version: str
    database: bool


@app.get("/health")
async def health(session: Session, response: Response) -> Health:
    try:
        await session.execute(text("SELECT 1"))
        database = True
    except (SQLAlchemyError, OSError):
        database = False
    if not database:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return Health(status="ok" if database else "degraded", version=__version__, database=database)

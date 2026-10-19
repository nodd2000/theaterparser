from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from theaterparser.db.models import (
    City,
    Country,
    Credit,
    CreditRole,
    Person,
    Production,
    ProductionStatus,
    Theatre,
)


async def make_theatre(session: AsyncSession) -> Theatre:
    country = Country(code="RU", name="Россия")
    city = City(country=country, name="Москва")
    theatre = Theatre(city=city, name="МХТ имени А. П. Чехова", aliases=["МХТ", "Художественный"])
    session.add(theatre)
    await session.flush()
    return theatre


async def test_production_with_credits(session: AsyncSession) -> None:
    theatre = await make_theatre(session)
    director = Person(full_name="Константин Богомолов")
    production = Production(
        theatre=theatre,
        title="Мушкетёры. Сага. Часть первая",
        premiere_date=date(2018, 5, 25),
        status=ProductionStatus.IN_REPERTOIRE,
        credits=[Credit(person=director, role=CreditRole.DIRECTOR)],
    )
    session.add(production)
    await session.flush()

    loaded = await session.scalar(select(Production).where(Production.theatre_id == theatre.id))
    assert loaded is not None
    assert loaded.status is ProductionStatus.IN_REPERTOIRE
    assert loaded.aliases == []
    assert theatre.aliases == ["МХТ", "Художественный"]


async def test_fuzzy_title_search(session: AsyncSession) -> None:
    theatre = await make_theatre(session)
    session.add_all(
        [
            Production(theatre=theatre, title="Гамлет"),
            Production(theatre=theatre, title="Вишнёвый сад"),
        ]
    )
    await session.flush()

    similarity = func.similarity(Production.title, "Гамлет. Коллаж")
    best = await session.scalar(select(Production.title).order_by(similarity.desc()).limit(1))
    assert best == "Гамлет"

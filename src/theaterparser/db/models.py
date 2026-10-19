"""Модель данных каталога и пайплайна сбора.

Сырые данные (RawPost) не изменяются: правка поста — новая версия. Всё извлечённое
(Extraction, Draft) ссылается на источник, чтобы посты можно было переобработать.
"""

from datetime import date, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy import (
    text as sql_text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from theaterparser.db.base import Base, TimestampMixin


def str_enum(enum_cls: type[StrEnum]) -> SAEnum:
    """Enum хранится как VARCHAR: новые значения добавляются без миграции БД."""
    return SAEnum(
        enum_cls,
        native_enum=False,
        length=32,
        values_callable=lambda e: [m.value for m in e],
        name=enum_cls.__name__.lower(),
    )


def aliases_column() -> Mapped[list[str]]:
    return mapped_column(ARRAY(Text), server_default=sql_text("'{}'"), default=list)


def trgm_index(name: str, column: str) -> Index:
    return Index(
        name,
        column,
        postgresql_using="gin",
        postgresql_ops={column: "gin_trgm_ops"},
    )


class TheatreKind(StrEnum):
    STATE = "state"
    MUNICIPAL = "municipal"
    PRIVATE = "private"
    INDEPENDENT = "independent"


class ProductionStatus(StrEnum):
    ANNOUNCED = "announced"
    IN_REPERTOIRE = "in_repertoire"
    ARCHIVED = "archived"


class CreditRole(StrEnum):
    DIRECTOR = "director"
    PLAYWRIGHT = "playwright"
    DRAMATURG = "dramaturg"
    SET_DESIGNER = "set_designer"
    COSTUME_DESIGNER = "costume_designer"
    LIGHTING_DESIGNER = "lighting_designer"
    VIDEO_DESIGNER = "video_designer"
    COMPOSER = "composer"
    CHOREOGRAPHER = "choreographer"
    ACTOR = "actor"
    OTHER = "other"


class SourceKind(StrEnum):
    TELEGRAM = "telegram"
    WEBSITE = "website"


class SourceCategory(StrEnum):
    THEATRE = "theatre"
    CRITIC = "critic"
    BLOGGER = "blogger"
    MEDIA = "media"
    INSTITUTION = "institution"


class CollectMethod(StrEnum):
    TG_WEB = "tg_web"
    TELETHON = "telethon"
    SITE = "site"


class ExtractionKind(StrEnum):
    CLASSIFICATION = "classification"
    ENTITIES = "entities"


class DraftKind(StrEnum):
    PRODUCTION = "production"
    REVIEW = "review"
    PHOTOS = "photos"
    UPDATE = "update"


class DraftStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MERGED = "merged"


class Country(Base):
    __tablename__ = "countries"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(2), unique=True)
    name: Mapped[str] = mapped_column(Text)

    cities: Mapped[list["City"]] = relationship(back_populates="country")


class City(Base):
    __tablename__ = "cities"
    __table_args__ = (UniqueConstraint("country_id", "name", "region"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    country_id: Mapped[int] = mapped_column(ForeignKey("countries.id"), index=True)
    name: Mapped[str] = mapped_column(Text)
    region: Mapped[str | None] = mapped_column(Text)
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)

    country: Mapped[Country] = relationship(back_populates="cities")
    theatres: Mapped[list["Theatre"]] = relationship(back_populates="city")


class Theatre(TimestampMixin, Base):
    __tablename__ = "theatres"
    __table_args__ = (trgm_index("ix_theatres_name_trgm", "name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id"), index=True)
    name: Mapped[str] = mapped_column(Text)
    short_name: Mapped[str | None] = mapped_column(Text)
    aliases: Mapped[list[str]] = aliases_column()
    kind: Mapped[TheatreKind | None] = mapped_column(str_enum(TheatreKind))
    address: Mapped[str | None] = mapped_column(Text)
    website: Mapped[str | None] = mapped_column(Text)
    repertoire_url: Mapped[str | None] = mapped_column(Text)
    wikidata_id: Mapped[str | None] = mapped_column(String(16), unique=True)
    culture_ru_id: Mapped[str | None] = mapped_column(String(32), unique=True)
    is_active: Mapped[bool] = mapped_column(server_default=sql_text("true"), default=True)

    city: Mapped[City] = relationship(back_populates="theatres")
    stages: Mapped[list["Stage"]] = relationship(back_populates="theatre")
    productions: Mapped[list["Production"]] = relationship(back_populates="theatre")


class Stage(Base):
    __tablename__ = "stages"
    __table_args__ = (UniqueConstraint("theatre_id", "name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    theatre_id: Mapped[int] = mapped_column(ForeignKey("theatres.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(Text)
    address: Mapped[str | None] = mapped_column(Text)

    theatre: Mapped[Theatre] = relationship(back_populates="stages")


class Person(TimestampMixin, Base):
    __tablename__ = "persons"
    __table_args__ = (trgm_index("ix_persons_full_name_trgm", "full_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(Text)
    aliases: Mapped[list[str]] = aliases_column()
    wikidata_id: Mapped[str | None] = mapped_column(String(16), unique=True)
    bio: Mapped[str | None] = mapped_column(Text)

    credits: Mapped[list["Credit"]] = relationship(back_populates="person")


class Production(TimestampMixin, Base):
    __tablename__ = "productions"
    __table_args__ = (trgm_index("ix_productions_title_trgm", "title"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    theatre_id: Mapped[int] = mapped_column(ForeignKey("theatres.id"), index=True)
    stage_id: Mapped[int | None] = mapped_column(ForeignKey("stages.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(Text)
    aliases: Mapped[list[str]] = aliases_column()
    source_work: Mapped[str | None] = mapped_column(Text)
    premiere_date: Mapped[date | None] = mapped_column(Date, index=True)
    status: Mapped[ProductionStatus] = mapped_column(
        str_enum(ProductionStatus), default=ProductionStatus.ANNOUNCED
    )
    age_rating: Mapped[str | None] = mapped_column(String(8))
    duration_minutes: Mapped[int | None] = mapped_column(SmallInteger)
    description: Mapped[str | None] = mapped_column(Text)

    theatre: Mapped[Theatre] = relationship(back_populates="productions")
    stage: Mapped[Stage | None] = relationship()
    credits: Mapped[list["Credit"]] = relationship(back_populates="production")
    reviews: Mapped[list["Review"]] = relationship(back_populates="production")
    photos: Mapped[list["Photo"]] = relationship(back_populates="production")


class Credit(Base):
    """Участие персоны в постановке: режиссёр, художник, актёр (с ролью-персонажем) и т.д."""

    __tablename__ = "credits"

    id: Mapped[int] = mapped_column(primary_key=True)
    production_id: Mapped[int] = mapped_column(
        ForeignKey("productions.id", ondelete="CASCADE"), index=True
    )
    person_id: Mapped[int] = mapped_column(ForeignKey("persons.id"), index=True)
    role: Mapped[CreditRole] = mapped_column(str_enum(CreditRole))
    character: Mapped[str | None] = mapped_column(Text)
    position: Mapped[int] = mapped_column(SmallInteger, server_default=sql_text("0"), default=0)

    production: Mapped[Production] = relationship(back_populates="credits")
    person: Mapped[Person] = relationship(back_populates="credits")


class Source(TimestampMixin, Base):
    """Откуда берём данные: Telegram-канал или сайт."""

    __tablename__ = "sources"
    __table_args__ = (UniqueConstraint("kind", "handle"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[SourceKind] = mapped_column(str_enum(SourceKind))
    # username канала без @ или URL сайта
    handle: Mapped[str] = mapped_column(Text)
    title: Mapped[str | None] = mapped_column(Text)
    category: Mapped[SourceCategory] = mapped_column(str_enum(SourceCategory))
    collect_method: Mapped[CollectMethod] = mapped_column(str_enum(CollectMethod))
    theatre_id: Mapped[int | None] = mapped_column(ForeignKey("theatres.id"), index=True)
    person_id: Mapped[int | None] = mapped_column(ForeignKey("persons.id"), index=True)
    weight: Mapped[float] = mapped_column(Float, server_default=sql_text("1.0"), default=1.0)
    is_active: Mapped[bool] = mapped_column(server_default=sql_text("true"), default=True)
    last_external_id: Mapped[int | None] = mapped_column(BigInteger)
    last_collected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    theatre: Mapped[Theatre | None] = relationship()
    person: Mapped[Person | None] = relationship()


class RawPost(Base):
    __tablename__ = "raw_posts"
    __table_args__ = (UniqueConstraint("source_id", "external_id", "version"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), index=True)
    external_id: Mapped[str] = mapped_column(Text)
    version: Mapped[int] = mapped_column(SmallInteger, server_default=sql_text("1"), default=1)
    url: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    edited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    text: Mapped[str | None] = mapped_column(Text)
    links: Mapped[list[Any]] = mapped_column(JSONB, server_default=sql_text("'[]'"), default=list)
    media: Mapped[list[Any]] = mapped_column(JSONB, server_default=sql_text("'[]'"), default=list)
    forwarded_from: Mapped[str | None] = mapped_column(Text)
    # Альбом из нескольких фото в Telegram — несколько сообщений с общим grouped_id
    grouped_id: Mapped[str | None] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64))
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    source: Mapped[Source] = relationship()
    extractions: Mapped[list["Extraction"]] = relationship(back_populates="raw_post")


class Extraction(Base):
    """Результат LLM: классификация поста или извлечённые сущности."""

    __tablename__ = "extractions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    raw_post_id: Mapped[int] = mapped_column(
        ForeignKey("raw_posts.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[ExtractionKind] = mapped_column(str_enum(ExtractionKind))
    model: Mapped[str] = mapped_column(Text)
    prompt_version: Mapped[str] = mapped_column(String(32))
    label: Mapped[str | None] = mapped_column(String(32))
    data: Mapped[dict[str, Any]] = mapped_column(
        JSONB, server_default=sql_text("'{}'"), default=dict
    )
    confidence: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    raw_post: Mapped[RawPost] = relationship(back_populates="extractions")


draft_posts = Table(
    "draft_posts",
    Base.metadata,
    Column("draft_id", ForeignKey("drafts.id", ondelete="CASCADE"), primary_key=True),
    Column("raw_post_id", ForeignKey("raw_posts.id", ondelete="CASCADE"), primary_key=True),
)


class Draft(TimestampMixin, Base):
    """Сформированная публикация, ожидающая решения модератора в боте."""

    __tablename__ = "drafts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    kind: Mapped[DraftKind] = mapped_column(str_enum(DraftKind))
    status: Mapped[DraftStatus] = mapped_column(
        str_enum(DraftStatus), default=DraftStatus.PENDING, index=True
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    production_id: Mapped[int | None] = mapped_column(ForeignKey("productions.id"))
    match_confidence: Mapped[float | None] = mapped_column(Float)
    bot_message_id: Mapped[int | None] = mapped_column(BigInteger)
    decided_by: Mapped[str | None] = mapped_column(Text)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    production: Mapped[Production | None] = relationship()
    raw_posts: Mapped[list[RawPost]] = relationship(secondary=draft_posts)


class Review(TimestampMixin, Base):
    __tablename__ = "reviews"
    __table_args__ = (UniqueConstraint("production_id", "url"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    production_id: Mapped[int] = mapped_column(
        ForeignKey("productions.id", ondelete="CASCADE"), index=True
    )
    author_id: Mapped[int | None] = mapped_column(ForeignKey("persons.id"), index=True)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"))
    raw_post_id: Mapped[int | None] = mapped_column(ForeignKey("raw_posts.id"))
    url: Mapped[str] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    quote: Mapped[str] = mapped_column(Text)

    production: Mapped[Production] = relationship(back_populates="reviews")
    author: Mapped[Person | None] = relationship()
    source: Mapped[Source | None] = relationship()


class Photo(Base):
    __tablename__ = "photos"

    id: Mapped[int] = mapped_column(primary_key=True)
    production_id: Mapped[int] = mapped_column(
        ForeignKey("productions.id", ondelete="CASCADE"), index=True
    )
    raw_post_id: Mapped[int | None] = mapped_column(ForeignKey("raw_posts.id"))
    storage_key: Mapped[str] = mapped_column(Text, unique=True)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    photographer: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    production: Mapped[Production] = relationship(back_populates="photos")

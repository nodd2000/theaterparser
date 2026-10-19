"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-10-19 08:58:53.464955
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Нечёткий поиск по названиям театров, спектаклей и именам персон
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.create_table(
        "countries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=2), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_countries")),
        sa.UniqueConstraint("code", name=op.f("uq_countries_code")),
    )
    op.create_table(
        "persons",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.Text(), nullable=False),
        sa.Column(
            "aliases", postgresql.ARRAY(sa.Text()), server_default=sa.text("'{}'"), nullable=False
        ),
        sa.Column("wikidata_id", sa.String(length=16), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_persons")),
        sa.UniqueConstraint("wikidata_id", name=op.f("uq_persons_wikidata_id")),
    )
    op.create_index(
        "ix_persons_full_name_trgm",
        "persons",
        ["full_name"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"full_name": "gin_trgm_ops"},
    )
    op.create_table(
        "cities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("country_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("region", sa.Text(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(
            ["country_id"], ["countries.id"], name=op.f("fk_cities_country_id_countries")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cities")),
        sa.UniqueConstraint(
            "country_id", "name", "region", name=op.f("uq_cities_country_id_name_region")
        ),
    )
    op.create_index(op.f("ix_cities_country_id"), "cities", ["country_id"], unique=False)
    op.create_table(
        "theatres",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("city_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("short_name", sa.Text(), nullable=True),
        sa.Column(
            "aliases", postgresql.ARRAY(sa.Text()), server_default=sa.text("'{}'"), nullable=False
        ),
        sa.Column(
            "kind",
            sa.Enum(
                "state",
                "municipal",
                "private",
                "independent",
                name="theatrekind",
                native_enum=False,
                length=32,
            ),
            nullable=True,
        ),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("website", sa.Text(), nullable=True),
        sa.Column("repertoire_url", sa.Text(), nullable=True),
        sa.Column("wikidata_id", sa.String(length=16), nullable=True),
        sa.Column("culture_ru_id", sa.String(length=32), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["city_id"], ["cities.id"], name=op.f("fk_theatres_city_id_cities")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_theatres")),
        sa.UniqueConstraint("culture_ru_id", name=op.f("uq_theatres_culture_ru_id")),
        sa.UniqueConstraint("wikidata_id", name=op.f("uq_theatres_wikidata_id")),
    )
    op.create_index(op.f("ix_theatres_city_id"), "theatres", ["city_id"], unique=False)
    op.create_index(
        "ix_theatres_name_trgm",
        "theatres",
        ["name"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"name": "gin_trgm_ops"},
    )
    op.create_table(
        "sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "kind",
            sa.Enum("telegram", "website", name="sourcekind", native_enum=False, length=32),
            nullable=False,
        ),
        sa.Column("handle", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column(
            "category",
            sa.Enum(
                "theatre",
                "critic",
                "blogger",
                "media",
                "institution",
                name="sourcecategory",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column(
            "collect_method",
            sa.Enum(
                "tg_web", "telethon", "site", name="collectmethod", native_enum=False, length=32
            ),
            nullable=False,
        ),
        sa.Column("theatre_id", sa.Integer(), nullable=True),
        sa.Column("person_id", sa.Integer(), nullable=True),
        sa.Column("weight", sa.Float(), server_default=sa.text("1.0"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("last_external_id", sa.BigInteger(), nullable=True),
        sa.Column("last_collected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["person_id"], ["persons.id"], name=op.f("fk_sources_person_id_persons")
        ),
        sa.ForeignKeyConstraint(
            ["theatre_id"], ["theatres.id"], name=op.f("fk_sources_theatre_id_theatres")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sources")),
        sa.UniqueConstraint("kind", "handle", name=op.f("uq_sources_kind_handle")),
    )
    op.create_index(op.f("ix_sources_person_id"), "sources", ["person_id"], unique=False)
    op.create_index(op.f("ix_sources_theatre_id"), "sources", ["theatre_id"], unique=False)
    op.create_table(
        "stages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("theatre_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["theatre_id"],
            ["theatres.id"],
            name=op.f("fk_stages_theatre_id_theatres"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_stages")),
        sa.UniqueConstraint("theatre_id", "name", name=op.f("uq_stages_theatre_id_name")),
    )
    op.create_table(
        "productions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("theatre_id", sa.Integer(), nullable=False),
        sa.Column("stage_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column(
            "aliases", postgresql.ARRAY(sa.Text()), server_default=sa.text("'{}'"), nullable=False
        ),
        sa.Column("source_work", sa.Text(), nullable=True),
        sa.Column("premiere_date", sa.Date(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "announced",
                "in_repertoire",
                "archived",
                name="productionstatus",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("age_rating", sa.String(length=8), nullable=True),
        sa.Column("duration_minutes", sa.SmallInteger(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["stage_id"],
            ["stages.id"],
            name=op.f("fk_productions_stage_id_stages"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["theatre_id"], ["theatres.id"], name=op.f("fk_productions_theatre_id_theatres")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_productions")),
    )
    op.create_index(
        op.f("ix_productions_premiere_date"), "productions", ["premiere_date"], unique=False
    )
    op.create_index(op.f("ix_productions_theatre_id"), "productions", ["theatre_id"], unique=False)
    op.create_index(
        "ix_productions_title_trgm",
        "productions",
        ["title"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"title": "gin_trgm_ops"},
    )
    op.create_table(
        "raw_posts",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("external_id", sa.Text(), nullable=False),
        sa.Column("version", sa.SmallInteger(), server_default=sa.text("1"), nullable=False),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("edited_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column(
            "links",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'"),
            nullable=False,
        ),
        sa.Column(
            "media",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'"),
            nullable=False,
        ),
        sa.Column("forwarded_from", sa.Text(), nullable=True),
        sa.Column("grouped_id", sa.Text(), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "collected_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["source_id"], ["sources.id"], name=op.f("fk_raw_posts_source_id_sources")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_raw_posts")),
        sa.UniqueConstraint(
            "source_id",
            "external_id",
            "version",
            name=op.f("uq_raw_posts_source_id_external_id_version"),
        ),
    )
    op.create_index(op.f("ix_raw_posts_published_at"), "raw_posts", ["published_at"], unique=False)
    op.create_index(op.f("ix_raw_posts_source_id"), "raw_posts", ["source_id"], unique=False)
    op.create_table(
        "credits",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("production_id", sa.Integer(), nullable=False),
        sa.Column("person_id", sa.Integer(), nullable=False),
        sa.Column(
            "role",
            sa.Enum(
                "director",
                "playwright",
                "dramaturg",
                "set_designer",
                "costume_designer",
                "lighting_designer",
                "video_designer",
                "composer",
                "choreographer",
                "actor",
                "other",
                name="creditrole",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("character", sa.Text(), nullable=True),
        sa.Column("position", sa.SmallInteger(), server_default=sa.text("0"), nullable=False),
        sa.ForeignKeyConstraint(
            ["person_id"], ["persons.id"], name=op.f("fk_credits_person_id_persons")
        ),
        sa.ForeignKeyConstraint(
            ["production_id"],
            ["productions.id"],
            name=op.f("fk_credits_production_id_productions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_credits")),
    )
    op.create_index(op.f("ix_credits_person_id"), "credits", ["person_id"], unique=False)
    op.create_index(op.f("ix_credits_production_id"), "credits", ["production_id"], unique=False)
    op.create_table(
        "drafts",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column(
            "kind",
            sa.Enum(
                "production",
                "review",
                "photos",
                "update",
                name="draftkind",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "approved",
                "rejected",
                "merged",
                name="draftstatus",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("production_id", sa.Integer(), nullable=True),
        sa.Column("match_confidence", sa.Float(), nullable=True),
        sa.Column("bot_message_id", sa.BigInteger(), nullable=True),
        sa.Column("decided_by", sa.Text(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["production_id"], ["productions.id"], name=op.f("fk_drafts_production_id_productions")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_drafts")),
    )
    op.create_index(op.f("ix_drafts_status"), "drafts", ["status"], unique=False)
    op.create_table(
        "extractions",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("raw_post_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "kind",
            sa.Enum(
                "classification", "entities", name="extractionkind", native_enum=False, length=32
            ),
            nullable=False,
        ),
        sa.Column("model", sa.Text(), nullable=False),
        sa.Column("prompt_version", sa.String(length=32), nullable=False),
        sa.Column("label", sa.String(length=32), nullable=True),
        sa.Column(
            "data",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["raw_post_id"],
            ["raw_posts.id"],
            name=op.f("fk_extractions_raw_post_id_raw_posts"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_extractions")),
    )
    op.create_index(
        op.f("ix_extractions_raw_post_id"), "extractions", ["raw_post_id"], unique=False
    )
    op.create_table(
        "photos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("production_id", sa.Integer(), nullable=False),
        sa.Column("raw_post_id", sa.BigInteger(), nullable=True),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("photographer", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["production_id"],
            ["productions.id"],
            name=op.f("fk_photos_production_id_productions"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["raw_post_id"], ["raw_posts.id"], name=op.f("fk_photos_raw_post_id_raw_posts")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_photos")),
        sa.UniqueConstraint("storage_key", name=op.f("uq_photos_storage_key")),
    )
    op.create_index(op.f("ix_photos_production_id"), "photos", ["production_id"], unique=False)
    op.create_table(
        "reviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("production_id", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=True),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("raw_post_id", sa.BigInteger(), nullable=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("quote", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["author_id"], ["persons.id"], name=op.f("fk_reviews_author_id_persons")
        ),
        sa.ForeignKeyConstraint(
            ["production_id"],
            ["productions.id"],
            name=op.f("fk_reviews_production_id_productions"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["raw_post_id"], ["raw_posts.id"], name=op.f("fk_reviews_raw_post_id_raw_posts")
        ),
        sa.ForeignKeyConstraint(
            ["source_id"], ["sources.id"], name=op.f("fk_reviews_source_id_sources")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reviews")),
        sa.UniqueConstraint("production_id", "url", name=op.f("uq_reviews_production_id_url")),
    )
    op.create_index(op.f("ix_reviews_author_id"), "reviews", ["author_id"], unique=False)
    op.create_index(op.f("ix_reviews_production_id"), "reviews", ["production_id"], unique=False)
    op.create_index(op.f("ix_reviews_published_at"), "reviews", ["published_at"], unique=False)
    op.create_table(
        "draft_posts",
        sa.Column("draft_id", sa.BigInteger(), nullable=False),
        sa.Column("raw_post_id", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(
            ["draft_id"],
            ["drafts.id"],
            name=op.f("fk_draft_posts_draft_id_drafts"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["raw_post_id"],
            ["raw_posts.id"],
            name=op.f("fk_draft_posts_raw_post_id_raw_posts"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("draft_id", "raw_post_id", name=op.f("pk_draft_posts")),
    )


def downgrade() -> None:
    op.drop_table("draft_posts")
    op.drop_index(op.f("ix_reviews_published_at"), table_name="reviews")
    op.drop_index(op.f("ix_reviews_production_id"), table_name="reviews")
    op.drop_index(op.f("ix_reviews_author_id"), table_name="reviews")
    op.drop_table("reviews")
    op.drop_index(op.f("ix_photos_production_id"), table_name="photos")
    op.drop_table("photos")
    op.drop_index(op.f("ix_extractions_raw_post_id"), table_name="extractions")
    op.drop_table("extractions")
    op.drop_index(op.f("ix_drafts_status"), table_name="drafts")
    op.drop_table("drafts")
    op.drop_index(op.f("ix_credits_production_id"), table_name="credits")
    op.drop_index(op.f("ix_credits_person_id"), table_name="credits")
    op.drop_table("credits")
    op.drop_index(op.f("ix_raw_posts_source_id"), table_name="raw_posts")
    op.drop_index(op.f("ix_raw_posts_published_at"), table_name="raw_posts")
    op.drop_table("raw_posts")
    op.drop_index(
        "ix_productions_title_trgm",
        table_name="productions",
        postgresql_using="gin",
        postgresql_ops={"title": "gin_trgm_ops"},
    )
    op.drop_index(op.f("ix_productions_theatre_id"), table_name="productions")
    op.drop_index(op.f("ix_productions_premiere_date"), table_name="productions")
    op.drop_table("productions")
    op.drop_table("stages")
    op.drop_index(op.f("ix_sources_theatre_id"), table_name="sources")
    op.drop_index(op.f("ix_sources_person_id"), table_name="sources")
    op.drop_table("sources")
    op.drop_index(
        "ix_theatres_name_trgm",
        table_name="theatres",
        postgresql_using="gin",
        postgresql_ops={"name": "gin_trgm_ops"},
    )
    op.drop_index(op.f("ix_theatres_city_id"), table_name="theatres")
    op.drop_table("theatres")
    op.drop_index(op.f("ix_cities_country_id"), table_name="cities")
    op.drop_table("cities")
    op.drop_index(
        "ix_persons_full_name_trgm",
        table_name="persons",
        postgresql_using="gin",
        postgresql_ops={"full_name": "gin_trgm_ops"},
    )
    op.drop_table("persons")
    op.drop_table("countries")
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")

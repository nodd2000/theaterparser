# theaterparser

Агрегатор информации о драматических спектаклях России по образцу nachtkritik.de:
каталог текущего репертуара и сводка прессы по каждой постановке. Источники — Telegram-каналы
театров, критиков и СМИ, а также сайты театров.

План и решения — [`docs/PLAN.md`](docs/PLAN.md), стартовые источники — [`docs/sources.md`](docs/sources.md).

## Структура

```
src/theaterparser/
  config.py        настройки из переменных окружения / .env
  db/              SQLAlchemy-модели, сессии
  api/             FastAPI-приложение
  vpn/             сборка конфига Xray из ссылки vless:// / trojan://
migrations/        миграции Alembic
docker/            Dockerfile приложения и контейнера vpn
tests/
```

## Запуск в Docker

```bash
cp .env.example .env          # вписать XRAY_LINK и пароли
docker compose up -d --build
curl localhost:8000/health
```

Сервисы: `postgres`, `redis`, `migrate` (применяет миграции и завершается), `api`, `vpn`.
Прокси `vpn` (SOCKS5 `vpn:1080`, HTTP `vpn:8118`) доступен только внутри docker-сети.
Вместо ссылки можно положить готовый конфиг в `docker/vpn/config.json` — он имеет приоритет.

## Локальная разработка

Нужны Python 3.12+, [uv](https://docs.astral.sh/uv/), PostgreSQL 16.

```bash
uv sync
createdb theater
uv run alembic upgrade head
uv run uvicorn theaterparser.api.app:app --reload
```

Проверки (то же, что в CI):

```bash
uv run ruff check . && uv run ruff format --check .
uv run mypy
TEST_DATABASE_URL=postgresql+asyncpg://theater:theater@localhost:5432/theater_test uv run pytest
```

Новая миграция после изменения моделей:

```bash
uv run alembic revision --autogenerate -m "описание"
```

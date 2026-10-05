from sqlalchemy.engine import URL, make_url


def normalize_asyncpg_url(database_url: str) -> tuple[URL, dict[str, str]]:
    """Move libpq SSL query options into asyncpg connection options."""
    url = make_url(database_url)
    if url.drivername != "postgresql+asyncpg":
        return url, {}

    query = dict(url.query)
    sslmode = query.pop("sslmode", None)
    query.pop("channel_binding", None)

    connect_args = {"ssl": sslmode} if sslmode else {}
    return url.set(query=query), connect_args

from database.hub.hub import normalize_database_url, safe_database_endpoint


def test_normalize_postgresql_urls():
    assert normalize_database_url("postgresql://user:pass@host/db") == (
        "postgresql+psycopg://user:pass@host/db"
    )
    assert normalize_database_url("postgres://user:pass@host/db") == (
        "postgresql+psycopg://user:pass@host/db"
    )


def test_normalize_database_url_leaves_other_schemes_unchanged():
    url = "sqlite:///./data/econojin.db"
    assert normalize_database_url(url) == url


def test_safe_database_endpoint_does_not_include_credentials():
    endpoint = safe_database_endpoint("postgresql+psycopg://user:secret@db.example:5432/app")
    assert endpoint == {"scheme": "postgresql+psycopg", "host": "db.example", "port": 5432}

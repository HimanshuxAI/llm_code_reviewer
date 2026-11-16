from sqlalchemy import create_engine, inspect

from app.db.models import Base


def test_models_create_tables():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    tables = set(inspect(engine).get_table_names())
    assert {"users", "reviews"} <= tables

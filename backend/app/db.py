from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.engine import Engine

from app.config import settings

try:
    from google.cloud.sql.connector import Connector, IPTypes
except ImportError:  # pragma: no cover
    Connector = None
    IPTypes = None


def create_db_engine() -> Engine:
    if settings.instance_connection_name:
        if not all([settings.db_user, settings.db_pass, settings.db_name]):
            raise ValueError(
                "DB_USER, DB_PASS, and DB_NAME are required when INSTANCE_CONNECTION_NAME is set"
            )
        if Connector is None or IPTypes is None:
            raise ImportError(
                "google-cloud-sql-connector is required when using Cloud SQL connector"
            )

        connector = Connector()
        ip_type = IPTypes.PRIVATE if settings.private_ip else IPTypes.PUBLIC

        def getconn():
            return connector.connect(
                settings.instance_connection_name,
                "pymysql",
                user=settings.db_user,
                password=settings.db_pass,
                db=settings.db_name,
                ip_type=ip_type,
            )

        return create_engine(
            "mysql+pymysql://",
            creator=getconn,
            pool_pre_ping=True,
            future=True,
        )

    return create_engine(
        settings.db_url,
        connect_args=settings.sqlalchemy_connect_args,
        pool_pre_ping=True,
        future=True,
    )


engine = create_db_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

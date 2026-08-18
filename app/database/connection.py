from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Determine if the connection is to an SQLite database.
# SQLite requires different connection arguments to allow multi-threading in web requests.
is_sqlite = settings.DATABASE_URL.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}

# pool_pre_ping=True checks connection health before issuing queries.
# This prevents 'MySQL server has gone away' issues in production/Docker.
engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)

# Each instance of SessionLocal will be a database session.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    Dependency injector to provide a database session per web request.
    Closes the session once the request has completed, preventing connection leaks.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

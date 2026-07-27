import json
import datetime

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, BigInteger
from sqlalchemy.orm import declarative_base, sessionmaker

from config import DATABASE_URL

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class Connection(Base):
    """A linked destination: a Telegram channel, Discord webhook, Twitter/X
    account, or Facebook Page that posts can be published to."""

    __tablename__ = "connections"

    id = Column(Integer, primary_key=True)
    telegram_user_id = Column(BigInteger, index=True)
    platform = Column(String(20))       # telegram | discord | twitter | facebook
    name = Column(String(100))          # nickname the user picks
    credentials = Column(Text)          # JSON blob, shape depends on platform
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    def creds(self):
        return json.loads(self.credentials)


class Post(Base):
    """A single scheduled (or already sent) post."""

    __tablename__ = "posts"

    id = Column(Integer, primary_key=True)
    telegram_user_id = Column(BigInteger, index=True)
    content = Column(Text)
    media_file_id = Column(String(300), nullable=True)   # Telegram file_id of attached photo
    connection_ids = Column(Text)       # JSON list of Connection.id to publish to
    scheduled_time = Column(DateTime)   # UTC
    status = Column(String(20), default="scheduled")  # scheduled|sent|failed|cancelled
    result_log = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


def init_db():
    Base.metadata.create_all(engine)


def get_session():
    return SessionLocal()

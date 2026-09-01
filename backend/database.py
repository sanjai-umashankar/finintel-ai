import datetime
import json
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

DATABASE_URL = "sqlite:///./finintel.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    risk_tolerance = Column(String, default="Moderate")          # Conservative | Moderate | Aggressive
    investment_horizon = Column(String, default="Medium Term")   # Short Term | Medium Term | Long Term
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    portfolio = relationship("PortfolioItem", back_populates="user", cascade="all, delete-orphan")
    watchlist = relationship("WatchlistItem", back_populates="user", cascade="all, delete-orphan")
    analyses = relationship("Analysis", back_populates="user", cascade="all, delete-orphan")


class PortfolioItem(Base):
    __tablename__ = "portfolio"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    symbol = Column(String, nullable=False)
    company_name = Column(String, default="")
    quantity = Column(Float, default=0)
    average_price = Column(Float, default=0)

    user = relationship("User", back_populates="portfolio")


class WatchlistItem(Base):
    __tablename__ = "watchlist"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    symbol = Column(String, nullable=False)

    user = relationship("User", back_populates="watchlist")


class DocumentRecord(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    stock_symbol = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String, default="processing")   # processing | processed | failed
    chunk_count = Column(Integer, default=0)


class Analysis(Base):
    __tablename__ = "analyses"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    symbol = Column(String, nullable=False)
    technical_result = Column(Text)     # JSON
    fundamental_result = Column(Text)   # JSON
    sentiment_result = Column(Text)     # JSON
    risk_result = Column(Text)          # JSON
    final_result = Column(Text)         # JSON
    confidence = Column(Float)
    analysis_time_ms = Column(Float)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="analyses")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "symbol": self.symbol,
            "technical_result": json.loads(self.technical_result),
            "fundamental_result": json.loads(self.fundamental_result),
            "sentiment_result": json.loads(self.sentiment_result),
            "risk_result": json.loads(self.risk_result),
            "final_result": json.loads(self.final_result),
            "confidence": self.confidence,
            "analysis_time_ms": self.analysis_time_ms,
            "created_at": self.created_at.isoformat(),
        }


class MetricEvent(Base):
    """One row per analysis attempt, used to compute the metrics dashboard."""
    __tablename__ = "metric_events"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String)
    success = Column(Boolean, default=True)
    analysis_time_ms = Column(Float, default=0)
    confidence = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

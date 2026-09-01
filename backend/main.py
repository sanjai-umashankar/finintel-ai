import time
import uuid
import json
import datetime

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database import (
    init_db, get_db, User, PortfolioItem, WatchlistItem,
    DocumentRecord, Analysis, MetricEvent,
)
from backend.models.schemas import (
    UserProfileIn, UserProfileOut, PortfolioItemIn, PortfolioItemOut,
    WatchlistItemIn, WatchlistItemOut,
)
from backend.data.market_data import get_market_data, get_price_history, list_supported_symbols
from backend.data.news_data import get_news
from backend.rag.ingestion import ingest_document
from backend.agents.technical_agent import run_technical_agent
from backend.agents.fundamental_agent import run_fundamental_agent
from backend.agents.sentiment_agent import run_sentiment_agent
from backend.agents.risk_agent import run_risk_agent
from backend.agents.synthesis_agent import run_synthesis_agent

app = FastAPI(title="FinIntel AI", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # local prototype only — restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------
@app.post("/api/profile", response_model=UserProfileOut)
def create_profile(payload: UserProfileIn, db: Session = Depends(get_db)):
    user = User(
        name=payload.name,
        risk_tolerance=payload.risk_tolerance,
        investment_horizon=payload.investment_horizon,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.get("/api/profile", response_model=list[UserProfileOut])
def list_profiles(db: Session = Depends(get_db)):
    return db.query(User).order_by(User.id.desc()).all()


@app.get("/api/profile/{user_id}", response_model=UserProfileOut)
def get_profile(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return user


# ---------------------------------------------------------------------------
# Portfolio
# ---------------------------------------------------------------------------
@app.post("/api/portfolio", response_model=PortfolioItemOut)
def add_portfolio_item(payload: PortfolioItemIn, db: Session = Depends(get_db)):
    if not db.query(User).get(payload.user_id):
        raise HTTPException(404, "User not found")
    item = PortfolioItem(**payload.dict())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.get("/api/portfolio", response_model=list[PortfolioItemOut])
def get_portfolio(user_id: int, db: Session = Depends(get_db)):
    return db.query(PortfolioItem).filter(PortfolioItem.user_id == user_id).all()


@app.delete("/api/portfolio/{item_id}")
def delete_portfolio_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(PortfolioItem).get(item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    db.delete(item)
    db.commit()
    return {"status": "deleted"}


# ---------------------------------------------------------------------------
# Watchlist
# ---------------------------------------------------------------------------
@app.post("/api/watchlist", response_model=WatchlistItemOut)
def add_watchlist_item(payload: WatchlistItemIn, db: Session = Depends(get_db)):
    if not db.query(User).get(payload.user_id):
        raise HTTPException(404, "User not found")
    item = WatchlistItem(**payload.dict())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.get("/api/watchlist", response_model=list[WatchlistItemOut])
def get_watchlist(user_id: int, db: Session = Depends(get_db)):
    return db.query(WatchlistItem).filter(WatchlistItem.user_id == user_id).all()


# ---------------------------------------------------------------------------
# Documents (RAG)
# ---------------------------------------------------------------------------
@app.post("/api/documents/upload")
async def upload_document(
    symbol: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    raw = await file.read()
    record = DocumentRecord(filename=file.filename, stock_symbol=symbol.upper(), status="processing")
    db.add(record)
    db.commit()
    db.refresh(record)

    document_id = f"doc-{record.id}-{uuid.uuid4().hex[:6]}"
    result = ingest_document(document_id, file.filename, symbol, raw)

    record.status = result["status"]
    record.chunk_count = result["chunks"]
    db.commit()

    return {
        "document_id": document_id,
        "filename": file.filename,
        "symbol": symbol.upper(),
        "status": result["status"],
        "chunks": result["chunks"],
        "reason": result.get("reason"),
    }


@app.get("/api/documents")
def list_documents(db: Session = Depends(get_db)):
    docs = db.query(DocumentRecord).order_by(DocumentRecord.id.desc()).all()
    return [
        {
            "id": d.id,
            "filename": d.filename,
            "stock_symbol": d.stock_symbol,
            "upload_date": d.upload_date.isoformat(),
            "status": d.status,
            "chunk_count": d.chunk_count,
        }
        for d in docs
    ]


# ---------------------------------------------------------------------------
# Stock lookup
# ---------------------------------------------------------------------------
@app.get("/api/symbols")
def symbols():
    return {"symbols": list_supported_symbols()}


@app.get("/api/stock/{symbol}")
def stock_overview(symbol: str):
    market = get_market_data(symbol)
    history = get_price_history(symbol)
    return {"market": market, "price_history": history}


# ---------------------------------------------------------------------------
# Analysis pipeline
# ---------------------------------------------------------------------------
@app.post("/api/analyze/{symbol}")
def analyze_stock(symbol: str, user_id: int, db: Session = Depends(get_db)):
    start = time.perf_counter()
    symbol = symbol.upper()

    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(404, "User not found")

    portfolio = [
        {"symbol": p.symbol, "quantity": p.quantity, "average_price": p.average_price}
        for p in db.query(PortfolioItem).filter(PortfolioItem.user_id == user_id).all()
    ]

    success = True
    try:
        market = get_market_data(symbol)
        price_history = get_price_history(symbol)
        news = get_news(symbol)

        # Technical, Fundamental, Sentiment agents run independently of each other.
        technical = run_technical_agent(price_history, market.get("volume"), market.get("avg_volume"))
        fundamental = run_fundamental_agent(market, symbol)
        sentiment = run_sentiment_agent(news)

        # Risk agent depends on the outputs above + the user's profile/portfolio.
        risk = run_risk_agent(
            risk_tolerance=user.risk_tolerance,
            investment_horizon=user.investment_horizon,
            portfolio=portfolio,
            symbol=symbol,
            technical=technical,
            fundamental=fundamental,
            sentiment=sentiment,
        )

        # Synthesis agent combines everything into the final personalized call.
        final = run_synthesis_agent(
            technical=technical,
            fundamental=fundamental,
            sentiment=sentiment,
            risk=risk,
            user_profile={"risk_tolerance": user.risk_tolerance, "investment_horizon": user.investment_horizon},
        )
    except Exception as exc:  # the pipeline itself should never 500 during a demo
        success = False
        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
        db.add(MetricEvent(symbol=symbol, success=False, analysis_time_ms=elapsed_ms, confidence=0))
        db.commit()
        raise HTTPException(500, f"Analysis pipeline failed: {exc}")

    elapsed_ms = round((time.perf_counter() - start) * 1000, 1)

    record = Analysis(
        user_id=user_id,
        symbol=symbol,
        technical_result=json.dumps(technical),
        fundamental_result=json.dumps(fundamental),
        sentiment_result=json.dumps(sentiment),
        risk_result=json.dumps(risk),
        final_result=json.dumps(final),
        confidence=final["confidence"],
        analysis_time_ms=elapsed_ms,
    )
    db.add(record)
    db.add(MetricEvent(symbol=symbol, success=success, analysis_time_ms=elapsed_ms, confidence=final["confidence"]))
    db.commit()
    db.refresh(record)

    return {
        "analysis_id": record.id,
        "symbol": symbol,
        "market": market,
        "price_history": price_history,
        "technical": technical,
        "fundamental": fundamental,
        "sentiment": sentiment,
        "risk": risk,
        "final": final,
        "analysis_time_ms": elapsed_ms,
    }


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------
@app.get("/api/analysis/history")
def analysis_history(user_id: int, db: Session = Depends(get_db)):
    rows = (
        db.query(Analysis)
        .filter(Analysis.user_id == user_id)
        .order_by(Analysis.id.desc())
        .limit(50)
        .all()
    )
    return [r.to_dict() for r in rows]


@app.get("/api/analysis/{analysis_id}")
def get_analysis(analysis_id: int, db: Session = Depends(get_db)):
    row = db.query(Analysis).get(analysis_id)
    if not row:
        raise HTTPException(404, "Analysis not found")
    return row.to_dict()


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------
@app.get("/api/metrics")
def metrics(db: Session = Depends(get_db)):
    total = db.query(func.count(MetricEvent.id)).scalar() or 0
    successes = db.query(func.count(MetricEvent.id)).filter(MetricEvent.success == True).scalar() or 0  # noqa: E712
    failures = total - successes
    avg_time = db.query(func.avg(MetricEvent.analysis_time_ms)).filter(MetricEvent.success == True).scalar() or 0  # noqa: E712
    avg_conf = db.query(func.avg(MetricEvent.confidence)).filter(MetricEvent.success == True).scalar() or 0  # noqa: E712

    return {
        "total_analyses": total,
        "successful_analyses": successes,
        "failed_analyses": failures,
        "average_analysis_time_ms": round(avg_time, 1),
        "average_confidence": round(avg_conf, 1),
    }


@app.get("/")
def root():
    return {
        "app": "FinIntel AI",
        "status": "running",
        "docs": "/docs",
        "note": "Open frontend/index.html separately and point it at this server.",
    }

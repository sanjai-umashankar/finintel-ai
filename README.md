# FinIntel AI - Multi-Agent Financial Analysis Platform

FinIntel AI is a personal financial advisor that uses multiple specialized agents to analyze stocks and provide personalized recommendations. The system combines technical analysis, fundamental analysis, sentiment analysis, risk assessment, and intelligent synthesis to offer data-driven investment insights.

## Features

- **Multi-Agent System**: Five distinct agents collaborate to analyze stocks:
  - **Technical Agent**: Analyzes price trends, moving averages, RSI, and MACD.
  - **Fundamental Agent**: Evaluates company financials, growth metrics, and leverage ratios.
  - **Sentiment Agent**: Processes news headlines and social sentiment.
  - **Risk Agent**: Assesses portfolio risk, concentration, and volatility.
  - **Synthesis Agent**: Combines all signals to generate a final recommendation.

- **Personalization**:
  - Users can create profiles with risk tolerance (Conservative, Moderate, Aggressive).
  - Portfolio tracking with position sizing.
  - Recommendations are tailored to the user's risk profile and existing holdings.

- **Data Integration**:
  - **Market Data**: Fetches historical stock data using `yfinance` (or uses demo data if `yfinance` is unavailable).
  - **News & Sentiment**: Analyzes recent headlines for market sentiment.
  - **Documents**: Supports RAG (Retrieval-Augmented Generation) by analyzing uploaded documents for fundamental insights.

- **RAG (Retrieval-Augmented Generation)**:
  - Users can upload documents (PDF, TXT) to provide context for analysis.
  - Documents are chunked and indexed for efficient retrieval.
  - The Fundamental Agent uses retrieved documents to enhance its analysis.

- **User Interface**:
  - **Single-Page Application**: Built with Vanilla JavaScript, Tailwind CSS, and Recharts for data visualization.
  - **Responsive Design**: Clean, modern interface with dark mode support.
  - **Interactive Charts**: Visualizes technical indicators and portfolio performance.

## Project Structure

```
finintel-ai/
├── frontend/
│   └── index.html            # Main UI (HTML, CSS, JavaScript)
├── backend/
│   ├── agents/                # Agent implementations (Technical, Fundamental, etc.)
│   ├── data/                  # Data fetching modules (market_data.py, news_data.py)
│   ├── rag/                   # RAG pipeline (ingestion, embeddings, retrieval)
│   ├── models/                # Pydantic data models
│   ├── database.py            # Database setup (SQLite)
│   └── main.py                # FastAPI application entry point
├── requirements.txt           # Python dependencies
└── .env.example               # Environment variable template
```

## Installation and Setup

### Prerequisites
- Python 3.8+
- pip (Python package installer)

### Installation

1.  **Clone the repository** (or download the source code).

2.  **Navigate to the backend directory**:
    ```bash
    cd finintel-ai
    ```

3.  **Create a virtual environment** (recommended):
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    ```

4.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

5.  **Run the backend server**:
    ```bash
    python3 -m uvicorn backend.main:app --reload --port 8000
    ```

The API will be available at `http://localhost:8000`.

### Running the Frontend

The frontend is a self-contained HTML file that communicates with the FastAPI backend.

1.  Open `frontend/index.html` directly in your web browser.
2.  Alternatively, serve the frontend directory:
    ```bash
    cd frontend
    python3 -m http.server 5500
    ```
    Then open `http://localhost:5500` in your browser.

## Usage

1.  **Create a User Profile**:
    - Go to the **Profile** tab.
    - Enter your name and select your risk tolerance (Conservative, Moderate, or Aggressive).
    - Click "Create Profile".

2.  **Manage Portfolio**:
    - Go to the **Portfolio** tab.
    - Add stocks by entering the ticker symbol and quantity.
    - The system will calculate the percentage weight of each holding.

3.  **Analyze Stocks**:
    - Go to the **Analyze** tab.
    - Select a stock from the dropdown menu (or enter a ticker symbol).
    - Click **LOAD** to fetch market data.
    - Click **ANALYSE STOCK** to run the multi-agent analysis.

4.  **Upload Documents**:
    - Go to the **Documents** tab.
    - Upload PDF or TXT files containing company information.
    - These documents will be used by the Fundamental Agent for analysis.

5.  **View Results**:
    - After analysis, review the agent cards to understand the reasoning behind the recommendation.
    - The **Synthesis Agent** provides a final verdict (e.g., BUY, HOLD, SELL, ACCUMULATE, REDUCE) with an explanation and confidence score.

## Technical Details

### RAG Implementation
- **Embedding**: Uses `sentence-transformers` (via `backend/rag/embeddings.py`) for text embeddings.
- **Storage**: Uses `chromadb` for persistent vector storage.
- **Ingestion**: Documents are split into chunks, embedded, and stored in a collection named after the ticker symbol.

### Data Flow
1.  **Request**: User selects a stock via the frontend.
2.  **Data Fetching**: `backend/data/market_data.py` fetches historical prices (tries `yfinance`, falls back to demo data).
3.  **RAG**: `backend/rag/retrieval.py` retrieves relevant documents for the symbol.
4.  **Agent Execution**: The five agents process the data in sequence:
    - Technical Agent -> Fundamental Agent -> Sentiment Agent (parallel)
    - Risk Agent -> Synthesis Agent (sequential)
5.  **Response**: The combined result is sent back to the frontend for display.

### Agents
- **Technical Agent**: Calculates Simple Moving Averages (SMA), Relative Strength Index (RSI), and Moving Average Convergence Divergence (MACD).
- **Fundamental Agent**: Analyzes Revenue Growth, Profit Growth, and Debt-to-Equity ratio.
- **Sentiment Agent**: Counts positive vs. negative keywords in news headlines.
- **Risk Agent**: Checks for portfolio concentration and volatility.
- **Synthesis Agent**: Weighs signals from other agents and adjusts based on user risk profile and portfolio context.

## Notes
- The system uses **demo data** for RELIANCE, TCS, and HDFCBANK to ensure the application works without live API keys.
- The RAG system is fully functional; users can upload their own documents to test it.
- The confidence scores are calculated based on the quality and quantity of available data.

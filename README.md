MLB Totals ML Betting System

A production-grade machine learning system for predicting MLB game totals (Over/Under) using:

* MLB Stats API (game + player + lineup data)
* The Odds API (market totals)
* Feature engineering (pitching, bullpen, lineup, park, market)
* XGBoost regression model
* CLV (Closing Line Value) tracking
* FastAPI inference service
* ETL workers + automated retraining
* Telegram signal bot

⸻

1. SYSTEM GOAL

The system predicts MLB total runs and identifies +EV betting opportunities by comparing:

* Model predicted total
* Market-implied total (closing line)

Output example:

Game: NYY vs BOS
Model Total: 8.7
Market Line: 8.5
Edge: +0.20
Recommendation: OVER
EV: +2.3%

⸻

2. ARCHITECTURE

MLB Stats API ───────┐
                      │
The Odds API ────────┤
                      ▼
              ETL WORKERS
        (data ingestion + normalization)
                      │
                      ▼
            SUPABASE DATABASE
 (games, features, odds, predictions, bets)
                      │
                      ▼
            FEATURE ENGINEERING
 (lineup + bullpen + pitching + market)
                      │
                      ▼
               XGBOOST MODEL
                      │
                      ▼
            FASTAPI INFERENCE API
                      │
                      ▼
             TELEGRAM BOT ALERTS

⸻

3. PROJECT STRUCTURE

mlb-totals-engine/
│
├── app/
│   ├── main.py
│   ├── api/
│   ├── services/
│   ├── workers/
│   ├── telegram/
│   └── db/
│
├── pipeline/
│   ├── run_etl.py
│   ├── feature_builder.py
│
├── ml/
│   ├── train.py
│   ├── inference.py
│   ├── model.pkl
│
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md

⸻

4. KEY FEATURES

Data features

* Starting pitcher strength differential
* Offensive rating (wRC+, OPS proxies)
* Bullpen fatigue index (last 3 days usage)
* Lineup strength (confirmed batting order)
* Park factor adjustment
* Weather impact (optional extension)
* Market line (opening + closing + pinnacle proxy)

⸻

Market features

* Odds snapshots (time series)
* Line movement tracking
* Closing line reconstruction
* CLV calculation

⸻

5. MACHINE LEARNING MODEL

* Model: XGBoost Regressor
* Target: Total runs scored
* Validation: TimeSeriesSplit (no leakage)
* Retraining: Weekly (Monday cycle)

⸻

Metrics tracked

Metric	Meaning
MAE	prediction accuracy
CLV	market beating ability
ROI	simulated profit
Edge rate	+EV bet accuracy

⸻

6. DATA PIPELINE

Step 1: Build dataset

python pipeline/run_pipeline.py --build

Fetches:

* MLB games
* lineups
* odds
* team + pitcher stats

⸻

Step 2: Train model

python pipeline/run_pipeline.py --train

Outputs:

* trained XGBoost model
* evaluation metrics

⸻

Step 3: Predict games

python pipeline/run_pipeline.py --predict

Generates:

* predicted totals
* EV calculations
* betting recommendations

⸻

7. FASTAPI ENDPOINTS

Prediction

GET /predict/{game_id}

Response:

{
  "game_id": "12345",
  "prediction": 8.7,
  "market_line": 8.5,
  "edge": 0.2
}

⸻

Bet signal

POST /bet/{game_id}

Returns:

* OVER / UNDER recommendation
* calculated edge
* bet amount suggestion

⸻

8. ETL WORKERS

Runs continuously:

Every 5–10 minutes:

* Odds snapshot ingestion
* Feature updates

Daily:

* Prediction refresh

Weekly:

* Model retraining

⸻

9. TELEGRAM BOT

Sends real-time alerts:

* +EV betting opportunities
* lineup-based adjustments
* sharp line movement signals

Example:

MLB TOTALS SIGNAL
Game: LAD vs SF
Model: 7.9
Line: 7.5
EV: +3.1%
Recommendation: OVER
Confidence: HIGH

⸻

10. SUPABASE TABLES

Core tables:

* games
* lineups
* features
* odds_snapshots
* predictions
* bets
* model_runs
* game_results

⸻

11. DEPLOYMENT

Run locally

uvicorn app.main:app --reload

⸻

Docker

docker-compose up --build

⸻

12. KEY DESIGN PRINCIPLES

1. No data leakage

Only pre-game features allowed

2. Market-aware ML

Odds are part of feature space

3. Lineup sensitivity

Late lineup changes are critical signal source

4. CLV is truth metric

Model quality is measured against closing line, not accuracy alone

⸻

13. WHAT THIS SYSTEM IS

This is not a prediction tool.

It is:

A closed-loop betting intelligence system that learns from MLB data and market inefficiencies to identify +EV totals bets.

⸻

14. FUTURE EXTENSIONS

* Steam detection engine (sharp money tracking)
* Automated bet execution
* Reinforcement learning on CLV
* Multi-sport expansion (NBA / NHL / NFL)
* Real-time arbitrage detection

⸻

15. QUICK START

git clone <repo>
cd mlb-totals-engine
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload

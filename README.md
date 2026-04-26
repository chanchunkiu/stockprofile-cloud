# 📈 Stock Portfolio Tracker

A personal finance and investment tracker built to learn cloud infrastructure — not just another web app.

## What it does

- Add, edit and delete stock holdings with ticker, shares and average buy price
- Fetches real-time stock prices via Yahoo Finance
- Calculates profit/loss in value and percentage per holding
- Shows total portfolio value and overall return
- Pie chart breakdown of portfolio allocation
- Set allocation rules (min/max/target %) per ticker with rebalancing suggestions
- Track monthly contribution goals

## Architecture

The web UI is not the main focus — the infrastructure is.

```
Phone / Browser
      │
      ▼
Cloudflare Zero Trust
  (Google login required)
      │
      ▼
Cloudflare Worker
  (proxies request, adds secret header)
      │
      ▼
Google Cloud Run
  (Flask app, validates secret header)
      │
      ├──▶ Google Firestore  (holdings, rules, goals)
      └──▶ Google Cloud Storage  (avatar image)
```

## Tech Stack

**Backend**
- Python + Flask
- Gunicorn (WSGI server)
- Google Cloud Run (serverless container)
- Google Firestore (NoSQL database)
- Google Cloud Storage (avatar image)
- Yahoo Finance API (real-time prices)

**Infrastructure & Security**
- Cloudflare Zero Trust (identity-aware access proxy)
- Cloudflare Workers (reverse proxy, blocks direct Cloud Run access)
- Google Cloud Build (CI/CD image builds)
- Google Container Registry (Docker image storage)

**Domain**
- Custom subdomain via Cloudflare DNS
- Cloudflare Worker handles SSL termination (avoids Full Strict SSL conflict with Cloud Run)

## Security Model

- Zero Trust enforces Google login before any request reaches the app
- Cloudflare Worker injects a secret header on every request
- Flask rejects any request missing the correct secret header
- Cloud Run URL is not publicly advertised
- Google Cloud Storage bucket is fully private — avatar served through Flask

## Why Cloudflare Worker instead of CNAME?

Pointing a Cloudflare proxied CNAME directly to Cloud Run causes an SSL conflict — Cloudflare Full Strict mode expects a Cloudflare Origin Certificate on the backend, but Cloud Run uses Google's own certificate. The Worker runs inside Cloudflare's network, so SSL terminates at Cloudflare and the Worker makes a separate internal request to Cloud Run. No conflict.

## Local Development

```bash
git clone https://github.com/chanchunkiu/stockprofile-cloud.git
cd stockprofile-cloud
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

## Deploy to Cloud Run

```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/portfolio
gcloud run deploy portfolio \
  --image gcr.io/YOUR_PROJECT_ID/portfolio \
  --region asia-northeast1 \
  --set-env-vars SECRET_KEY=your-secret-here
```

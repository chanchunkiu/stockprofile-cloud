# 📈 Stock Portfolio Tracker

A personal investment tracker built as a hands-on project to learn cloud infrastructure and security. The web UI is a means to an end — the real focus is the backend architecture.

## Screenshots

**ZeroTrust login**

<img width="950" height="1359" alt="image" src="https://github.com/user-attachments/assets/2c3dfffc-6932-4978-8473-cac2d9bddbac" />

**Dashboard — portfolio**

<img width="1334" height="1013" alt="image" src="https://github.com/user-attachments/assets/4467f010-e06d-47ff-b382-0ec6adcc2117" />


**Holdings — modify holdings**

<img width="1347" height="1054" alt="image" src="https://github.com/user-attachments/assets/4d172589-c934-4078-b3b8-e4900d17bd8b" />


**Goals and action — Give recommendations based on goals**

<img width="1331" height="1065" alt="image" src="https://github.com/user-attachments/assets/7e08d30a-3efe-4445-ac02-b6caa49bfdb1" />



## Features

- **Holdings** — add, edit and delete stock positions with ticker, shares and average buy price
- **Live Prices** — fetches real-time prices from Yahoo Finance on demand
- **P&L Tracking** — shows profit/loss per holding in both value and percentage
- **Portfolio Summary** — total portfolio value, total cost, overall return at a glance
- **Allocation Pie Chart** — visual breakdown of how your money is distributed
- **Rebalancing Rules** — set min/max/target allocation % per ticker, get buy/trim suggestions automatically
- **Goals** — track monthly contribution targets and progress
- **Avatar** — personalise your dashboard with a profile image

## Architecture

```
Phone / Browser
      │
      ▼
Cloudflare Zero Trust  ←  Google login required
      │
      ▼
Cloudflare Worker  ←  reverse proxy + secret header injection
      │
      ▼
Google Cloud Run  ←  Flask app, validates secret header
      │
      ├──▶ Google Firestore    (holdings, rules, goals)
      └──▶ Google Cloud Storage  (avatar image, private)
```

## Design Decisions

**Why Google Cloud Run?**
I didn't want to pay for or manage a VM running 24/7 for a personal app I check occasionally. Cloud Run is serverless — the container spins up on demand and scales to zero when idle. For personal use, the free tier covers everything, so the running cost is effectively zero.

**Why Cloudflare Zero Trust instead of building a login page?**
This app is strictly for my own personal use. Building and maintaining my own authentication system just to protect a single-user app made no sense. Zero Trust lets me gate the entire app behind my existing Google account — no passwords to store, no sessions to manage, no auth code to write or secure.

**Why Cloudflare Workers instead of a simple CNAME?**
I first tried pointing a Cloudflare-proxied CNAME directly at Cloud Run. This caused an SSL handshake failure — Cloudflare's Full Strict mode expects a Cloudflare Origin Certificate on the backend, but Cloud Run presents Google's own certificate. Rather than downgrading SSL for my entire domain, I used a Cloudflare Worker as a reverse proxy. The Worker runs inside Cloudflare's own network, so SSL terminates cleanly at the edge, and the Worker makes a separate request to Cloud Run. This also lets me inject a secret header on every request, so Cloud Run rejects anything that doesn't come through the Worker.

**Why Google Firestore?**
No schema to define upfront, no database server to manage, and it fits naturally with the rest of the Google Cloud stack. For a small personal app with a handful of documents, Firestore's free tier is more than sufficient, and it requires zero ops overhead.

## What I Learned

- Deploying and managing containerised apps on Google Cloud Run
- Setting up Cloudflare Zero Trust for identity-aware access control
- Using Cloudflare Workers to solve real infrastructure problems (SSL conflicts, secret injection)
- Layering multiple security controls so no single bypass exposes the app
- Managing secrets properly via environment variables rather than hardcoding

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| Framework | Flask + Gunicorn |
| Database | Google Firestore |
| Storage | Google Cloud Storage |
| Hosting | Google Cloud Run |
| Build | Google Cloud Build |
| Proxy | Cloudflare Workers |
| Access | Cloudflare Zero Trust |
| Prices | Yahoo Finance API |

import yfinance as yf
from google.cloud import firestore
from google.cloud import storage
import urllib.request
import json
from datetime import datetime, timedelta

# ── Firestore client ──────────────────────────────────────────────────────────
db = firestore.Client(project='stock-personal-494502')

# ── Cloud Storage client ──────────────────────────────────────────────────────
storage_client = storage.Client(project='stock-personal-494502')
BUCKET_NAME    = 'stock-profile-origino'


# ── Holdings ──────────────────────────────────────────────────────────────────
def get_all_holdings():
    docs = db.collection('holdings').stream()
    return [{'id': d.id, **d.to_dict()} for d in docs]


def upsert_holding(ticker, company_name, shares, avg_cost):
    ticker = ticker.upper()
    price  = fetch_price(ticker) or 0
    db.collection('holdings').document(ticker).set({
        'ticker':        ticker,
        'company_name':  company_name,
        'shares':        shares,
        'avg_cost':      avg_cost,
        'current_price': price,
    })


def delete_holding(holding_id):
    db.collection('holdings').document(holding_id).delete()


# ── Rules ─────────────────────────────────────────────────────────────────────
def get_all_rules():
    docs = db.collection('rules').stream()
    return [{'id': d.id, **d.to_dict()} for d in docs]


def upsert_rule(ticker, min_pct, max_pct, target_pct):
    def to_float(v):
        if v is None or v == '':
            return None
        return float(v)

    ticker = ticker.upper()
    db.collection('rules').document(ticker).set({
        'ticker':     ticker,
        'min_pct':    to_float(min_pct),
        'max_pct':    to_float(max_pct),
        'target_pct': to_float(target_pct),
    })


def delete_rule(rule_id):
    db.collection('rules').document(rule_id).delete()


# ── Goals ─────────────────────────────────────────────────────────────────────
def get_goals():
    doc = db.collection('goals').document('main').get()
    if doc.exists:
        return doc.to_dict()
    # default goals if not set yet
    defaults = {
        'portfolio_target':            50000,
        'monthly_contribution_target': 500,
        'monthly_contributed':         0,
    }
    db.collection('goals').document('main').set(defaults)
    return defaults


def update_goals(portfolio_target, monthly_target, monthly_contributed):
    db.collection('goals').document('main').set({
        'portfolio_target':            portfolio_target,
        'monthly_contribution_target': monthly_target,
        'monthly_contributed':         monthly_contributed,
    })


# ── Price fetching ────────────────────────────────────────────────────────────

def fetch_price(ticker: str):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=1d"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        price = data['chart']['result'][0]['meta']['regularMarketPrice']
        return round(price, 2)
    except Exception as e:
        print(f"[fetch_price] {ticker}: {e}")
        return None


def refresh_all_prices():
    import time
    holdings = get_all_holdings()
    for h in holdings:
        price = fetch_price(h['ticker'])
        if price is not None:
            db.collection('holdings').document(h['ticker']).update({
                'current_price': price
            })
        time.sleep(0.5)


# ── Avatar (Cloud Storage) ────────────────────────────────────────────────────
def upload_avatar(file_stream, extension):
    bucket = storage_client.bucket(BUCKET_NAME)
    for ext in ['png', 'jpg', 'jpeg', 'gif', 'webp']:
        blob = bucket.blob(f'avatar.{ext}')
        if blob.exists():
            blob.delete()

    blob = bucket.blob(f'avatar.{extension}')
    blob.upload_from_file(file_stream, content_type=f'image/{extension}')
    return f'/avatar/image'

def get_avatar_url():
    bucket = storage_client.bucket(BUCKET_NAME)
    for ext in ['png', 'jpg', 'jpeg', 'gif', 'webp']:
        blob = bucket.blob(f'avatar.{ext}')
        if blob.exists():
            return f'/avatar/image'
    return None


# ── Portfolio compute (unchanged) ─────────────────────────────────────────────
def compute_portfolio(holdings, rules):
    total_value  = sum(h['shares'] * h['current_price'] for h in holdings)
    total_cost   = sum(h['shares'] * h['avg_cost']      for h in holdings)
    total_pnl    = total_value - total_cost
    total_return = (total_pnl / total_cost * 100) if total_cost else 0

    enriched = []
    for h in holdings:
        value   = h['shares'] * h['current_price']
        cost    = h['shares'] * h['avg_cost']
        pnl     = value - cost
        pnl_pct = (pnl / cost * 100) if cost else 0
        alloc   = (value / total_value * 100) if total_value else 0
        enriched.append({**h, 'value':     round(value,   2),
                               'pnl':       round(pnl,     2),
                               'pnl_pct':   round(pnl_pct, 2),
                               'alloc_pct': round(alloc,   2)})

    suggestions = []
    rules_map   = {r['ticker']: r for r in rules}

    for h in enriched:
        rule = rules_map.get(h['ticker'])
        if not rule:
            continue

        actual  = h['alloc_pct']
        target  = rule['target_pct']
        max_pct = rule['max_pct']
        min_pct = rule['min_pct']

        if max_pct is not None and actual > max_pct:
            diff_val = round((actual - max_pct) / 100 * total_value, 0)
            suggestions.append({'ticker': h['ticker'], 'action': 'trim',
                                 'reason': f"over max {max_pct}% · now {actual}%",
                                 'amount': diff_val, 'severity': 'alert'})

        elif min_pct is not None and actual < min_pct:
            diff_val = round((min_pct - actual) / 100 * total_value, 0)
            suggestions.append({'ticker': h['ticker'], 'action': 'buy',
                                 'reason': f"below min {min_pct}% · now {actual}%",
                                 'amount': diff_val, 'severity': 'alert'})

        elif target is not None:
            deviation = actual - target
            tolerance = 0.5
            if abs(deviation) <= tolerance:
                suggestions.append({'ticker': h['ticker'], 'action': 'hold',
                                     'reason': f"target {target}% · now {actual}%",
                                     'amount': 0, 'severity': 'ok'})
            else:
                diff_val = round(abs(deviation) / 100 * total_value, 0)
                action   = 'trim' if deviation > 0 else 'buy'
                suggestions.append({'ticker': h['ticker'], 'action': action,
                                     'reason': f"target {target}% · now {actual}%",
                                     'amount': diff_val,
                                     'severity': 'alert' if action == 'trim' else 'warn'})
        else:
            suggestions.append({'ticker': h['ticker'], 'action': 'hold',
                                 'reason': 'within target range',
                                 'amount': 0, 'severity': 'ok'})

    gaining = sum(1 for h in enriched if h['pnl'] >= 0)
    losing  = len(enriched) - gaining

    return {
        'total_value':  round(total_value,  2),
        'total_cost':   round(total_cost,   2),
        'total_pnl':    round(total_pnl,    2),
        'total_return': round(total_return, 2),
        'gaining':      gaining,
        'losing':       losing,
        'holdings':     enriched,
        'suggestions':  suggestions,
    }
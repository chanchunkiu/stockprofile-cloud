from flask import Flask, render_template, request, redirect, url_for, jsonify
import database as db
import os

app = Flask(__name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

#avatar
@app.route('/avatar/image')
def avatar_image():
    import io
    bucket = db.storage_client.bucket(db.BUCKET_NAME)
    for ext in ['png', 'jpg', 'jpeg', 'gif', 'webp']:
        blob = bucket.blob(f'avatar.{ext}')
        if blob.exists():
            buf = io.BytesIO()
            blob.download_to_file(buf)
            buf.seek(0)
            return buf.read(), 200, {'Content-Type': f'image/{ext}'}
    return '', 404

# ── Dashboard ─────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    holdings   = db.get_all_holdings()
    rules      = db.get_all_rules()
    goals      = db.get_goals()
    portfolio  = db.compute_portfolio(holdings, rules)
    avatar_url = db.get_avatar_url()
    return render_template('stockprofile.html',
                           portfolio=portfolio,
                           rules=rules,
                           goals=goals,
                           avatar_url=avatar_url)

# ── Refresh ───────────────────────────────────────────────────────────────────
@app.route('/refresh')
def refresh():
    db.refresh_all_prices()
    return redirect(url_for('index'))

# ── Avatar ────────────────────────────────────────────────────────────────────
@app.route('/avatar/upload', methods=['POST'])
def avatar_upload():
    file = request.files.get('avatar')
    if not file or file.filename == '':
        return jsonify({'error': 'no file'}), 400

    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({'error': f'invalid file type. allowed: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

    url = db.upload_avatar(file.stream, ext)
    return jsonify({'url': url})

# ── Holdings ──────────────────────────────────────────────────────────────────
@app.route('/holdings/save', methods=['POST'])
def holding_save():
    db.upsert_holding(
        ticker       = request.form['ticker'].upper().strip(),
        company_name = request.form.get('company_name', '').strip(),
        shares       = float(request.form['shares']),
        avg_cost     = float(request.form['avg_cost']),
    )
    return redirect(url_for('index'))

@app.route('/holdings/delete/<holding_id>', methods=['POST'])
def holding_delete(holding_id):
    db.delete_holding(holding_id)
    return redirect(url_for('index'))

# ── Rules ─────────────────────────────────────────────────────────────────────
@app.route('/rules/save', methods=['POST'])
def rule_save():
    db.upsert_rule(
        ticker     = request.form['ticker'].upper().strip(),
        min_pct    = request.form.get('min_pct')    or None,
        max_pct    = request.form.get('max_pct')    or None,
        target_pct = request.form.get('target_pct') or None,
    )
    return redirect(url_for('index'))

@app.route('/rules/delete/<rule_id>', methods=['POST'])
def rule_delete(rule_id):
    db.delete_rule(rule_id)
    return redirect(url_for('index'))

# ── Goals ─────────────────────────────────────────────────────────────────────
@app.route('/goals/save', methods=['POST'])
def goals_save():
    db.update_goals(
        portfolio_target    = float(request.form['portfolio_target']),
        monthly_target      = float(request.form['monthly_contribution_target']),
        monthly_contributed = float(request.form['monthly_contributed']),
    )
    return redirect(url_for('index'))

# ── JSON API ──────────────────────────────────────────────────────────────────
@app.route('/api/holdings')
def api_holdings():
    holdings  = db.get_all_holdings()
    rules     = db.get_all_rules()
    portfolio = db.compute_portfolio(holdings, rules)
    return jsonify(portfolio)

#disasble the link to google cloud run
@app.before_request
def check_secret():
    if request.headers.get('X-Secret-Key') != os.environ.get('SECRET_KEY'):
        return 'Forbidden', 403

# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
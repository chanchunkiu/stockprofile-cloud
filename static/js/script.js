// ── Chart colours ────────────────────────────────────────────────────────────
const COLORS = ['#4c8ef7','#4caf82','#e0a84a','#9b6ef7','#e05a5a','#4ecdc4','#f76c8e','#a3e635'];

// ── Pie chart — built from real PORTFOLIO data ────────────────────────────────
(function buildChart() {
  const holdings = PORTFOLIO.holdings;
  if (!holdings || !holdings.length) return;

  const labels = holdings.map(h => h.ticker);
  const data   = holdings.map(h => h.alloc_pct);

  new Chart(document.getElementById('pie'), {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data,
        backgroundColor: COLORS,
        borderWidth: 0,
        hoverOffset: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: c => ` ${c.label}: ${c.parsed}%` } }
      },
      cutout: '70%'
    }
  });

  // Build legend dynamically
  const legend = document.getElementById('allocLegend');
  if (legend) {
    legend.innerHTML = holdings.map((h, i) => `
      <div class="alloc-row">
        <div class="alloc-left">
          <div class="alloc-dot" style="background:${COLORS[i % COLORS.length]}"></div>
          <span class="alloc-name">${h.ticker}</span>
        </div>
        <span class="alloc-pct">${h.alloc_pct}%</span>
      </div>
    `).join('');
  }
})();

// ── Value toggle ──────────────────────────────────────────────────────────────
// ── Value toggle ──────────────────────────────────────────────────────────────
let valuesHidden = false;

document.getElementById('toggleValues').addEventListener('click', function() {
  valuesHidden = !valuesHidden;
  this.textContent = valuesHidden ? '👁 show' : '👁 hide';

  // metric cards
  document.querySelectorAll('.metric-value, .metric-sub').forEach(el => {
    el.dataset.original = el.dataset.original || el.textContent;
    el.textContent = valuesHidden ? '***' : el.dataset.original;
  });

  // progress bar numbers
  document.querySelectorAll('.prog-row span:last-child').forEach(el => {
    el.dataset.original = el.dataset.original || el.textContent;
    el.textContent = valuesHidden ? '***' : el.dataset.original;
  });

  // progress hints
  document.querySelectorAll('.prog-hint').forEach(el => {
    el.dataset.original = el.dataset.original || el.textContent;
    el.textContent = valuesHidden ? '***' : el.dataset.original;
  });
});

// ── Timestamp ────────────────────────────────────────────────────────────────
document.getElementById('lastUpdated').textContent =
  'updated ' + new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

// ── Avatar upload ────────────────────────────────────────────────────────────
document.getElementById('avatarInput').addEventListener('change', function(e) {
  const file = e.target.files[0];
  if (!file) return;

  const form = new FormData();
  form.append('avatar', file);

  fetch('/avatar/upload', { method: 'POST', body: form })
    .then(r => r.json())
    .then(data => {
      if (data.url) {
        const img = document.getElementById('avatarImg');
        img.src = data.url + '?t=' + Date.now(); // bust cache
        img.style.display = 'block';
        document.getElementById('avatarInitials').style.display = 'none';
      } else {
        alert('Upload failed: ' + (data.error || 'unknown error'));
      }
    })
    .catch(() => alert('Upload failed — check server logs'));
});

// ── Modal helpers ─────────────────────────────────────────────────────────────
function openModal(id)  { document.getElementById(id).classList.add('open'); }
function closeModal(id) {
  document.getElementById(id).classList.remove('open');
  const base = id.replace('Modal', '');
  showForm(base);
}
function showForm(base) {
  document.getElementById(base + 'FormWrap').style.display    = '';
  document.getElementById(base + 'ConfirmWrap').style.display = 'none';
  document.getElementById(base + 'Preview').style.display     = 'none';
}
function showConfirm(base) {
  document.getElementById(base + 'FormWrap').style.display    = 'none';
  document.getElementById(base + 'ConfirmWrap').style.display = '';
  document.getElementById(base + 'Preview').style.display     = '';
}
function backToForm(base) { showForm(base); }

function buildPreview(containerId, fields) {
  document.getElementById(containerId).innerHTML = fields.map(([k, v]) => `
    <div class="modal-field">
      <span class="modal-key">${k}</span>
      <span class="modal-val">${v}</span>
    </div>
  `).join('');
}

// Close modal when clicking the dark overlay
document.querySelectorAll('.modal-overlay').forEach(el => {
  el.addEventListener('click', e => { if (e.target === el) closeModal(el.id); });
});

// ── Holding modal ─────────────────────────────────────────────────────────────
function openAddHolding() {
  document.getElementById('holdingModalTitle').textContent = 'Add position';
  document.getElementById('holdingForm').reset();
  showForm('holding');
  openModal('holdingModal');
}

function openEditHolding(h) {
  document.getElementById('holdingModalTitle').textContent = `Edit ${h.ticker}`;
  const f = document.getElementById('holdingForm');
  f.ticker.value       = h.ticker;
  f.company_name.value = h.company_name || '';
  f.shares.value       = h.shares;
  f.avg_cost.value     = h.avg_cost;
  showForm('holding');
  openModal('holdingModal');
}

function previewHolding() {
  const f = document.getElementById('holdingForm');
  if (!f.ticker.value || !f.shares.value || !f.avg_cost.value) {
    alert('Please fill in ticker, shares and avg cost');
    return;
  }
  buildPreview('holdingPreview', [
    ['ticker',   f.ticker.value.toUpperCase()],
    ['company',  f.company_name.value || '—'],
    ['shares',   f.shares.value],
    ['avg cost', '$' + parseFloat(f.avg_cost.value).toFixed(2)],
  ]);
  showConfirm('holding');
}

// ── Rule modal ────────────────────────────────────────────────────────────────
function openRuleModal() {
  document.getElementById('ruleModalTitle').textContent = 'Add allocation rule';
  document.getElementById('ruleForm').reset();
  document.getElementById('ruleId').value = '';
  document.querySelector('#ruleForm [name="ticker"]').removeAttribute('readonly');
  showForm('rule');
  openModal('ruleModal');
}

function openEditRule(r) {
  document.getElementById('ruleModalTitle').textContent = `Edit rule — ${r.ticker}`;
  const f = document.getElementById('ruleForm');
  f.reset();
  document.getElementById('ruleId').value = r.id;
  f.ticker.value     = r.ticker;
  f.target_pct.value = r.target_pct || '';
  f.max_pct.value    = r.max_pct    || '';
  f.min_pct.value    = r.min_pct    || '';
  // lock ticker when editing
  f.ticker.setAttribute('readonly', true);
  showForm('rule');
  openModal('ruleModal');
}

function previewRule() {
  const f = document.getElementById('ruleForm');
  if (!f.ticker.value) { alert('Please enter a ticker'); return; }
  const isEdit = !!document.getElementById('ruleId').value;
  buildPreview('rulePreview', [
    ['action',   isEdit ? 'update rule' : 'add rule'],
    ['ticker',   f.ticker.value.toUpperCase()],
    ['target %', f.target_pct.value || '—'],
    ['max %',    f.max_pct.value    || '—'],
    ['min %',    f.min_pct.value    || '—'],
  ]);
  showConfirm('rule');
}

// ── Goals modal ───────────────────────────────────────────────────────────────
function openGoalsModal() {
  showForm('goals');
  openModal('goalsModal');
}

function previewGoals() {
  const f = document.getElementById('goalsForm');
  buildPreview('goalsPreview', [
    ['portfolio target', '$' + parseFloat(f.portfolio_target.value).toLocaleString()],
    ['monthly target',   '$' + parseFloat(f.monthly_contribution_target.value).toLocaleString()],
    ['contributed',      '$' + parseFloat(f.monthly_contributed.value).toLocaleString()],
  ]);
  showConfirm('goals');
}

// ── Holdings sort ─────────────────────────────────────────────────────────────
let sortCol = null;
let sortDir = 1; // 1 = asc, -1 = desc

function sortHoldings(col) {
  const tbody = document.getElementById('holdingsTbody');
  if (!tbody) return;

  // Toggle direction if same column, else default asc (desc for numeric cols)
  if (sortCol === col) {
    sortDir *= -1;
  } else {
    sortDir = (col === 'ticker') ? 1 : -1; // numbers default desc, ticker default asc
  }
  sortCol = col;

  // Update header styles and icons
  document.querySelectorAll('th.sortable').forEach(th => {
    th.classList.remove('active');
    const icon = th.querySelector('.sort-icon');
    if (icon) icon.textContent = '↕';
  });
  const activeTh = document.querySelector(`th[data-col="${col}"]`);
  if (activeTh) {
    activeTh.classList.add('active');
    const icon = activeTh.querySelector('.sort-icon');
    if (icon) icon.textContent = sortDir === 1 ? '↑' : '↓';
  }

  // Sort rows
  const rows = Array.from(tbody.querySelectorAll('tr'));
  rows.sort((a, b) => {
    let aVal = a.dataset[col] || '';
    let bVal = b.dataset[col] || '';

    if (col === 'ticker') {
      return aVal.localeCompare(bVal) * sortDir;
    } else {
      return (parseFloat(aVal) - parseFloat(bVal)) * sortDir;
    }
  });

  rows.forEach(r => tbody.appendChild(r));
}

// Initialise sort icons to neutral state
document.querySelectorAll('th.sortable .sort-icon').forEach(el => {
  el.textContent = '↕';
});
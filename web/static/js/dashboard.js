// PySQL-Sync Frontend Engine (Decoupled SPA Architecture)

let charts = {};
let mapInstance = null;

// Dynamic API Base URL resolver
function getApiBaseUrl() {
  const urlParams = new URLSearchParams(window.location.search);
  const paramApi = urlParams.get('api');
  if (paramApi) {
    localStorage.setItem('pysql_api_url', paramApi.replace(/\/$/, ''));
  }

  const saved = localStorage.getItem('pysql_api_url');
  if (saved) return saved;

  // If frontend is served directly by FastAPI backend
  if (window.location.port === '8000') {
    return '';
  }

  // If running on Vercel / Netlify / Cloudflare (production cloud)
  if (window.location.hostname.includes('vercel.app') || window.location.hostname.includes('netlify.app')) {
    return 'https://retailytics-m48i.onrender.com';
  }

  // Default to local backend for local development
  return 'http://127.0.0.1:8000';
}

function getApiUrl(path) {
  const base = getApiBaseUrl();
  return base ? `${base}${path}` : path;
}

// API Config Modal
function openApiConfigModal() {
  const modal = document.getElementById('api-modal');
  const input = document.getElementById('backend-url-input');
  if (modal && input) {
    input.value = getApiBaseUrl() || window.location.origin;
    modal.style.display = 'flex';
  }
}

function closeApiConfigModal() {
  const modal = document.getElementById('api-modal');
  if (modal) modal.style.display = 'none';
}

function saveApiUrl() {
  const input = document.getElementById('backend-url-input');
  if (input) {
    let val = input.value.trim().replace(/\/$/, '');
    if (val) {
      localStorage.setItem('pysql_api_url', val);
      showToast(`Connected to API: ${val}`, 'success');
    }
    closeApiConfigModal();
    updateApiIndicator();
    loadAllData();
  }
}

function resetToDefaultApi() {
  localStorage.removeItem('pysql_api_url');
  closeApiConfigModal();
  updateApiIndicator();
  showToast('Reset API to default (http://127.0.0.1:8000)', 'info');
  loadAllData();
}

function updateApiIndicator() {
  const badge = document.getElementById('api-indicator-text');
  const base = getApiBaseUrl();
  if (badge) {
    if (!base || base.includes('127.0.0.1') || base.includes('localhost')) {
      badge.innerText = 'API: Local';
    } else {
      try {
        const url = new URL(base);
        badge.innerText = `API: ${url.hostname}`;
      } catch (e) {
        badge.innerText = 'API: Remote';
      }
    }
  }
}

let loadedTabs = new Set();

document.addEventListener('DOMContentLoaded', () => {
  initNavigation();
  updateApiIndicator();
  loadInitialData();
  setupQuerySelector();
  setupSqlStudio();
  setupEtlRunner();
  setupAiAssistant();
  setupPdfExport();
});

// Fast initial load (only overview essentials)
function loadInitialData() {
  loadSystemStatus();
  loadKPIs();
  loadAnalyticsOverview();
  loadedTabs.add('tab-overview');
}

// Complete refresh (clears tab cache)
function loadAllData() {
  loadedTabs.clear();
  loadSystemStatus();
  loadKPIs();
  loadAnalyticsOverview();
  loadedTabs.add('tab-overview');
}

// Smart Tab Navigation with On-Demand Lazy Loading
function initNavigation() {
  const navLinks = document.querySelectorAll('.nav-link');
  navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const targetTab = link.getAttribute('data-tab');
      
      navLinks.forEach(l => l.classList.remove('active'));
      link.classList.add('active');

      document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
      });

      const activeTabEl = document.getElementById(targetTab);
      if (activeTabEl) {
        activeTabEl.classList.add('active');
      }

      // Lazy load tab data on first visit
      if (targetTab === 'tab-geo') {
        setTimeout(initGeospatialMap, 150);
      } else if (targetTab === 'tab-ml' && !loadedTabs.has('tab-ml')) {
        loadedTabs.add('tab-ml');
        loadMLForecast();
        loadRFMSegments();
        loadMarketBasket();
        loadClvAndChurn();
      } else if (targetTab === 'tab-logistics' && !loadedTabs.has('tab-logistics')) {
        loadedTabs.add('tab-logistics');
        loadLogisticsDelay();
      }
    });
  });
}

// Toast Notifications
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = 'toast';
  
  const icon = type === 'success' ? '✅' : type === 'error' ? '❌' : type === 'warning' ? '⚠️' : 'ℹ️';
  toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// 1. System Status
async function loadSystemStatus() {
  try {
    const res = await fetch(getApiUrl('/api/status'));
    const data = await res.json();
    
    document.getElementById('db-status-badge').innerText = `${data.db_type} (${data.connected ? 'Online' : 'Offline'})`;
    document.getElementById('total-records-count').innerText = (data.total_records || 0).toLocaleString();
    
    const tblBody = document.getElementById('etl-stats-body');
    if (tblBody && data.tables) {
      tblBody.innerHTML = data.tables.map(t => `
        <tr>
          <td><strong>${t.table}</strong></td>
          <td style="text-align: right; color: #10b981; font-weight: 600;">${t.count.toLocaleString()}</td>
          <td style="text-align: right;"><span class="badge badge-champion">Indexed</span></td>
        </tr>
      `).join('');
    }
  } catch (err) {
    document.getElementById('db-status-badge').innerText = 'API Disconnected';
    console.error('Failed to fetch status:', err);
  }
}

// 2. Executive KPIs
async function loadKPIs() {
  try {
    const res = await fetch(getApiUrl('/api/kpis'));
    const data = await res.json();

    document.getElementById('kpi-revenue').innerText = `$${(data.total_revenue || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    document.getElementById('kpi-orders').innerText = (data.total_orders || 0).toLocaleString();
    document.getElementById('kpi-aov').innerText = `$${(data.avg_order_value || 0).toFixed(2)}`;
    document.getElementById('kpi-customers').innerText = (data.total_customers || 0).toLocaleString();
  } catch (err) {
    console.error('Failed to load KPIs:', err);
  }
}

// 3. Analytics Overview & Charts
async function loadAnalyticsOverview() {
  try {
    const res = await fetch(getApiUrl('/api/analytics/overview'));
    const data = await res.json();

    // Line Chart
    if (data.monthly_sales && data.monthly_sales.length > 0) {
      const labels = data.monthly_sales.map(d => `${d.sale_year}-${d.sale_month}`);
      const revData = data.monthly_sales.map(d => d.monthly_revenue);
      const cumData = data.monthly_sales.map(d => d.cumulative_revenue);

      renderLineChart('salesTrendChart', labels, [
        {
          label: 'Monthly Revenue ($)',
          data: revData,
          borderColor: '#6366f1',
          backgroundColor: 'rgba(99, 102, 241, 0.1)',
          fill: true,
          tension: 0.3
        },
        {
          label: 'Cumulative Revenue ($)',
          data: cumData,
          borderColor: '#06b6d4',
          borderDash: [5, 5],
          tension: 0.3
        }
      ]);
    }

    // Category Chart
    if (data.top_categories && data.top_categories.length > 0) {
      const catLabels = data.top_categories.map(c => c.category);
      const catSales = data.top_categories.map(c => c.total_sales);
      renderBarChart('categoryChart', catLabels, catSales, '#8b5cf6');
    }

    // State Chart
    if (data.state_distribution && data.state_distribution.length > 0) {
      const stateLabels = data.state_distribution.map(s => s.customer_state);
      const stateCounts = data.state_distribution.map(s => s.customer_count);
      renderBarChart('stateChart', stateLabels, stateCounts, '#06b6d4');
    }

    // YoY Table
    const yoyBody = document.getElementById('yoy-table-body');
    if (yoyBody && data.yoy_growth) {
      yoyBody.innerHTML = data.yoy_growth.map(y => {
        const growth = y.yoy_growth_percentage;
        const badge = growth ? (growth >= 0 ? `<span style="color: #10b981;">+${growth}% ↗</span>` : `<span style="color: #ef4444;">${growth}% ↘</span>`) : '<span style="color: #94a3b8;">Baseline</span>';
        return `
          <tr>
            <td><strong>${y.order_year}</strong></td>
            <td style="text-align: right;">$${Number(y.total_sales).toLocaleString()}</td>
            <td style="text-align: right;">${badge}</td>
          </tr>
        `;
      }).join('');
    }
  } catch (err) {
    console.error('Failed to load overview:', err);
  }
}

// Chart Helpers
function renderLineChart(canvasId, labels, datasets) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  if (charts[canvasId]) charts[canvasId].destroy();

  charts[canvasId] = new Chart(ctx, {
    type: 'line',
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { labels: { color: '#94a3b8' } } },
      scales: {
        x: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#94a3b8' } },
        y: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#94a3b8' } }
      }
    }
  });
}

function renderBarChart(canvasId, labels, data, color) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  if (charts[canvasId]) charts[canvasId].destroy();

  charts[canvasId] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Volume / Revenue',
        data,
        backgroundColor: color,
        borderRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false }, ticks: { color: '#94a3b8' } },
        y: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#94a3b8' } }
      }
    }
  });
}

// 4. AI Assistant (Schema-Aware RAG)
function setupAiAssistant() {
  const btn = document.getElementById('btn-ask-ai');
  const input = document.getElementById('ai-prompt-input');
  const container = document.getElementById('ai-response-container');
  const sqlEl = document.getElementById('ai-generated-sql');
  const insightsBox = document.getElementById('ai-insights-box');
  const tableEl = document.getElementById('ai-results-table');

  if (!btn || !input) return;

  const handleAsk = async () => {
    const prompt = input.value.trim();
    if (!prompt) {
      showToast('Please type a question for the AI Assistant', 'warning');
      return;
    }

    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Analyzing...';
    container.style.display = 'flex';
    sqlEl.innerText = 'Analyzing question and retrieving database schema...';
    insightsBox.innerText = 'Executing query and generating insights...';
    tableEl.innerHTML = '';

    try {
      const res = await fetch(getApiUrl('/api/ai/ask'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt })
      });
      const data = await res.json();

      if (data.status === 'success') {
        sqlEl.innerText = data.generated_sql;
        insightsBox.style.background = 'rgba(99, 102, 241, 0.1)';
        insightsBox.style.borderLeftColor = 'var(--primary)';
        insightsBox.innerHTML = `
          <strong>💡 AI Business Explanation:</strong> ${data.explanation}<br/>
          <span style="font-size:12px; color:#cbd5e1;">${(data.insights || []).join(' ')}</span>
        `;

        if (data.data && data.data.length > 0) {
          const cols = data.columns || Object.keys(data.data[0]);
          let headerHtml = `<thead><tr>${cols.map(c => `<th>${c.toUpperCase()}</th>`).join('')}</tr></thead>`;
          let rowsHtml = `<tbody>${data.data.map(row => `
            <tr>${cols.map(c => `<td>${row[c] !== null ? row[c] : 'N/A'}</td>`).join('')}</tr>
          `).join('')}</tbody>`;
          tableEl.innerHTML = headerHtml + rowsHtml;
        } else {
          tableEl.innerHTML = '<tr><td colspan="5" style="text-align:center;">No records found.</td></tr>';
        }
        showToast('AI Query answered successfully!', 'success');
      } else if (data.status === 'out_of_scope') {
        sqlEl.innerText = data.generated_sql || '-- Out of Scope';
        insightsBox.style.background = 'rgba(245, 158, 11, 0.12)';
        insightsBox.style.borderLeftColor = '#f59e0b';
        insightsBox.innerHTML = `
          <strong style="color:#fbbf24;">${data.explanation}</strong><br/>
          <div style="font-size:13px; color:#e2e8f0; margin-top:6px;">${(data.insights || []).map(i => `• ${i}`).join('<br/>')}</div>
        `;
        tableEl.innerHTML = '';
        showToast('Query is out of database scope', 'warning');
      } else if (data.status === 'no_data') {
        sqlEl.innerText = data.generated_sql || '-- No Data Found';
        insightsBox.style.background = 'rgba(56, 189, 248, 0.1)';
        insightsBox.style.borderLeftColor = '#38bdf8';
        insightsBox.innerHTML = `
          <strong style="color:#38bdf8;">${data.explanation}</strong><br/>
          <span style="font-size:12px; color:#94a3b8;">${(data.insights || []).join(' ')}</span>
        `;
        tableEl.innerHTML = '';
        showToast('No records matched this query', 'info');
      } else {
        sqlEl.innerText = 'Query Execution Failed';
        insightsBox.style.background = 'rgba(239, 68, 68, 0.1)';
        insightsBox.style.borderLeftColor = '#ef4444';
        insightsBox.innerText = data.message || 'An error occurred while answering.';
        tableEl.innerHTML = '';
      }
    } catch (err) {
      insightsBox.innerText = `Error connecting to API (${getApiBaseUrl()}): ${err.message}`;
    } finally {
      btn.disabled = false;
      btn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Ask AI';
    }
  };

  btn.addEventListener('click', handleAsk);
  input.addEventListener('keypress', (e) => { if (e.key === 'Enter') handleAsk(); });
}

// 5. Geospatial Leaflet Map
async function initGeospatialMap() {
  const mapEl = document.getElementById('brazil-map');
  if (!mapEl) return;

  if (mapInstance) {
    mapInstance.invalidateSize();
    return;
  }

  mapInstance = L.map('brazil-map').setView([-14.235, -51.925], 4);

  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 18
  }).addTo(mapInstance);

  try {
    const res = await fetch(getApiUrl('/api/geo/density'));
    const states = await res.json();

    states.forEach(st => {
      const radius = Math.max(Math.min(st.intensity * 28, 30), 8);
      const color = st.intensity > 0.4 ? '#ec4899' : st.intensity > 0.1 ? '#6366f1' : '#06b6d4';

      const circle = L.circleMarker([st.lat, st.lng], {
        radius: radius,
        fillColor: color,
        color: '#fff',
        weight: 1,
        opacity: 0.8,
        fillOpacity: 0.65
      }).addTo(mapInstance);

      circle.bindPopup(`
        <div style="font-family: 'Inter', sans-serif; color: #0f172a; padding: 4px;">
          <h4 style="margin: 0 0 4px 0; font-size: 14px; font-weight: 700;">${st.state_name} (${st.state})</h4>
          <div style="font-size: 12px;"><strong>Gross Revenue:</strong> $${st.revenue.toLocaleString()}</div>
          <div style="font-size: 12px;"><strong>Active Customers:</strong> ${st.customers.toLocaleString()}</div>
          <div style="font-size: 12px;"><strong>Orders:</strong> ${st.orders.toLocaleString()}</div>
        </div>
      `);
    });

    const routeRes = await fetch(getApiUrl('/api/geo/routes'));
    const routes = await routeRes.json();

    routes.forEach(r => {
      const latlngs = [
        [r.origin_lat, r.origin_lng],
        [r.destination_lat, r.destination_lng]
      ];
      const polyline = L.polyline(latlngs, {
        color: '#f59e0b',
        weight: 2,
        opacity: 0.6,
        dashArray: '5, 8'
      }).addTo(mapInstance);

      polyline.bindPopup(`
        <div style="font-family: 'Inter', sans-serif; color: #0f172a; padding: 4px;">
          <strong>Fulfillment Route:</strong> ${r.origin} ➔ ${r.destination}<br/>
          <strong>Volume:</strong> ${r.items_shipped.toLocaleString()} items<br/>
          <strong>Route Value:</strong> $${r.route_value.toLocaleString()}
        </div>
      `);
    });

  } catch (err) {
    console.error('Failed to load map data:', err);
  }
}

// 6. Logistics Delay Analysis
async function loadLogisticsDelay() {
  try {
    const res = await fetch(getApiUrl('/api/ml/delay'));
    const data = await res.json();
    if (data.status !== 'success') return;

    document.getElementById('logistics-ontime').innerText = `${data.on_time_rate_pct}%`;
    document.getElementById('logistics-avgdays').innerText = `${data.avg_delivery_days} days`;
    document.getElementById('logistics-delayrate').innerText = `${data.overall_delay_rate_pct}%`;

    const tblBody = document.getElementById('delay-states-body');
    if (tblBody && data.top_delayed_states) {
      tblBody.innerHTML = data.top_delayed_states.map(s => `
        <tr>
          <td><strong style="color:#f8fafc;">${s.customer_state}</strong></td>
          <td style="text-align:right;">${s.total.toLocaleString()}</td>
          <td style="text-align:right; color:#f87171;">${s.delayed.toLocaleString()}</td>
          <td style="text-align:right;">${s.avg_days}d</td>
          <td style="text-align:right; font-weight:700; color:${s.delay_pct > 15 ? '#ef4444' : '#f59e0b'};">${s.delay_pct}%</td>
        </tr>
      `).join('');
    }
  } catch (err) {
    console.error('Failed to load logistics:', err);
  }
}

// 7. CLV & Churn
async function loadClvAndChurn() {
  try {
    const res = await fetch(getApiUrl('/api/ml/clv'));
    const data = await res.json();
    if (data.status !== 'success') return;

    const container = document.getElementById('clv-kpi-container');
    if (container && data.churn_distribution) {
      const c = data.churn_distribution;
      container.innerHTML = `
        <div class="card kpi-card">
          <div class="kpi-top"><span class="kpi-label">Avg 12-Month CLV</span></div>
          <div class="kpi-value" style="color:#10b981;">$${data.avg_predicted_clv}</div>
          <div class="kpi-sub">Top 10% Threshold: $${data.high_value_clv_threshold}</div>
        </div>
        <div class="card kpi-card">
          <div class="kpi-top"><span class="kpi-label">Active / Low Churn Risk</span></div>
          <div class="kpi-value" style="color:#38bdf8;">${c.low_risk_active.pct}%</div>
          <div class="kpi-sub">${c.low_risk_active.count.toLocaleString()} customers (Avg CLV: $${c.low_risk_active.avg_clv})</div>
        </div>
        <div class="card kpi-card">
          <div class="kpi-top"><span class="kpi-label">At-Risk / Dormant Risk</span></div>
          <div class="kpi-value" style="color:#f87171;">${c.high_risk_dormant.pct}%</div>
          <div class="kpi-sub">${c.high_risk_dormant.count.toLocaleString()} customers</div>
        </div>
      `;
    }
  } catch (err) {
    console.error('Failed to load CLV:', err);
  }
}

// 8. Standard Queries Runner
function setupQuerySelector() {
  const btn = document.getElementById('btn-run-query');
  const selector = document.getElementById('query-select');
  if (!btn || !selector) return;

  btn.addEventListener('click', async () => {
    const qId = selector.value;
    const resultBox = document.getElementById('query-results-table');
    resultBox.innerHTML = '<tr><td colspan="5" style="text-align:center;">Executing SQL Query...</td></tr>';

    try {
      const res = await fetch(getApiUrl(`/api/analytics/query/${qId}`));
      const data = await res.json();

      if (data.result !== undefined) {
        resultBox.innerHTML = `<tr><td colspan="5" style="text-align:center; font-size:18px; color:#10b981;"><strong>${data.title}:</strong> ${JSON.stringify(data.result)}</td></tr>`;
        return;
      }

      if (data.data && data.data.length > 0) {
        const cols = data.columns || Object.keys(data.data[0]);
        let headerHtml = `<thead><tr>${cols.map(c => `<th>${c.replace(/_/g, ' ').toUpperCase()}</th>`).join('')}</tr></thead>`;
        let rowsHtml = `<tbody>${data.data.map(row => `
          <tr>${cols.map(c => `<td>${row[c] !== null ? row[c] : 'N/A'}</td>`).join('')}</tr>
        `).join('')}</tbody>`;

        resultBox.innerHTML = headerHtml + rowsHtml;
      } else {
        resultBox.innerHTML = '<tr><td colspan="5" style="text-align:center;">No records found.</td></tr>';
      }
    } catch (err) {
      resultBox.innerHTML = `<tr><td colspan="5" style="text-align:center; color:#ef4444;">Error running query: ${err.message}</td></tr>`;
    }
  });
}

// 9. SQL Studio
function setupSqlStudio() {
  const btn = document.getElementById('btn-execute-sql');
  const editor = document.getElementById('sql-input');
  const resultContainer = document.getElementById('sql-studio-result');
  if (!btn || !editor) return;

  btn.addEventListener('click', async () => {
    const query = editor.value.trim();
    if (!query) {
      showToast('Please write a SQL query to execute.', 'warning');
      return;
    }

    resultContainer.innerHTML = '<p style="color:#94a3b8;">Executing SQL Query...</p>';
    const startTime = performance.now();

    try {
      const res = await fetch(getApiUrl('/api/sql/run'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      });
      const data = await res.json();
      const elapsed = ((performance.now() - startTime) / 1000).toFixed(3);

      if (!res.ok) {
        resultContainer.innerHTML = `<div style="color:#ef4444; padding:12px; background:rgba(239,68,68,0.1); border-radius:8px;"><strong>Error:</strong> ${data.detail}</div>`;
        return;
      }

      showToast(`Query executed in ${elapsed}s (${data.row_count} rows)`, 'success');

      if (data.data.length === 0) {
        resultContainer.innerHTML = `<p style="color:#10b981;">Query returned 0 rows (${elapsed}s).</p>`;
        return;
      }

      let headerHtml = `<thead><tr>${data.columns.map(c => `<th>${c}</th>`).join('')}</tr></thead>`;
      let rowsHtml = `<tbody>${data.data.map(row => `
        <tr>${data.columns.map(c => `<td>${row[c] !== null ? row[c] : 'NULL'}</td>`).join('')}</tr>
      `).join('')}</tbody>`;

      resultContainer.innerHTML = `
        <div style="margin-bottom:8px; font-size:12px; color:#94a3b8;">Returned ${data.row_count} rows in ${elapsed}s</div>
        <div class="table-responsive"><table class="custom-table">${headerHtml}${rowsHtml}</table></div>
      `;
    } catch (err) {
      resultContainer.innerHTML = `<div style="color:#ef4444;">Request failed: ${err.message}</div>`;
    }
  });
}

// 10. ML RFM Segmentation
async function loadRFMSegments() {
  try {
    const res = await fetch(getApiUrl('/api/ml/rfm'));
    const data = await res.json();
    if (data.status !== 'success') return;

    const container = document.getElementById('rfm-cards-container');
    if (container && data.segments) {
      container.innerHTML = data.segments.map(seg => {
        let badgeClass = 'badge-potential';
        if (seg.segment.includes('Champions')) badgeClass = 'badge-champion';
        if (seg.segment.includes('Loyal')) badgeClass = 'badge-loyal';
        if (seg.segment.includes('At-Risk')) badgeClass = 'badge-risk';

        return `
          <div class="card" style="padding: 16px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
              <span class="badge ${badgeClass}">${seg.segment}</span>
              <strong style="color:#fff;">${seg.percentage}%</strong>
            </div>
            <div style="font-size: 20px; font-weight:700; color:#fff; margin-bottom:4px;">${seg.customer_count.toLocaleString()} customers</div>
            <div style="font-size:12px; color:#94a3b8;">Avg Spend: <span style="color:#10b981;">$${seg.avg_monetary_spend}</span> | Recency: ${seg.avg_recency_days}d</div>
          </div>
        `;
      }).join('');
    }
  } catch (err) {
    console.error('Failed to load RFM:', err);
  }
}

// 11. ML Sales Forecast
async function loadMLForecast() {
  try {
    const res = await fetch(getApiUrl('/api/ml/forecast'));
    const data = await res.json();
    if (data.status !== 'success') return;

    const histLabels = data.historical.map(h => h.month);
    const histSales = data.historical.map(h => h.actual_sales);

    const fLabels = data.forecast.map(f => f.month);
    const fPreds = data.forecast.map(f => f.predicted_sales);
    const fUpper = data.forecast.map(f => f.upper_bound);
    const fLower = data.forecast.map(f => f.lower_bound);

    const allLabels = [...histLabels, ...fLabels];
    const actualData = [...histSales, ...Array(fLabels.length).fill(null)];
    const predData = [...Array(histLabels.length - 1).fill(null), histSales[histSales.length - 1], ...fPreds];
    const upperData = [...Array(histLabels.length - 1).fill(null), histSales[histSales.length - 1], ...fUpper];
    const lowerData = [...Array(histLabels.length - 1).fill(null), histSales[histSales.length - 1], ...fLower];

    renderLineChart('forecastChart', allLabels, [
      {
        label: 'Historical Actual Sales ($)',
        data: actualData,
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        fill: true,
        tension: 0.2
      },
      {
        label: 'AI Forecasted Sales ($)',
        data: predData,
        borderColor: '#ec4899',
        borderDash: [6, 4],
        tension: 0.2
      },
      {
        label: 'Upper 95% Bound',
        data: upperData,
        borderColor: 'rgba(236, 72, 153, 0.3)',
        borderDash: [2, 2],
        pointRadius: 0
      },
      {
        label: 'Lower 95% Bound',
        data: lowerData,
        borderColor: 'rgba(236, 72, 153, 0.3)',
        borderDash: [2, 2],
        pointRadius: 0
      }
    ]);
  } catch (err) {
    console.error('Failed to load forecast:', err);
  }
}

// 12. Market Basket
async function loadMarketBasket() {
  try {
    const res = await fetch(getApiUrl('/api/ml/basket'));
    const data = await res.json();
    if (data.status !== 'success') return;

    const basketBody = document.getElementById('basket-table-body');
    if (basketBody && data.rules) {
      basketBody.innerHTML = data.rules.map(r => `
        <tr>
          <td><strong style="color:#6366f1;">${r.category_a}</strong></td>
          <td><strong style="color:#06b6d4;">${r.category_b}</strong></td>
          <td style="text-align:right; font-weight:600; color:#10b981;">${r.co_occurrence_count} orders</td>
          <td><span style="font-size:12px; color:#cbd5e1;">${r.recommendation}</span></td>
        </tr>
      `).join('');
    }
  } catch (err) {
    console.error('Failed to load market basket:', err);
  }
}

// 13. ETL Trigger with Background Poller
function setupEtlRunner() {
  const btn = document.getElementById('btn-run-etl');
  if (!btn) return;

  btn.addEventListener('click', async () => {
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Ingesting Data...';
    showToast('Starting high-speed batch ETL pipeline on server...', 'info');

    try {
      const res = await fetch(getApiUrl('/api/etl/run'), { method: 'POST' });
      const data = await res.json();

      if (res.ok) {
        showToast(data.message || 'Ingestion initiated. Syncing tables...', 'info');
      }

      // Poll system status every 3 seconds until tables populate (max 45s)
      let attempts = 0;
      const interval = setInterval(async () => {
        attempts++;
        try {
          const statusRes = await fetch(getApiUrl('/api/status'));
          const statusData = await statusRes.json();
          if (statusData.total_records > 10000 || attempts > 15) {
            clearInterval(interval);
            btn.disabled = false;
            btn.innerHTML = '<i class="fa-solid fa-bolt"></i> Run Ingestion';
            showToast(`Ingestion completed! ${statusData.total_records.toLocaleString()} records indexed.`, 'success');
            loadAllData();
          }
        } catch (e) {
          if (attempts > 15) {
            clearInterval(interval);
            btn.disabled = false;
            btn.innerHTML = '<i class="fa-solid fa-bolt"></i> Run Ingestion';
          }
        }
      }, 3000);

    } catch (err) {
      showToast(`ETL trigger notice: ${err.message}. Checking status...`, 'info');
      btn.disabled = false;
      btn.innerHTML = '<i class="fa-solid fa-bolt"></i> Run Ingestion';
      setTimeout(loadAllData, 5000);
    }
  });
}

// 14. Export PDF
function setupPdfExport() {
  const btn = document.getElementById('btn-export-pdf');
  if (btn) {
    btn.addEventListener('click', () => {
      window.open(getApiUrl('/api/export/pdf'), '_blank');
    });
  }
}

function downloadCsv(queryId) {
  window.open(getApiUrl(`/api/export/csv/${queryId}`), '_blank');
}

/* ── app.js — ClientIQ Frontend Logic ── */

// ── State ────────────────────────────────────────────────────
let currentMode = 'company';
let reportText  = '';
let progressPct = 0;

const SECTION_COUNT_COMPANY = 10;
const SECTION_COUNT_STARTUP = 10;

// ── Demo data ─────────────────────────────────────────────────
const DEMOS = {
  infosys: `Client Meeting - March 2025
Client: Infosys, global IT services company, website: infosys.com
They provide digital transformation, cloud services, data analytics
to Fortune 500 enterprises. Competitors: TCS, Wipro, HCL, Accenture.
Focus is on growing AI and cloud services division.`,

  zepto: `Meeting Notes - Client Onboarding
Client: Zepto, website: zeptonow.com
Mumbai-based quick commerce startup, groceries in 10 minutes.
Operates in Mumbai, Delhi, Bengaluru, Hyderabad.
Competitors: Blinkit, Swiggy Instamart, BigBasket.`,

  razorpay: `Business Meeting - Razorpay, URL: razorpay.com
B2B fintech: payment gateway, RazorpayX banking, Razorpay Capital lending.
Serves startups, SMEs, large enterprises in India.
Competitors: PayU, Cashfree, Stripe India, CCAvenue.`,

  textile: `I want to start an online textile business in India.
I plan to sell ethnic fabrics, sarees, and dress materials
directly to consumers through a website and Instagram.
My target customers are women aged 25-50 who love ethnic fashion.
I want to start small with a budget of around 2-3 lakhs.`,

  edtech: `I want to start an online tutoring platform for Indian students
in grades 8-12. Focus on CBSE and state board subjects,
especially Maths, Science, and English. I want to offer
live classes and recorded content. Target is Tier 2 and Tier 3 cities.`,

  food: `I want to launch a D2C brand selling organic, healthy snacks
and superfoods online in India. Products would include millet-based
snacks, organic dry fruits, and protein bars.
Target audience: health-conscious urban millennials.`
};

// ── Init ─────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const ta = document.getElementById('main-input');
  ta.addEventListener('input', () => {
    document.getElementById('char-count').textContent = `${ta.value.length} characters`;
  });
});

// ── Helpers ──────────────────────────────────────────────────
function scrollToApp() {
  document.getElementById('app').scrollIntoView({ behavior: 'smooth' });
}


function setMode(mode) {
  currentMode = mode;
  document.getElementById('tab-company').classList.toggle('active', mode === 'company');
  document.getElementById('tab-startup').classList.toggle('active', mode === 'startup');
  document.getElementById('demo-chips-company').classList.toggle('hidden', mode !== 'company');
  document.getElementById('demo-chips-startup').classList.toggle('hidden', mode !== 'startup');
  document.getElementById('input-label').textContent =
    mode === 'company'
      ? 'Meeting Transcript *'
      : 'Business Idea Description *';
  document.getElementById('main-input').placeholder =
    mode === 'company'
      ? 'Paste your client meeting transcript here...'
      : 'Describe your business idea in detail...';
}

function loadDemo(key) {
  const ta = document.getElementById('main-input');
  ta.value = DEMOS[key] || '';
  document.getElementById('char-count').textContent = `${ta.value.length} characters`;
  ta.focus();
}

function showCard(id) {
  ['config-section', 'progress-section', 'report-section'].forEach(s => {
    document.getElementById(s).classList.toggle('hidden', s !== id);
  });
}

function showTab(tab) {
  document.getElementById('tab-preview').classList.toggle('hidden', tab !== 'preview');
  document.getElementById('tab-raw').classList.toggle('hidden', tab !== 'raw');
  document.getElementById('rtab-preview').classList.toggle('active', tab === 'preview');
  document.getElementById('rtab-raw').classList.toggle('active', tab === 'raw');
}

function appendLog(text, isSpecial = false) {
  const box = document.getElementById('log-box');
  const line = document.createElement('span');
  line.className = 'log-line' + (isSpecial ? ' special' : '');
  line.textContent = text;
  box.appendChild(line);
  box.appendChild(document.createElement('br'));
  box.scrollTop = box.scrollHeight;
}

function setProgress(pct, statusText) {
  document.getElementById('progress-bar').style.width = pct + '%';
  if (statusText) document.getElementById('progress-status').textContent = statusText;
}

function buildMetaChips(meta, mode) {
  const el = document.getElementById('report-meta');
  el.innerHTML = '';
  const fields = mode === 'company'
    ? { Company: meta.company_name, Industry: meta.industry, Website: meta.website_url }
    : { Idea: meta.business_idea, Industry: meta.industry, Market: meta.target_market, Geography: meta.geography };
  Object.entries(fields).forEach(([k, v]) => {
    if (!v) return;
    const chip = document.createElement('div');
    chip.className = 'meta-chip';
    chip.innerHTML = `<strong>${k}:</strong> ${v}`;
    el.appendChild(chip);
  });
}

// ── Simple Markdown → HTML ────────────────────────────────────
function mdToHtml(md) {
  return md
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/^# (.+)$/gm,   '<h1>$1</h1>')
    .replace(/^## (.+)$/gm,  '<h2>$1</h2>')
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g,   '<em>$1</em>')
    .replace(/`(.+?)`/g,     '<code>$1</code>')
    .replace(/^---$/gm,      '<hr/>')
    .replace(/^&gt; (.+)$/gm,'<blockquote>$1</blockquote>')
    .replace(/^\* (.+)$/gm,  '<li>$1</li>')
    .replace(/^- (.+)$/gm,   '<li>$1</li>')
    .replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')
    .replace(/\n{2,}/g, '</p><p>')
    .replace(/^(?!<[hul]|<hr|<block)(.+)/gm, '<p>$1</p>');
}

// ── Start Research ────────────────────────────────────────────
async function startResearch() {
  const input  = document.getElementById('main-input').value.trim();

  if (!input)  { alert('Please enter the transcript or business idea.'); return; }

  const btn = document.getElementById('run-btn');
  btn.disabled = true;
  document.getElementById('run-btn-label').textContent = 'Starting...';

  // Start job
  let jobId;
  try {
    const res = await fetch('/api/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode: currentMode, input })
    });
    const data = await res.json();
    if (!res.ok) { alert(data.error || 'Failed to start.'); btn.disabled = false; return; }
    jobId = data.job_id;
  } catch(e) {
    alert('Could not reach server. Is app.py running?');
    btn.disabled = false;
    document.getElementById('run-btn-label').textContent = 'Start Research';
    return;
  }

  // Switch to progress view
  showCard('progress-section');
  document.getElementById('log-box').innerHTML = '';
  setProgress(5, 'Connected to agent...');
  progressPct = 5;

  // SSE stream
  const evtSrc = new EventSource(`/api/stream/${jobId}`);
  let logCount = 0;
  const total = currentMode === 'company' ? SECTION_COUNT_COMPANY : SECTION_COUNT_STARTUP;

  evtSrc.onmessage = (e) => {
    const msg = JSON.parse(e.data);

    if (msg.event === 'log') {
      const text = msg.data.text;
      const isSpecial = text.includes('Researching:') || text.includes('Final Answer') || text.includes('✓');
      appendLog(text, isSpecial);
      logCount++;
      // Estimate progress from log density
      const est = Math.min(90, 5 + Math.round((logCount / (total * 12)) * 85));
      if (est > progressPct) { progressPct = est; setProgress(progressPct); }
    }

    else if (msg.event === 'status') {
      setProgress(progressPct, msg.data.text);
      appendLog('→ ' + msg.data.text, true);
    }

    else if (msg.event === 'done') {
      evtSrc.close();
      setProgress(100, 'Report complete!');
      reportText = msg.data.report;
      const meta  = msg.data.meta;
      const mode  = msg.data.mode;

      document.getElementById('report-title').textContent =
        mode === 'company' ? `BI Report — ${meta.company_name || 'Company'}` : `Startup Report`;

      buildMetaChips(meta, mode);
      document.getElementById('report-rendered').innerHTML = mdToHtml(reportText);
      document.getElementById('report-raw').textContent = reportText;
      showTab('preview');
      setTimeout(() => showCard('report-section'), 600);

      btn.disabled = false;
      document.getElementById('run-btn-label').textContent = 'Start Research';
    }

    else if (msg.event === 'error') {
      evtSrc.close();
      appendLog('ERROR: ' + msg.data.text);
      setProgress(progressPct, 'Error occurred — check logs above.');
      btn.disabled = false;
      document.getElementById('run-btn-label').textContent = 'Start Research';
    }
  };

  evtSrc.onerror = () => {
    evtSrc.close();
    appendLog('Connection lost.');
    btn.disabled = false;
    document.getElementById('run-btn-label').textContent = 'Start Research';
  };
}

// ── Copy / Download ───────────────────────────────────────────
function copyReport() {
  if (!reportText) return;
  navigator.clipboard.writeText(reportText).then(() => {
    const btn = document.querySelector('.action-btn');
    btn.textContent = '✓ Copied!';
    setTimeout(() => { btn.textContent = '📋 Copy'; }, 2000);
  });
}

function downloadReport() {
  if (!reportText) return;
  const blob = new Blob([reportText], { type: 'text/markdown' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `ClientIQ_Report_${Date.now()}.md`;
  a.click();
  URL.revokeObjectURL(a.href);
}

function resetApp() {
  reportText = '';
  progressPct = 0;
  document.getElementById('log-box').innerHTML = '';
  document.getElementById('report-rendered').innerHTML = '';
  document.getElementById('report-raw').textContent = '';
  document.getElementById('main-input').value = '';
  document.getElementById('char-count').textContent = '0 characters';
  document.getElementById('run-btn').disabled = false;
  document.getElementById('run-btn-label').textContent = 'Start Research';
  showCard('config-section');
  document.getElementById('app').scrollIntoView({ behavior: 'smooth' });
}

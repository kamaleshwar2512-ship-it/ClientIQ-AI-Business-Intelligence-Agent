# ClientIQ — AI Business Intelligence Agent

> Autonomous AI agent that researches companies and startup ideas using **live web data** and generates consulting-grade reports in minutes.

---

## ✨ Features

- **Two Research Modes:**
  - 🏢 **Company BI Report** — paste a meeting transcript → get a full 10-section intelligence report
  - 🚀 **Startup Research** — describe a business idea → get market research, competitor analysis & GTM strategy
- **Web UI** — beautiful dark-mode frontend, no terminal needed
- **ReAct Architecture** — LLM reasons step-by-step, calls live tools, then answers
- **Live Web Tools** — DuckDuckGo search, website scraper, email/social extractor
- **Powered by Groq** — blazing-fast inference with LLaMA 3.3 70B

---

## 📁 Project Structure

```
ClientIQ/
├── app.py               # Flask web server (Web UI entry point)
├── main.py              # CLI entry point
├── .env                 # Your API key (never committed)
├── requirements.txt
│
├── core/                # Agent logic
│   ├── agent.py         # ReAct agent loop (Groq LLM)
│   ├── tools.py         # Web search, scraping, link extraction
│   ├── prompts.py       # All LLM prompt templates
│   └── report.py        # Report formatter & file saver
│
├── static/              # Web frontend
│   ├── index.html
│   ├── style.css
│   └── app.js
│
└── reports/             # Generated .md reports (auto-created)
```

---

## ⚙️ Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Get your Groq API Key (free)
- Visit: https://console.groq.com
- Sign up → Create API Key → Copy it

### 3. Add your key to `.env`
Create a `.env` file in the project root:
```
GROQ_API_KEY=gsk_your_key_here
```

---

## 🚀 Running the Web UI (recommended)

```bash
python app.py
```

Then open **http://localhost:5000** in your browser.

- Select a mode (Company BI or Startup Research)
- Load a demo or paste your own input
- Watch the agent research live → download the `.md` report

---

## 💻 Running via CLI

```bash
python main.py
```

Follow the prompts to select a mode, pick a demo or paste your transcript, and choose an output folder.

---

## 🧠 How It Works (ReAct Architecture)

```
Input (Transcript or Startup Idea)
       ↓
[Groq LLM] Extract structured info
       ↓
For each research section:
   ┌─ Thought: What do I need to find?
   ├─ Action:  web_search / scrape_website / extract_emails_and_links
   ├─ Observation: Tool returns real live data
   └─ Repeat (up to 8 steps) → Final Answer
       ↓
Assemble complete Markdown report
       ↓
Save to reports/ folder
```

---

## 📄 Report Sections

**Company BI Report (10 sections):**
1. Company Overview · 2. Brand Analysis · 3. Website Analysis · 4. Competitor Analysis
5. SEO & Digital Presence · 6. Target Audience · 7. SWOT Analysis
8. Market Opportunities · 9. Strategic Recommendations · 10. Final Assessment

**Startup Research Report (10 sections):**
1. Market Landscape · 2. Competitor Benchmarking · 3. Target Customer Profile
4. Business Model & Revenue · 5. Tech Stack & Tools · 6. Marketing Channels
7. Risk Analysis · 8. SWOT (New Entrant) · 9. Go-To-Market Strategy · 10. Viability Assessment

---

## 🛠️ Tech Stack

| Layer | Tech |
|---|---|
| LLM | `llama-3.3-70b-versatile` via Groq API |
| Web Search | DuckDuckGo (free, no API key) |
| Scraping | requests + BeautifulSoup4 |
| Backend | Flask + SSE (Server-Sent Events) |
| Frontend | Vanilla HTML / CSS / JavaScript |

---

## Example Input

```
Client Meeting — April 2025
Client: Razorpay, website: razorpay.com
B2B fintech providing payment gateway, banking, and lending to Indian businesses.
Competitors: PayU, Cashfree, Stripe India.
```

Paste this → agent researches live → full report in minutes.

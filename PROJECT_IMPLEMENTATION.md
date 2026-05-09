# ClientIQ — Project Implementation Document

> **Version:** 2.0.0  
> **Status:** ✅ Fully Implemented  
> **Last Updated:** May 2026  
> **Author:** Kamaleshwar  
> **Stack:** Python · Flask · Groq LLaMA 3.3 70B · ReAct Architecture · HTML/CSS/JS

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture Diagram](#2-architecture-diagram)
3. [Project Structure](#3-project-structure)
4. [Core Modules](#4-core-modules)
   - 4.1 [Agent Engine — `core/agent.py`](#41-agent-engine--coreagentpy)
   - 4.2 [Agent Tools — `core/tools.py`](#42-agent-tools--coretoolspy)
   - 4.3 [Prompt Templates — `core/prompts.py`](#43-prompt-templates--corepromptspy)
   - 4.4 [Report Builder — `core/report.py`](#44-report-builder--corereportpy)
   - 4.5 [Email Dispatcher — `core/email_sender.py`](#45-email-dispatcher--coreemail_senderpy)
5. [Web Application — `app.py`](#5-web-application--apppy)
6. [Frontend — `static/`](#6-frontend--static)
7. [Research Modes](#7-research-modes)
   - 7.1 [Company BI Report Mode](#71-company-bi-report-mode)
   - 7.2 [Startup Research Mode](#72-startup-research-mode)
8. [Report Output Formats](#8-report-output-formats)
9. [Email Delivery Feature](#9-email-delivery-feature)
10. [Environment Configuration](#10-environment-configuration)
11. [Dependencies](#11-dependencies)
12. [API Reference](#12-api-reference)
13. [Setup & Running](#13-setup--running)
14. [Known Limitations & Notes](#14-known-limitations--notes)

---

## 1. Project Overview

**ClientIQ** is an autonomous AI-powered Business Intelligence agent that conducts live internet research and generates professional consulting-grade reports.

### What it does:
- Accepts a **client meeting transcript** or **startup idea description** as input
- Autonomously browses the live web using a **ReAct (Reason + Act) loop**
- Researches 9–10 structured BI sections per report
- Generates reports in both **Markdown** and **styled Excel (.xlsx)** formats
- Delivers the report to any **email address** as an attachment
- Provides a **real-time streaming web UI** that shows agent activity live

### Technology Stack:
| Layer | Technology |
|---|---|
| LLM | Groq API · LLaMA 3.3 70B Versatile |
| Agent Pattern | ReAct (Reasoning + Acting) |
| Web Search | DuckDuckGo Search (`ddgs`) — free, no API key |
| Web Scraping | `requests` + `BeautifulSoup4` + `lxml` |
| Backend | Flask + Flask-CORS |
| Streaming | Server-Sent Events (SSE) |
| Excel Export | `openpyxl` |
| Email | `smtplib` + Gmail SMTP SSL |
| Frontend | Vanilla HTML + CSS + JavaScript |
| Fonts | Inter + JetBrains Mono (Google Fonts) |
| Terminal UI | `rich` (console panels, spinners, rules) |

---

## 2. Architecture Diagram

```
User Browser
    │
    │  HTTP POST /api/start  →  job_id returned
    │  GET  /api/stream/<job_id>  →  SSE event stream (live logs)
    │  POST /api/send-email  →  sends Excel via SMTP
    │  GET  /api/download-excel  →  streams .xlsx file
    ▼
Flask Web Server (app.py)
    │
    ├── Worker Thread (_run_agent)
    │       │
    │       ├── ClientIQAgent (core/agent.py)
    │       │       │
    │       │       ├── Groq LLM API  ←→  LLaMA 3.3 70B
    │       │       │
    │       │       └── ReAct Loop
    │       │               │
    │       │               ├── Tool: web_search       (DuckDuckGo)
    │       │               ├── Tool: scrape_website   (requests + BS4)
    │       │               └── Tool: extract_emails_and_links
    │       │
    │       ├── report.py  →  Markdown + Excel (.xlsx) output
    │       └── email_sender.py  →  Gmail SMTP delivery
    │
    └── SSE Queue  →  streams logs/status/done events to browser
```

---

## 3. Project Structure

```
ai_agent/
│
├── app.py                      # Flask web server — REST + SSE endpoints
├── requirements.txt            # Python dependencies
├── .env                        # API keys and email credentials (never committed)
├── .gitignore                  # Excludes .env, __pycache__, reports/
├── README.md                   # Basic setup guide
├── PROJECT_IMPLEMENTATION.md   # This file — full technical documentation
│
├── core/                       # Agent package
│   ├── __init__.py
│   ├── agent.py                # ReAct agent engine (ClientIQAgent class)
│   ├── tools.py                # Web search, scraping, link extraction tools
│   ├── prompts.py              # All LLM prompt templates
│   ├── report.py               # Markdown + Excel report builders
│   └── email_sender.py         # SMTP email dispatcher
│
├── static/                     # Frontend assets (served by Flask)
│   ├── index.html              # Single-page application
│   ├── style.css               # Dark-mode premium UI styles
│   └── app.js                  # Frontend logic, SSE handling, email UI
│
└── reports/                    # Auto-created — generated report files
    ├── BI_Report_*.md
    ├── BI_Report_*.xlsx
    ├── Startup_Report_*.md
    └── Startup_Report_*.xlsx
```

---

## 4. Core Modules

### 4.1 Agent Engine — `core/agent.py`

The central intelligence of the system. Implements the `ClientIQAgent` class.

**Class:** `ClientIQAgent`

| Method | Purpose |
|---|---|
| `__init__(api_key)` | Initialises Groq client with `llama-3.3-70b-versatile` |
| `_llm(messages, temperature, max_tokens)` | Single LLM API call, returns text |
| `_parse_react(text)` | Parses ReAct-formatted LLM output into `{thought, action, action_input, final_answer}` |
| `extract_company_info(transcript)` | Extracts structured company data from meeting transcript via LLM (JSON output) |
| `research_section(section_key, company_info)` | Runs full ReAct loop for one BI section, returns Final Answer |
| `generate_final_assessment(company_info)` | Generates executive summary from all collected research |
| `run(transcript)` | **Main BI pipeline**: extract → research 9 sections → assessment |
| `extract_startup_idea(user_input)` | Parses free-form startup description into structured JSON |
| `research_startup_section(section_key, idea)` | ReAct loop for one startup research section |
| `generate_startup_assessment(idea)` | Generates startup viability verdict |
| `run_startup(user_input)` | **Main startup pipeline**: parse → research 9 sections → verdict |

**ReAct Loop Configuration:**
- `MAX_REACT_STEPS = 8` — maximum tool calls per section
- Temperature: `0.3` for research, `0.4` for assessment, `0.1` for extraction
- Observation truncated at 3,000 characters to manage token limits
- 1-second rate-limit delay between sections
- Fallback: if max steps reached without Final Answer, LLM is explicitly prompted to conclude

---

### 4.2 Agent Tools — `core/tools.py`

Three callable tools registered in `TOOL_REGISTRY`, available to the ReAct agent.

#### Tool 1: `web_search(query, max_results=6)`
- Uses `ddgs` (DuckDuckGo Search) — **free, no API key required**
- Returns formatted list of: title, URL, snippet for each result
- Error-safe with try/except fallback

#### Tool 2: `scrape_website(url, max_chars=4000)`
- Fetches full webpage via `requests` with realistic browser User-Agent
- Strips: `<script>`, `<style>`, `<nav>`, `<footer>`, `<iframe>`, `<noscript>`, `<aside>`, `<form>`
- Extracts: page title, meta description, Open Graph tags, headings (H1–H3), body paragraphs
- Bonus: extracts CSS hex colour hints for brand analysis
- Handles: Timeout, HTTPError, generic exceptions gracefully

#### Tool 3: `extract_emails_and_links(url)`
- Extracts contact email addresses via regex
- Identifies social media profile links (LinkedIn, Twitter/X, Instagram, Facebook, YouTube, GitHub)
- Returns up to 15 key hyperlinks from the page

**Tool Registry Pattern:**
```python
TOOL_REGISTRY = {
    "web_search": { "fn": web_search, "description": "..." },
    "scrape_website": { "fn": scrape_website, "description": "..." },
    "extract_emails_and_links": { "fn": extract_emails_and_links, "description": "..." },
}
```
`run_tool(name, input_str)` dispatches to the correct function with error handling.

---

### 4.3 Prompt Templates — `core/prompts.py`

All LLM instructions are centralised here as string constants.

| Prompt | Purpose |
|---|---|
| `SYSTEM_PROMPT` | Defines ReAct format, agent persona (Business Analyst, SEO Auditor, etc.), tool descriptions |
| `EXTRACT_COMPANY_PROMPT` | Extracts company name, URL, industry, services from transcript → JSON |
| `RESEARCH_SECTIONS` | Dict of 9 BI section prompts (see §7.1) |
| `FINAL_ASSESSMENT_PROMPT` | Executive summary prompt — market position, digital maturity, brand, growth |
| `EXTRACT_STARTUP_IDEA_PROMPT` | Parses free-form startup description → structured JSON |
| `STARTUP_RESEARCH_SECTIONS` | Dict of 9 startup section prompts (see §7.2) |
| `STARTUP_FINAL_ASSESSMENT_PROMPT` | Startup viability verdict — market, competition, revenue, execution, verdict |

---

### 4.4 Report Builder — `core/report.py`

Handles all report generation and file saving in two formats.

#### Markdown Reports
| Function | Output |
|---|---|
| `build_report(company_info, sections)` | Returns full BI report as a Markdown string |
| `save_report(report, company_name, output_dir)` | Saves `.md` file, returns filepath |
| `build_startup_report(idea_info, sections)` | Returns full Startup report as Markdown string |
| `save_startup_report(report, business_idea, output_dir)` | Saves `.md` file, returns filepath |
| `display_report_summary(company_info, sections)` | Rich terminal summary with section status |
| `display_startup_summary(idea_info, sections)` | Rich terminal summary for startup reports |

#### Excel Reports (`.xlsx`)
| Function | Output |
|---|---|
| `save_report_excel(company_info, sections, output_dir)` | Saves styled `.xlsx` BI report, returns filepath |
| `save_startup_report_excel(idea_info, sections, output_dir)` | Saves styled `.xlsx` Startup report, returns filepath |

**Excel Styling (Dark Theme via `openpyxl`):**
- Title row: large purple font on dark navy background, merged across columns
- Subtitle: generation timestamp
- Metadata rows: bold labels + values on deep blue background with thin borders
- Section headers: purple font on `#0F3460` blue background
- Content rows: alternating dark body colours (`#1E1E3F` / `#252545`) with text wrap
- Column widths: A = 28, B = 100 (wide content column)
- Sheet tab: purple (`#7C3AED`)
- Row heights auto-estimated from content length (capped at 400px)

---

### 4.5 Email Dispatcher — `core/email_sender.py`

Sends the generated Excel report as an email attachment.

**Function:** `send_report_email(recipient, excel_path, report_title, subject)`

- Transport: `smtplib.SMTP_SSL` on port 465 (Gmail)
- Reads `EMAIL_SENDER` and `EMAIL_PASSWORD` from environment
- Attaches the `.xlsx` file using `MIMEBase` + `encoders.encode_base64`
- Email body: branded dark-mode HTML template matching the app's colour scheme
- Raises `EnvironmentError` if credentials are missing
- Raises `FileNotFoundError` if Excel file doesn't exist

> **Requires a Gmail App Password** (16-character code from Google Account settings). A regular Gmail password will fail with error 535.

---

## 5. Web Application — `app.py`

Flask server that exposes the REST + SSE API and serves the static frontend.

### Key Components

**SSE Queue System:**
- Each research job gets a unique `job_id = f"job_{timestamp_ms}"`
- A `queue.Queue` is created per job and stored in `_queues` dict
- Worker thread pushes events: `log`, `status`, `done`, `error`, `ping`
- SSE stream delivers events to browser in real time

**Console Capture (`CaptureConsole`):**
- Monkey-patches `rich.Console` to intercept all terminal output
- Strips ANSI escape codes
- Pushes captured text as `log` SSE events to the browser

### API Routes

| Method | Route | Description |
|---|---|---|
| `GET` | `/` | Serves `static/index.html` |
| `POST` | `/api/start` | Starts agent job, returns `{ job_id }` |
| `GET` | `/api/stream/<job_id>` | SSE stream for real-time logs |
| `POST` | `/api/send-email` | Sends Excel report via email |
| `GET` | `/api/download-excel?path=...` | Streams Excel file download |

**Security on `/api/download-excel`:** Path is validated via `os.path.abspath` to ensure it resolves within `./reports/`. Requests outside this directory return HTTP 403.

---

## 6. Frontend — `static/`

A single-page application (no framework, pure HTML/CSS/JS).

### `index.html` — Structure
- **Navbar:** Fixed top bar with ClientIQ branding
- **Hero Section:** Title, stats (9+ sections, 3 tools, ~5min), animated report preview widget, CTA button
- **Step 01 — Config Card:** Mode tabs (Company / Startup), demo preset chips, textarea input, Start Research button
- **Step 02 — Progress Card:** Progress bar, status text, live log box (streams SSE)
- **Step 03 — Report Card:** Preview/Raw tabs, meta chips, Copy/Download MD/Download Excel buttons, **Email section**

### `style.css` — Design System
- **Colour Tokens:** `--bg`, `--surface`, `--surface2`, `--border`, `--accent` (`#6366f1`), `--accent2` (`#8b5cf6`), `--cyan`, `--green`, `--yellow`, `--red`
- **Typography:** Inter (UI) + JetBrains Mono (code/logs)
- **Effects:** Glassmorphism cards, gradient text, animated hero float, progress bar glow, spinner
- **Email Section:** Gradient top-border strip, glassmorphism background, focus ring on input, gradient send button

### `app.js` — Logic

**State Variables:**
```javascript
let currentMode = 'company';   // 'company' | 'startup'
let reportText  = '';           // Markdown report content
let excelPath   = '';           // Server-side path to .xlsx
let reportTitle = '';           // Report title for email subject
let progressPct = 0;            // Progress bar percentage
```

**Key Functions:**
| Function | Purpose |
|---|---|
| `startResearch()` | POST to `/api/start`, open SSE stream, update UI |
| `downloadReport('md')` | Client-side Blob download of Markdown |
| `downloadReport('xlsx')` | Triggers `/api/download-excel` server download |
| `sendEmail()` | POST to `/api/send-email`, handles loading/success/error states |
| `showEmailStatus(text, type)` | Updates email status div with class `success`/`error`/`loading` |
| `mdToHtml(md)` | Lightweight Markdown-to-HTML renderer (regex-based) |
| `resetApp()` | Clears all state, resets UI to config step |

**SSE Event Handling:**
| Event | Action |
|---|---|
| `log` | Appends to log box; special colour if contains `Researching:`, `Final Answer`, `✓` |
| `status` | Updates progress status text |
| `done` | Captures `report`, `excel_path`, `meta`, `mode`; renders report; shows report card |
| `error` | Shows error in log, re-enables run button |
| `ping` | Keepalive — no UI action |

---

## 7. Research Modes

### 7.1 Company BI Report Mode

**Input:** Client meeting transcript (paste from CRM, notes, etc.)

**Pipeline:**
1. LLM extracts: `company_name`, `website_url`, `industry`, `services`
2. ReAct researches 9 sections sequentially

**9 BI Sections:**
| # | Section | What's Researched |
|---|---|---|
| 1 | Company Overview | Founding, size, HQ, revenue, business model, geographic presence |
| 2 | Brand Analysis | Colours, typography, tone, taglines, customer sentiment |
| 3 | Website Analysis | UX/UI quality, CTAs, content depth, SEO signals, tech stack |
| 4 | Competitor Analysis | Top 4–5 competitors: strengths, weaknesses, positioning |
| 5 | SEO & Digital Presence | Keywords, blog activity, social profiles, ad maturity, reviews |
| 6 | Target Audience | Buyer personas, pain points, segments, verticals, geographies |
| 7 | SWOT Analysis | Evidence-based Strengths, Weaknesses, Opportunities, Threats |
| 8 | Market Opportunities | Underserved segments, geographic gaps, adjacent products, trends |
| 9 | Strategic Recommendations | 5–7 specific actionable improvements across marketing, SEO, brand, product |
| 10 | Final Assessment | Executive summary — market position, digital maturity, growth potential |

---

### 7.2 Startup Research Mode

**Input:** Free-form business idea description

**Pipeline:**
1. LLM extracts: `business_idea`, `industry`, `target_market`, `geography`, `business_model`, `unique_angle`, `budget_hint`
2. ReAct researches 9 sections sequentially

**9 Startup Sections:**
| # | Section | What's Researched |
|---|---|---|
| 1 | Market Landscape | TAM/SAM/SOM, growth rate, key players, Indian vs global, regulatory environment |
| 2 | Competitor Benchmarking | Top 5 competitors: offerings, pricing, strengths, weaknesses, target customer |
| 3 | Target Customer Profile | Demographics, pain points, buying behavior, discovery channels, social platforms |
| 4 | Business Model & Revenue | Monetisation models, pricing benchmarks, CAC/LTV, unit economics |
| 5 | Tech Stack & Tools | Platforms, integrations, MVP options, hosting, monthly tech cost |
| 6 | Marketing Channels | Digital channels, SEO keywords, paid ads, influencers, content strategy, CPC |
| 7 | Risk Analysis | Market, competitive, operational, regulatory, financial, technology risks + mitigations |
| 8 | SWOT (New Entrant) | SWOT from the perspective of entering as a startup |
| 9 | Go-To-Market Strategy | 3-phase GTM plan (Launch / Growth / Scale), KPIs, pricing strategy |
| 10 | Startup Viability Assessment | Verdict on market viability, feasibility, revenue potential, execution complexity |

---

## 8. Report Output Formats

### Markdown (`.md`)
- Professional heading hierarchy (H1 title, H2 sections)
- Metadata block (company, date, generated by)
- 10 sections with `---` dividers
- Saved to `./reports/BI_Report_<CompanyName>_<timestamp>.md`
- Viewable in the UI with Preview (rendered) and Raw tabs
- Downloadable as a file from the browser

### Excel (`.xlsx`)
- Dark-themed styled spreadsheet using `openpyxl`
- Two-column layout: Label column (A) + Content column (B)
- Sections styled with colour-coded headers and alternating body rows
- Metadata header block with company/idea details
- Saved to `./reports/BI_Report_<CompanyName>_<timestamp>.xlsx`
- Downloadable via the "📊 Download Excel" button
- Sent as email attachment via the email delivery feature

---

## 9. Email Delivery Feature

After a report is generated, users can send it to any email address directly from the UI.

### User Flow:
1. Report generation completes → Report card appears
2. User enters an email address in the "Send Report to Email" panel
3. Clicks "📨 Send Report"
4. UI shows `⏳ Sending...` with loading state
5. Server sends the `.xlsx` via Gmail SMTP
6. UI shows `✅ Report sent to email@example.com successfully!`

### Backend Flow (`POST /api/send-email`):
1. Validates recipient email and `excel_path` are present
2. Checks `excel_path` exists on disk
3. Calls `send_report_email()` from `core/email_sender.py`
4. Returns `{ success: true, message: "..." }` or `{ error: "..." }`

### Configuration Required (`.env`):
```env
EMAIL_SENDER=yourapp@gmail.com
EMAIL_PASSWORD=abcdefghijklmnop   # 16-char Gmail App Password (NOT real password)
```

### Gmail App Password Setup:
1. Enable 2-Step Verification: https://myaccount.google.com/security
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Paste the 16-character code (no spaces) as `EMAIL_PASSWORD`

---

## 10. Environment Configuration

File: `.env` (in project root — **never commit to Git**)

```env
# Groq LLM API Key (required)
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx

# Gmail credentials for email delivery (required for email feature)
EMAIL_SENDER=yourapp@gmail.com
EMAIL_PASSWORD=xxxxxxxxxxxxxxxx    # Gmail App Password, NOT your real password
```

`.gitignore` excludes `.env` to prevent credential leaks.

---

## 11. Dependencies

**`requirements.txt`:**
```
groq               # Groq SDK for LLaMA API
requests           # HTTP requests for web scraping
beautifulsoup4     # HTML parsing
ddgs               # DuckDuckGo Search (free, no key)
rich               # Terminal UI (panels, spinners, colours)
lxml               # Fast HTML parser for BeautifulSoup
flask              # Web framework
flask-cors         # CORS headers for API
python-dotenv      # Load .env into os.environ
openpyxl           # Excel (.xlsx) report generation
```

All standard library modules used (`smtplib`, `email`, `queue`, `threading`, `re`, `json`, `os`, `time`, `io`) require no installation.

---

## 12. API Reference

### `POST /api/start`
**Request:**
```json
{ "mode": "company", "input": "Meeting transcript text..." }
```
**Response:**
```json
{ "job_id": "job_1778306765837" }
```

### `GET /api/stream/<job_id>`
Server-Sent Events stream. Each event:
```json
{ "event": "log",    "data": { "text": "→ ReAct step 3/8" } }
{ "event": "status", "data": { "text": "Extracting company info..." } }
{ "event": "done",   "data": { "report": "# BUSINESS...", "excel_path": "./reports/BI_Report_...xlsx", "meta": {...}, "mode": "company" } }
{ "event": "error",  "data": { "text": "Error message" } }
```

### `POST /api/send-email`
**Request:**
```json
{ "email": "user@example.com", "excel_path": "./reports/BI_Report_X.xlsx", "report_title": "BI Report — Infosys" }
```
**Response (success):**
```json
{ "success": true, "message": "Report sent to user@example.com successfully!" }
```
**Response (error):**
```json
{ "error": "EMAIL_SENDER and EMAIL_PASSWORD must be set in your .env file." }
```

### `GET /api/download-excel?path=<encoded_path>`
- Returns the `.xlsx` file as a download attachment
- MIME type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- Security: path must resolve inside `./reports/` directory (HTTP 403 otherwise)

---

## 13. Setup & Running

### Prerequisites
- Python 3.10+
- Groq API key (free at [console.groq.com](https://console.groq.com))
- Gmail account with App Password (for email feature)

### Installation
```bash
# 1. Clone / navigate to project
cd ai_agent

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
# Edit .env and fill in GROQ_API_KEY (and EMAIL_SENDER + EMAIL_PASSWORD for email)
```

### Running the Web App
```bash
python app.py
```
Open browser at: **http://localhost:5000**

---

## 14. Known Limitations & Notes

| Item | Detail |
|---|---|
| **Rate Limits** | Groq free tier has token-per-minute limits. Research may slow down on very long reports. The agent adds a 1-second delay between sections. |
| **DuckDuckGo** | DDGS may occasionally return no results for very specific queries. The agent handles this gracefully and retries with a different query. |
| **Web Scraping** | Some websites block scraping (Cloudflare, paywalls). The agent falls back to search snippets in such cases. |
| **Observation Truncation** | Tool outputs are truncated at 3,000 characters to manage context window size. Very large pages may lose detail. |
| **Email: Gmail Only** | The current SMTP implementation is configured for Gmail SSL (port 465). Other providers require changing the SMTP host/port in `email_sender.py`. |
| **Email: App Password Required** | Google's security policy blocks direct password authentication. A Gmail App Password is mandatory. |
| **Excel Dark Theme** | Dark-themed Excel files look best in Excel for Windows/Mac. Google Sheets may render colours differently. |
| **Concurrent Jobs** | Multiple simultaneous research jobs are supported via the threading + queue architecture. Each job is fully isolated. |
| **Reports Directory** | `./reports/` is auto-created on server start. Files accumulate over time and should be periodically cleaned. |

---

*— ClientIQ · AI Business Intelligence Agent · Built with Groq LLaMA 3.3 70B + ReAct Architecture*

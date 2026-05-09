# -*- coding: utf-8 -*-
"""
main.py -- ClientIQ Entry Point
Supports two modes:
  Mode A: Analyze an existing company (BI Report from meeting transcript)
  Mode B: Research a new business idea (Startup Research Report)
"""

import os
import sys

# Load .env so GROQ_API_KEY is available without manually exporting it
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.rule import Rule

from core.agent import ClientIQAgent
from core.report import (
    build_report, save_report, display_report_summary,
    build_startup_report, save_startup_report, display_startup_summary,
)

console = Console()

BANNER = """
  ============================================================
    ClientIQ  --  Business Intelligence Agent
    Two Modes: Analyze a Company | Research Your Business Idea
  ============================================================
"""


# ─────────────────────────────────────────────────────────────────
# Demo transcripts (Mode A)
# ─────────────────────────────────────────────────────────────────

DEMO_TRANSCRIPTS = {
    "1": {
        "label": "Infosys (IT Services)",
        "text": (
            "Client Meeting - March 2025\n"
            "Client: Infosys, global IT services company, website: infosys.com\n"
            "They provide digital transformation, cloud services, data analytics\n"
            "to Fortune 500 enterprises. Competitors: TCS, Wipro, HCL, Accenture.\n"
            "Focus is on growing AI and cloud services division.\n"
        )
    },
    "2": {
        "label": "Zepto (Quick Commerce)",
        "text": (
            "Meeting Notes - Client Onboarding\n"
            "Client: Zepto, website: zeptonow.com\n"
            "Mumbai-based quick commerce startup, groceries in 10 minutes.\n"
            "Operates in Mumbai, Delhi, Bengaluru, Hyderabad.\n"
            "Competitors: Blinkit, Swiggy Instamart, BigBasket.\n"
        )
    },
    "3": {
        "label": "Razorpay (Fintech)",
        "text": (
            "Business Meeting - Razorpay, URL: razorpay.com\n"
            "B2B fintech: payment gateway, RazorpayX banking, Razorpay Capital lending.\n"
            "Serves startups, SMEs, large enterprises in India.\n"
            "Competitors: PayU, Cashfree, Stripe India, CCAvenue.\n"
        )
    },
}


# ─────────────────────────────────────────────────────────────────
# Demo startup ideas (Mode B)
# ─────────────────────────────────────────────────────────────────

DEMO_STARTUP_IDEAS = {
    "1": {
        "label": "Online Textile / Fabric Business",
        "text": (
            "I want to start an online textile business in India. "
            "I plan to sell ethnic fabrics, sarees, and dress materials "
            "directly to consumers through a website and Instagram. "
            "My target customers are women aged 25-50 who love ethnic fashion. "
            "I want to start small with a budget of around 2-3 lakhs."
        )
    },
    "2": {
        "label": "Online Tutoring / EdTech Platform",
        "text": (
            "I want to start an online tutoring platform for Indian students "
            "in grades 8-12. Focus on CBSE and state board subjects, "
            "especially Maths, Science, and English. I want to offer "
            "live classes and recorded content. Target is Tier 2 and Tier 3 cities."
        )
    },
    "3": {
        "label": "Organic Food / Healthy Snacks D2C",
        "text": (
            "I want to launch a D2C brand selling organic, healthy snacks "
            "and superfoods online in India. Products would include millet-based "
            "snacks, organic dry fruits, and protein bars. "
            "Target audience: health-conscious urban millennials."
        )
    },
}


# ─────────────────────────────────────────────────────────────────
# Input helpers
# ─────────────────────────────────────────────────────────────────

def select_mode() -> str:
    """Ask user which mode they want to use."""
    console.print("\n[bold]What do you want to do?[/]\n")
    console.print("  [cyan]A[/] - Analyze an existing company")
    console.print("      (Paste a client meeting transcript -> get a BI Report)\n")
    console.print("  [cyan]B[/] - Research a new business idea")
    console.print("      (Describe a business you want to start -> get a Startup Report)\n")
    return Prompt.ask("[bold]Select mode[/]", choices=["A", "B", "a", "b"]).upper()


def get_transcript() -> str:
    """Mode A: Collect existing company meeting transcript."""
    console.print("\n[bold]Provide the client meeting transcript:[/]\n")
    console.print("  [cyan]1[/] - Demo: Infosys (IT Services)")
    console.print("  [cyan]2[/] - Demo: Zepto (Quick Commerce)")
    console.print("  [cyan]3[/] - Demo: Razorpay (Fintech)")
    console.print("  [cyan]4[/] - Type my own transcript")
    console.print("  [cyan]5[/] - Load from .txt file\n")

    choice = Prompt.ask("[bold]Select[/]", choices=["1","2","3","4","5"], default="1")

    if choice in DEMO_TRANSCRIPTS:
        demo = DEMO_TRANSCRIPTS[choice]
        console.print(f"\n[green]Using demo: {demo['label']}[/]")
        console.print(Panel(demo["text"].strip(), title="Transcript Preview", border_style="dim"))
        return demo["text"]

    elif choice == "4":
        console.print("\n[bold]Paste your transcript. Type END on a new line when done.[/]\n")
        lines = []
        while True:
            try:
                line = input()
                if line.strip().upper() == "END":
                    break
                lines.append(line)
            except EOFError:
                break
        text = "\n".join(lines).strip()
        return text if text else DEMO_TRANSCRIPTS["1"]["text"]

    elif choice == "5":
        path = Prompt.ask("[bold]File path[/]")
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            console.print(f"[red]Could not read file: {e}[/]")
            return DEMO_TRANSCRIPTS["1"]["text"]

    return DEMO_TRANSCRIPTS["1"]["text"]


def get_startup_idea() -> str:
    """Mode B: Collect new business idea description."""
    console.print("\n[bold]Describe your business idea:[/]\n")
    console.print("  [cyan]1[/] - Demo: Online Textile Business")
    console.print("  [cyan]2[/] - Demo: Online Tutoring / EdTech")
    console.print("  [cyan]3[/] - Demo: Organic Food / Healthy Snacks D2C")
    console.print("  [cyan]4[/] - Type my own idea\n")

    choice = Prompt.ask("[bold]Select[/]", choices=["1","2","3","4"], default="1")

    if choice in DEMO_STARTUP_IDEAS:
        demo = DEMO_STARTUP_IDEAS[choice]
        console.print(f"\n[green]Using demo: {demo['label']}[/]")
        console.print(Panel(demo["text"].strip(), title="Your Business Idea", border_style="dim"))
        return demo["text"]

    elif choice == "4":
        console.print(
            "\n[bold]Describe your business idea in as much detail as possible.[/]\n"
            "[dim]Include: what you want to sell, who your customers are,\n"
            "where you want to operate, your budget (optional), any unique angle.\n"
            "Type END on a new line when done.[/]\n"
        )
        lines = []
        while True:
            try:
                line = input()
                if line.strip().upper() == "END":
                    break
                lines.append(line)
            except EOFError:
                break
        text = "\n".join(lines).strip()
        return text if text else DEMO_STARTUP_IDEAS["1"]["text"]

    return DEMO_STARTUP_IDEAS["1"]["text"]


def get_api_key() -> str:
    key = os.environ.get("GROQ_API_KEY", "")
    if key:
        console.print("[green]GROQ_API_KEY found in environment.[/]")
        return key
    console.print(
        "[yellow]GROQ_API_KEY not set.[/]\n"
        "Get your free key at: https://console.groq.com\n"
    )
    return Prompt.ask("[bold]Enter your Groq API Key[/]", password=True).strip()


def get_output_dir() -> str:
    return Prompt.ask("[bold]Save report to directory[/]", default="./reports")


# ─────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────

def main():
    console.print(f"[bold cyan]{BANNER}[/]")
    console.print(Rule())

    api_key    = get_api_key()
    mode       = select_mode()
    output_dir = get_output_dir()

    console.print(Rule())
    agent = ClientIQAgent(api_key=api_key)

    # ── MODE A: Company BI Report ──────────────────────────────
    if mode == "A":
        transcript = get_transcript()
        console.print(
            "\n[bold]The agent will:[/]\n"
            "  1. Extract the company from your transcript\n"
            "  2. Browse the internet live for 9 BI sections\n"
            "  3. Output a complete Business Intelligence Report\n"
            "  [dim]Takes 3-8 minutes.[/]\n"
        )
        if not Confirm.ask("[bold green]Start?[/]", default=True):
            sys.exit(0)

        try:
            result = agent.run(transcript=transcript)
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted.[/]")
            sys.exit(1)
        except Exception as e:
            console.print(f"\n[red]Fatal error: {e}[/]")
            import traceback; traceback.print_exc()
            sys.exit(1)

        company_info = result["company_info"]
        sections     = result["sections"]

        console.print(Rule("[bold]Assembling Report[/]"))
        report_text = build_report(company_info, sections)
        report_path = save_report(
            report       = report_text,
            company_name = company_info.get("company_name", "Report"),
            output_dir   = output_dir,
        )
        display_report_summary(company_info, sections)
        console.print(f"\n[bold green]Report saved to:[/] [cyan]{report_path}[/]\n")

    # ── MODE B: Startup Research Report ───────────────────────
    elif mode == "B":
        idea_text = get_startup_idea()
        console.print(
            "\n[bold]The agent will:[/]\n"
            "  1. Parse your business idea\n"
            "  2. Research the market, competitors, customers, tech, risks\n"
            "  3. Build a Go-To-Market strategy and viability verdict\n"
            "  [dim]Takes 3-8 minutes.[/]\n"
        )
        if not Confirm.ask("[bold yellow]Start Startup Research?[/]", default=True):
            sys.exit(0)

        try:
            result = agent.run_startup(user_input=idea_text)
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted.[/]")
            sys.exit(1)
        except Exception as e:
            console.print(f"\n[red]Fatal error: {e}[/]")
            import traceback; traceback.print_exc()
            sys.exit(1)

        idea_info = result["idea_info"]
        sections  = result["sections"]

        console.print(Rule("[bold]Assembling Startup Report[/]"))
        report_text = build_startup_report(idea_info, sections)
        report_path = save_startup_report(
            report       = report_text,
            business_idea= idea_info.get("business_idea", "startup"),
            output_dir   = output_dir,
        )
        display_startup_summary(idea_info, sections)
        console.print(f"\n[bold green]Report saved to:[/] [cyan]{report_path}[/]\n")


if __name__ == "__main__":
    main()

"""
agent.py — Core ReAct Agent Engine for ClientIQ
Handles: company extraction, section-by-section research, ReAct loop
"""

import os
import re
import json
import time
from groq import Groq
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.spinner import Spinner
from rich.live import Live
from rich.rule import Rule

from .tools import get_tool_descriptions, run_tool
from .prompts import (
    SYSTEM_PROMPT,
    EXTRACT_COMPANY_PROMPT,
    RESEARCH_SECTIONS,
    FINAL_ASSESSMENT_PROMPT,
    EXTRACT_STARTUP_IDEA_PROMPT,
    STARTUP_RESEARCH_SECTIONS,
    STARTUP_FINAL_ASSESSMENT_PROMPT,
)

console = Console()

MAX_REACT_STEPS = 8          # Max tool calls per research section
GROQ_MODEL      = "llama-3.3-70b-versatile"


# ─────────────────────────────────────────────────────────
# ClientIQ Agent
# ─────────────────────────────────────────────────────────

class ClientIQAgent:
    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)
        self.model  = GROQ_MODEL
        self.research_results: dict = {}

    # ── LLM Call ──────────────────────────────────────────
    def _llm(self, messages: list, temperature: float = 0.3,
             max_tokens: int = 2048) -> str:
        """Single LLM call. Returns the assistant message text."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()

    # ── Parse ReAct response ───────────────────────────────
    def _parse_react(self, text: str) -> dict:
        """
        Parse the LLM's ReAct-formatted response.
        Returns dict with keys: thought, action, action_input, final_answer
        """
        result = {
            "thought": "",
            "action": None,
            "action_input": None,
            "final_answer": None,
        }

        # Extract Thought
        thought_match = re.search(r"Thought:\s*(.*?)(?=Action:|Final Answer:|$)",
                                   text, re.DOTALL | re.IGNORECASE)
        if thought_match:
            result["thought"] = thought_match.group(1).strip()

        # Extract Final Answer (takes priority if present)
        final_match = re.search(r"Final Answer:\s*(.*?)$", text,
                                 re.DOTALL | re.IGNORECASE)
        if final_match:
            result["final_answer"] = final_match.group(1).strip()
            return result

        # Extract Action
        action_match = re.search(r"Action:\s*(\w+)", text, re.IGNORECASE)
        if action_match:
            result["action"] = action_match.group(1).strip()

        # Extract Action Input
        input_match = re.search(r"Action Input:\s*(.*?)(?=Thought:|Observation:|Action:|Final Answer:|$)",
                                  text, re.DOTALL | re.IGNORECASE)
        if input_match:
            result["action_input"] = input_match.group(1).strip().strip('"').strip("'")

        return result

    # ── Step 1: Extract company from transcript ────────────
    def extract_company_info(self, transcript: str) -> dict:
        """Use Groq to extract structured company info from the transcript."""
        console.print(Rule("[bold cyan]Step 1: Extracting Company Information[/]"))

        prompt = EXTRACT_COMPANY_PROMPT.format(transcript=transcript)
        response = self._llm(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=512,
        )

        # Try to parse JSON
        try:
            # Extract JSON block if wrapped in markdown
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                info = json.loads(json_match.group())
            else:
                info = json.loads(response)
        except json.JSONDecodeError:
            # Fallback: parse manually
            console.print("[yellow]⚠ Could not parse JSON, falling back to text parse[/]")
            info = {
                "company_name": self._extract_field(response, "company_name"),
                "website_url":  self._extract_field(response, "website_url"),
                "industry":     self._extract_field(response, "industry"),
                "services":     self._extract_field(response, "services"),
                "other_details": "",
            }

        # Validate & clean
        if not info.get("company_name") or info["company_name"] == "...":
            info["company_name"] = "Unknown Company"
        if not info.get("website_url") or info["website_url"] in ["...", "unknown"]:
            info["website_url"] = f"https://www.{info['company_name'].lower().replace(' ', '')}.com"
        if not info.get("industry"):
            info["industry"] = "Unknown"
        if not info.get("services"):
            info["services"] = "Not specified"

        console.print(Panel(
            f"[bold]Company:[/] {info['company_name']}\n"
            f"[bold]Website:[/] {info['website_url']}\n"
            f"[bold]Industry:[/] {info['industry']}\n"
            f"[bold]Services:[/] {info['services']}",
            title="[green]✓ Company Identified[/]",
            border_style="green"
        ))
        return info

    def _extract_field(self, text: str, field: str) -> str:
        match = re.search(rf'"{field}"\s*:\s*"([^"]*)"', text)
        return match.group(1) if match else ""

    # ── Step 2: ReAct Research Loop for one section ────────
    def research_section(self, section_key: str, company_info: dict) -> str:
        """
        Run the ReAct loop for a single BI section.
        Returns the Final Answer string.
        """
        section = RESEARCH_SECTIONS[section_key]
        section_title = section["title"]

        console.print(Rule(f"[bold blue]Researching: {section_title}[/]"))

        # Build section instruction
        instruction = section["instruction"].format(
            company_name=company_info.get("company_name", ""),
            website_url=company_info.get("website_url", ""),
            industry=company_info.get("industry", ""),
            services=company_info.get("services", ""),
        )

        # Build system message with tool descriptions
        system_msg = SYSTEM_PROMPT.format(
            tool_descriptions=get_tool_descriptions()
        )

        # Message history for this section
        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": instruction},
        ]

        final_answer = None
        step = 0

        while step < MAX_REACT_STEPS:
            step += 1
            console.print(f"  [dim]→ ReAct step {step}/{MAX_REACT_STEPS}[/]")

            # LLM call
            try:
                llm_response = self._llm(messages, temperature=0.3, max_tokens=1500)
            except Exception as e:
                console.print(f"  [red]LLM error: {e}[/]")
                break

            # Parse response
            parsed = self._parse_react(llm_response)

            # Show thought
            if parsed["thought"]:
                console.print(f"  [italic cyan]Thought:[/] {parsed['thought'][:120]}...")

            # Check for Final Answer
            if parsed["final_answer"]:
                final_answer = parsed["final_answer"]
                console.print(f"  [green]✓ Final Answer obtained[/]")
                break

            # Execute tool
            if parsed["action"] and parsed["action_input"]:
                tool_name  = parsed["action"]
                tool_input = parsed["action_input"]

                console.print(f"  [yellow]⚙ Tool:[/] {tool_name}")
                console.print(f"  [yellow]  Input:[/] {tool_input[:80]}...")

                # Run tool with loading indicator
                with console.status(f"  [dim]Running {tool_name}...[/]", spinner="dots"):
                    observation = run_tool(tool_name, tool_input)
                    time.sleep(0.5)  # Polite delay

                # Truncate very long observations
                if len(observation) > 3000:
                    observation = observation[:3000] + "\n[... truncated ...]"

                console.print(f"  [dim]  → Got {len(observation)} chars[/]")

                # Add to conversation
                messages.append({"role": "assistant", "content": llm_response})
                messages.append({
                    "role": "user",
                    "content": f"Observation: {observation}\n\nContinue your research. "
                               f"If you have enough data, give your Final Answer."
                })

            else:
                # LLM didn't follow format — nudge it
                messages.append({"role": "assistant", "content": llm_response})
                messages.append({
                    "role": "user",
                    "content": (
                        "Please continue using the ReAct format. "
                        "Use a tool to gather more data, or give your Final Answer "
                        "if you have enough information."
                    )
                })

        # If loop ended without Final Answer, ask for it
        if not final_answer:
            console.print(f"  [yellow]⚠ Max steps reached — requesting final answer[/]")
            messages.append({
                "role": "user",
                "content": (
                    "You have reached the maximum research steps. "
                    "Based on everything you have found so far, provide your "
                    "Final Answer now. Be specific and evidence-based."
                )
            })
            try:
                llm_response = self._llm(messages, temperature=0.3, max_tokens=2000)
                parsed = self._parse_react(llm_response)
                final_answer = parsed["final_answer"] or llm_response
            except Exception as e:
                final_answer = f"Research incomplete due to error: {e}"

        return final_answer

    # ── Step 3: Generate Final Assessment ──────────────────
    def generate_final_assessment(self, company_info: dict) -> str:
        """Generate the executive summary using all research collected."""
        console.print(Rule("[bold magenta]Generating Final Executive Assessment[/]"))

        # Build a brief summary of all sections for context
        summary_parts = []
        for key, content in self.research_results.items():
            title = RESEARCH_SECTIONS.get(key, {}).get("title", key)
            snippet = content[:300] if content else "No data"
            summary_parts.append(f"[{title}]: {snippet}")
        research_summary = "\n".join(summary_parts)

        prompt = FINAL_ASSESSMENT_PROMPT.format(
            company_name=company_info["company_name"],
            research_summary=research_summary
        )

        try:
            assessment = self._llm(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=600,
            )
        except Exception as e:
            assessment = f"Assessment generation failed: {e}"

        return assessment

    # ── Main Run Pipeline ──────────────────────────────────
    def run(self, transcript: str) -> dict:
        """
        Full pipeline:
        1. Extract company from transcript
        2. Research each BI section
        3. Generate final assessment
        Returns dict with company_info and all section results.
        """
        console.print(Panel(
            "[bold white]ClientIQ — Business Intelligence Agent[/]\n"
            "[dim]Autonomous Research • Live Web Data • Consulting-Grade Reports[/]",
            border_style="cyan",
            padding=(1, 4)
        ))

        # Step 1: Extract company
        company_info = self.extract_company_info(transcript)

        # Step 2: Research each section
        for section_key in RESEARCH_SECTIONS:
            try:
                result = self.research_section(section_key, company_info)
                self.research_results[section_key] = result
            except Exception as e:
                console.print(f"  [red]Section '{section_key}' failed: {e}[/]")
                self.research_results[section_key] = f"Research failed: {str(e)}"
            time.sleep(1)  # Avoid rate limiting

        # Step 3: Final assessment
        self.research_results["final_assessment"] = self.generate_final_assessment(
            company_info
        )

        return {
            "company_info": company_info,
            "sections": self.research_results,
        }


    # ═══════════════════════════════════════════════════════
    # STARTUP RESEARCH MODE
    # ═══════════════════════════════════════════════════════

    def extract_startup_idea(self, user_input: str) -> dict:
        """
        Use Groq to parse a free-form business idea description
        into structured fields for the startup research pipeline.
        """
        console.print(Rule("[bold cyan]Step 1: Parsing Your Business Idea[/]"))

        prompt = EXTRACT_STARTUP_IDEA_PROMPT.format(user_input=user_input)
        response = self._llm(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=512,
        )

        # Parse JSON
        try:
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            idea = json.loads(json_match.group()) if json_match else json.loads(response)
        except (json.JSONDecodeError, AttributeError):
            console.print("[yellow]Warning: Could not parse JSON cleanly, using defaults.[/]")
            idea = {
                "business_idea": user_input[:200],
                "industry": "E-commerce / Online Retail",
                "target_market": "General consumers",
                "geography": "India",
                "business_model": "Online / D2C",
                "unique_angle": "Not specified",
                "budget_hint": "Not specified",
            }

        # Fill missing keys with sensible defaults
        defaults = {
            "business_idea": user_input[:200],
            "industry": "Online Business",
            "target_market": "General consumers",
            "geography": "India",
            "business_model": "Online",
            "unique_angle": "Not specified",
            "budget_hint": "Not specified",
        }
        for k, v in defaults.items():
            if not idea.get(k) or idea[k] in ["", "..."]:
                idea[k] = v

        console.print(Panel(
            f"[bold]Business Idea:[/] {idea['business_idea']}\n"
            f"[bold]Industry:[/]     {idea['industry']}\n"
            f"[bold]Target Market:[/]{idea['target_market']}\n"
            f"[bold]Geography:[/]    {idea['geography']}\n"
            f"[bold]Model:[/]        {idea['business_model']}",
            title="[green]Business Idea Understood[/]",
            border_style="green"
        ))
        return idea

    def research_startup_section(self, section_key: str, idea: dict) -> str:
        """
        Run the ReAct loop for a single startup research section.
        Uses STARTUP_RESEARCH_SECTIONS prompts.
        """
        section       = STARTUP_RESEARCH_SECTIONS[section_key]
        section_title = section["title"]
        console.print(Rule(f"[bold blue]Researching: {section_title}[/]"))

        instruction = section["instruction"].format(
            business_idea = idea.get("business_idea", ""),
            industry      = idea.get("industry", ""),
            target_market = idea.get("target_market", ""),
            geography     = idea.get("geography", ""),
            business_model= idea.get("business_model", ""),
            unique_angle  = idea.get("unique_angle", ""),
            budget_hint   = idea.get("budget_hint", ""),
        )

        system_msg = SYSTEM_PROMPT.format(tool_descriptions=get_tool_descriptions())
        messages   = [
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": instruction},
        ]

        final_answer = None
        step         = 0

        while step < MAX_REACT_STEPS:
            step += 1
            console.print(f"  [dim]ReAct step {step}/{MAX_REACT_STEPS}[/]")

            try:
                llm_response = self._llm(messages, temperature=0.3, max_tokens=1500)
            except Exception as e:
                console.print(f"  [red]LLM error: {e}[/]")
                break

            parsed = self._parse_react(llm_response)

            if parsed["thought"]:
                console.print(f"  [italic cyan]Thought:[/] {parsed['thought'][:120]}...")

            if parsed["final_answer"]:
                final_answer = parsed["final_answer"]
                console.print("  [green]Final Answer obtained[/]")
                break

            if parsed["action"] and parsed["action_input"]:
                console.print(f"  [yellow]Tool:[/] {parsed['action']}")
                console.print(f"  [yellow]Input:[/] {parsed['action_input'][:80]}...")
                with console.status(f"  [dim]Running {parsed['action']}...[/]", spinner="dots"):
                    observation = run_tool(parsed["action"], parsed["action_input"])
                    time.sleep(0.5)
                if len(observation) > 3000:
                    observation = observation[:3000] + "\n[... truncated ...]"
                console.print(f"  [dim]Got {len(observation)} chars[/]")
                messages.append({"role": "assistant", "content": llm_response})
                messages.append({
                    "role": "user",
                    "content": (
                        f"Observation: {observation}\n\n"
                        "Continue your research. If you have enough data, give your Final Answer."
                    )
                })
            else:
                messages.append({"role": "assistant", "content": llm_response})
                messages.append({
                    "role": "user",
                    "content": (
                        "Use the ReAct format. Call a tool to gather more data, "
                        "or provide your Final Answer now."
                    )
                })

        if not final_answer:
            messages.append({
                "role": "user",
                "content": (
                    "Maximum research steps reached. "
                    "Provide your Final Answer now based on everything gathered."
                )
            })
            try:
                resp   = self._llm(messages, temperature=0.3, max_tokens=2000)
                parsed = self._parse_react(resp)
                final_answer = parsed["final_answer"] or resp
            except Exception as e:
                final_answer = f"Research incomplete: {e}"

        return final_answer

    def generate_startup_assessment(self, idea: dict) -> str:
        """Generate the executive viability verdict using all startup research."""
        console.print(Rule("[bold magenta]Generating Startup Viability Assessment[/]"))

        summary_parts = []
        for key, content in self.research_results.items():
            title   = STARTUP_RESEARCH_SECTIONS.get(key, {}).get("title", key)
            snippet = content[:300] if content else "No data"
            summary_parts.append(f"[{title}]: {snippet}")

        prompt = STARTUP_FINAL_ASSESSMENT_PROMPT.format(
            business_idea    = idea["business_idea"],
            industry         = idea["industry"],
            research_summary = "\n".join(summary_parts),
        )
        try:
            return self._llm(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=700,
            )
        except Exception as e:
            return f"Assessment generation failed: {e}"

    def run_startup(self, user_input: str) -> dict:
        """
        Full startup research pipeline:
        1. Parse business idea from free-form text
        2. Research all 9 startup sections via ReAct
        3. Generate viability verdict
        Returns dict with idea_info and all section results.
        """
        console.print(Panel(
            "[bold white]ClientIQ — Startup Research Mode[/]\n"
            "[dim]Market Research | Competitor Analysis | Go-To-Market Strategy[/]",
            border_style="yellow",
            padding=(1, 4)
        ))

        # Step 1: Extract structured idea
        idea = self.extract_startup_idea(user_input)

        # Step 2: Research each section
        self.research_results = {}
        for section_key in STARTUP_RESEARCH_SECTIONS:
            try:
                result = self.research_startup_section(section_key, idea)
                self.research_results[section_key] = result
            except Exception as e:
                console.print(f"  [red]Section '{section_key}' failed: {e}[/]")
                self.research_results[section_key] = f"Research failed: {e}"
            time.sleep(1)

        # Step 3: Viability verdict
        self.research_results["viability_assessment"] = self.generate_startup_assessment(idea)

        return {
            "idea_info": idea,
            "sections":  self.research_results,
        }

"""
tools.py — Agent Tool Implementations for ClientIQ
Tools: web_search, scrape_website, extract_emails_and_links
"""

import requests
import re
from bs4 import BeautifulSoup
from ddgs import DDGS


# ─────────────────────────────────────────────────────────
# TOOL 1: Web Search via DuckDuckGo (free, no API key)
# ─────────────────────────────────────────────────────────

def web_search(query: str, max_results: int = 6) -> str:
    """
    Search the web using DuckDuckGo.
    Returns formatted results with titles, URLs, and snippets.
    """
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url":   r.get("href", ""),
                    "snippet": r.get("body", "")
                })

        if not results:
            return "No search results found."

        output = f"[WEB SEARCH RESULTS for: '{query}']\n\n"
        for i, r in enumerate(results, 1):
            output += f"{i}. {r['title']}\n"
            output += f"   URL: {r['url']}\n"
            output += f"   Summary: {r['snippet']}\n\n"

        return output.strip()

    except Exception as e:
        return f"Search failed: {str(e)}"


# ─────────────────────────────────────────────────────────
# TOOL 2: Scrape Website — extract readable page content
# ─────────────────────────────────────────────────────────

def scrape_website(url: str, max_chars: int = 4000) -> str:
    """
    Fetch and extract clean readable text from a URL.
    Strips scripts, styles, navigation, and returns structured content.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=12)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove clutter
        for tag in soup(["script", "style", "nav", "footer",
                          "iframe", "noscript", "aside", "form"]):
            tag.decompose()

        # Title
        title = soup.title.string.strip() if soup.title else "No title"

        # Meta description
        meta_desc = ""
        meta = soup.find("meta", attrs={"name": "description"})
        if meta:
            meta_desc = meta.get("content", "")

        # Open Graph tags (brand info)
        og_tags = {}
        for og in soup.find_all("meta", property=lambda x: x and x.startswith("og:")):
            og_tags[og.get("property")] = og.get("content", "")

        # Headings
        headings = []
        for h in soup.find_all(["h1", "h2", "h3"], limit=20):
            text = h.get_text(strip=True)
            if text:
                headings.append(f"[{h.name.upper()}] {text}")

        # Paragraphs
        paragraphs = []
        for p in soup.find_all("p"):
            text = p.get_text(strip=True)
            if len(text) > 40:
                paragraphs.append(text)

        # CSS color hints (very lightweight)
        css_text = " ".join([s.get_text() for s in soup.find_all("style")])
        color_hints = re.findall(r"#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b", css_text)
        unique_colors = list(dict.fromkeys(color_hints))[:10]

        body_text = "\n".join(paragraphs)

        output = (
            f"[PAGE CONTENT: {url}]\n"
            f"Title: {title}\n"
            f"Meta Description: {meta_desc}\n"
        )
        if og_tags:
            output += f"OG Tags: {og_tags}\n"
        if unique_colors:
            output += f"CSS Colour Hints: {', '.join(unique_colors)}\n"
        output += (
            f"\n--- HEADINGS ---\n" + "\n".join(headings) + "\n\n"
            f"--- BODY TEXT ---\n{body_text[:max_chars]}"
        )

        return output.strip()

    except requests.exceptions.Timeout:
        return f"Timeout: Could not reach {url} within 12 seconds."
    except requests.exceptions.HTTPError as e:
        return f"HTTP Error for {url}: {str(e)}"
    except Exception as e:
        return f"Scraping failed for {url}: {str(e)}"


# ─────────────────────────────────────────────────────────
# TOOL 3: Extract Emails & Links from a page
# ─────────────────────────────────────────────────────────

def extract_emails_and_links(url: str) -> str:
    """
    Extract contact emails and important hyperlinks from a page.
    Useful for finding social media profiles and contact info.
    """
    headers = {"User-Agent": "Mozilla/5.0 (compatible; ClientIQBot/1.0)"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

        # Emails
        emails = re.findall(
            r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", resp.text
        )
        emails = list(dict.fromkeys(emails))[:10]

        # Social media links
        social_keywords = ["linkedin", "twitter", "instagram", "facebook",
                           "youtube", "github", "medium", "x.com"]
        social_links = {}
        all_links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = a.get_text(strip=True)
            for kw in social_keywords:
                if kw in href.lower():
                    social_links[kw] = href
            if href.startswith("http") and text and len(text) < 60:
                all_links.append(f"{text} → {href}")

        output = f"[CONTACT & SOCIAL from {url}]\n"
        output += f"Emails: {', '.join(emails) if emails else 'None found'}\n\n"
        output += "Social Media Profiles:\n"
        for platform, link in social_links.items():
            output += f"  {platform.capitalize()}: {link}\n"
        output += "\nOther Key Links:\n"
        output += "\n".join(all_links[:15])

        return output.strip()

    except Exception as e:
        return f"Extraction failed: {str(e)}"


# ─────────────────────────────────────────────────────────
# TOOL REGISTRY
# ─────────────────────────────────────────────────────────

TOOL_REGISTRY = {
    "web_search": {
        "fn": web_search,
        "description": (
            "Search the internet for any information. "
            "Input: a search query string. "
            "Best for: finding competitors, news, market data, social profiles, SEO info."
        ),
    },
    "scrape_website": {
        "fn": scrape_website,
        "description": (
            "Visit and read the full content of a specific webpage. "
            "Input: a full URL starting with https://. "
            "Best for: reading a company homepage, about page, services page."
        ),
    },
    "extract_emails_and_links": {
        "fn": extract_emails_and_links,
        "description": (
            "Extract contact emails and social media profile links from a webpage. "
            "Input: a full URL. "
            "Best for: finding LinkedIn, Instagram, Twitter handles and contact info."
        ),
    },
}


def get_tool_descriptions() -> str:
    """Returns formatted tool descriptions for inclusion in the LLM prompt."""
    lines = ["AVAILABLE TOOLS:"]
    for name, meta in TOOL_REGISTRY.items():
        lines.append(f"\n  Tool: {name}")
        lines.append(f"  Description: {meta['description']}")
    return "\n".join(lines)


def run_tool(name: str, input_str: str) -> str:
    """Execute a named tool with a string input. Returns result as string."""
    if name not in TOOL_REGISTRY:
        available = list(TOOL_REGISTRY.keys())
        return f"Error: Unknown tool '{name}'. Available tools: {available}"
    try:
        return TOOL_REGISTRY[name]["fn"](input_str.strip())
    except Exception as e:
        return f"Tool '{name}' execution error: {str(e)}"

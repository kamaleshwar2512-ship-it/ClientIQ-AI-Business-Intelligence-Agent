"""
prompts.py — All LLM prompt templates for ClientIQ Agent
"""

# ─────────────────────────────────────────────────────────
# SYSTEM PROMPT — defines the agent's role and ReAct format
# ─────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are ClientIQ, an elite Business Intelligence Research Agent.

Your job is to research a company thoroughly using live internet data and produce a complete, accurate Business Intelligence Report — like a senior consultant would.

PERSONA:
- Business Analyst
- Market Research Specialist
- Competitive Intelligence Expert
- Brand Research Specialist
- SEO & Digital Presence Auditor

REASONING FORMAT (ReAct):
You must strictly follow this format in your responses:

Thought: [What do I need to find? What is my current reasoning?]
Action: [tool_name]
Action Input: [the input to pass to the tool]

After the tool returns an Observation, continue:
Thought: [What did I learn? What do I need next?]
Action: [tool_name]
Action Input: [...]

When you have enough information:
Thought: I now have sufficient data to answer this research question.
Final Answer: [your complete, fact-based, professional answer for this section]

RULES:
- ALWAYS use tools to gather real data before answering. Never guess.
- Use at least 2-3 tool calls per research section for depth.
- If a tool returns an error, try a different query or URL.
- Be specific and evidence-based. No generic filler text.
- If information is truly unavailable after searching, say "Not publicly available" and infer carefully from what you found, clearly labelling it as [Inferred].
- Final Answer must be dense with facts, specific details, and real data.
- Do not repeat the same search query twice.

{tool_descriptions}
"""


# ─────────────────────────────────────────────────────────
# COMPANY EXTRACTION PROMPT
# ─────────────────────────────────────────────────────────

EXTRACT_COMPANY_PROMPT = """You are an expert at reading meeting transcripts and extracting structured business information.

Read the following client meeting transcript carefully and extract:
1. Company Name (exact)
2. Company Website URL (if mentioned, else say "unknown")
3. Industry / Business Sector
4. Key services or products mentioned
5. Any other company identifiers (location, size, founders, etc.)

Respond in this exact JSON format:
{{
  "company_name": "...",
  "website_url": "...",
  "industry": "...",
  "services": "...",
  "other_details": "..."
}}

TRANSCRIPT:
{transcript}
"""


# ─────────────────────────────────────────────────────────
# RESEARCH SECTION PROMPTS
# Each defines exactly what the agent must find for that BI section
# ─────────────────────────────────────────────────────────

RESEARCH_SECTIONS = {

    "company_overview": {
        "title": "Company Overview",
        "instruction": """
Research the following company and extract:
- Full company name
- Industry and sub-sector
- Headquarters location
- Year founded
- Company size (employees)
- Business model (B2B / B2C / SaaS / etc.)
- Core services and products
- Geographic presence (markets served)
- Revenue or funding (if public)

Company: {company_name}
Website: {website_url}

Search their website, LinkedIn, Crunchbase, and news sources.
"""
    },

    "brand_analysis": {
        "title": "Brand Analysis",
        "instruction": """
Research the brand identity of this company:
- Brand colours (hex codes if possible)
- Typography style (font families if detectable)
- Visual style (minimalist, corporate, playful, etc.)
- Brand tone (formal, friendly, technical, inspirational)
- Messaging style (how they talk about themselves)
- Taglines or slogans
- Brand personality
- Customer perception (reviews, sentiment)

Company: {company_name}
Website: {website_url}

Scrape their homepage, about page, and read their messaging carefully.
Look for CSS colour values. Check review sites for customer perception.
"""
    },

    "website_analysis": {
        "title": "Website Analysis",
        "instruction": """
Perform a detailed analysis of this company's website:
- Overall website quality (design, professionalism)
- UX/UI quality (navigation, layout, clarity)
- Mobile optimization (evidence from search or meta tags)
- Call-To-Action strategy (what actions they push visitors toward)
- Content quality and depth
- Blog / resources section existence
- Technical observations (speed hints, tech stack if visible)
- SEO signals (meta tags, structured data hints)

Company: {company_name}
Website: {website_url}

Scrape their homepage, services page, about page, and blog if available.
"""
    },

    "competitor_analysis": {
        "title": "Competitor Analysis",
        "instruction": """
Identify the top 4-5 direct competitors of this company.
For each competitor find:
- Company name and website
- Their key strengths
- Their key weaknesses
- How they position themselves vs this company

Company: {company_name}
Industry: {industry}
Website: {website_url}

Search for competitors using Google, industry reports, and comparison sites.
Look up each competitor's website and LinkedIn.
"""
    },

    "seo_and_digital_presence": {
        "title": "SEO & Digital Presence",
        "instruction": """
Analyze the digital presence and SEO posture of this company:
- Website SEO quality (meta tags, content depth, keyword usage)
- Primary keywords they seem to target
- Blog activity (frequency, topics, quality)
- Social media platforms they are active on
- LinkedIn presence (followers, activity, content)
- Instagram / Twitter / YouTube presence
- Engagement quality on social media
- Digital marketing maturity (paid ads, content marketing, email)
- Online reputation / reviews

Company: {company_name}
Website: {website_url}

Search their social profiles, check LinkedIn, look for review mentions, blog activity.
"""
    },

    "target_audience": {
        "title": "Target Audience",
        "instruction": """
Identify and profile the target audience of this company:
- Primary audience (who they sell to)
- Secondary audience (secondary buyer personas)
- Customer problems / pain points they solve
- Buyer intent type (awareness, consideration, decision)
- Estimated customer segment (enterprise, SMB, consumer, etc.)
- Industries or verticals they serve
- Geographic focus of their customer base

Company: {company_name}
Website: {website_url}
Services: {services}

Read their services page, case studies, testimonials, and any customer success content.
"""
    },

    "swot_analysis": {
        "title": "SWOT Analysis",
        "instruction": """
Based on your research so far, construct a comprehensive SWOT analysis:

STRENGTHS: What does this company genuinely do well? (evidence-based)
WEAKNESSES: Where do they fall short? (gaps in digital presence, positioning, etc.)
OPPORTUNITIES: What market trends or gaps could they exploit?
THREATS: What competitive or market threats do they face?

Company: {company_name}
Website: {website_url}
Industry: {industry}

Search for industry trends, competitive landscape, and company-specific signals.
This should be evidence-based, not generic. Cite specific findings.
"""
    },

    "market_opportunities": {
        "title": "Market Opportunities",
        "instruction": """
Identify 3-5 concrete market opportunities for this company:
- Underserved customer segments they could target
- Geographic markets they haven't entered
- Adjacent services or products they could offer
- Industry trends they could capitalize on
- Technology trends relevant to their business
- Partnership or integration opportunities

Company: {company_name}
Industry: {industry}
Website: {website_url}

Search for industry trends, market gaps, competitor blind spots, and emerging technologies.
"""
    },

    "strategic_recommendations": {
        "title": "Strategic Recommendations",
        "instruction": """
Generate 5-7 specific, actionable strategic recommendations for this company covering:
- Marketing improvements (specific tactics)
- SEO improvements (specific keyword or content gaps)
- Product or service expansion ideas
- Branding improvements (specific changes)
- Social media strategy (platforms, content types, frequency)
- Market positioning improvements
- Digital maturity improvements

Company: {company_name}
Website: {website_url}
Industry: {industry}

Base all recommendations on your research findings. Be specific, not generic.
"""
    },
}


# ─────────────────────────────────────────────────────────
# FINAL ASSESSMENT PROMPT
# ─────────────────────────────────────────────────────────

FINAL_ASSESSMENT_PROMPT = """
Based on all research conducted on {company_name}, write a concise executive-level assessment covering:

1. Market Position — Where do they stand vs. competitors?
2. Digital Maturity — How sophisticated is their online presence?
3. Branding Quality — Is their brand coherent, differentiated, and compelling?
4. Growth Potential — What is their realistic growth trajectory?
5. Competitive Standing — Are they a market leader, challenger, or niche player?

Keep it factual, dense with evidence, and under 300 words. 
This is the closing paragraph of a consulting report.

Research findings available: {research_summary}
"""


# ═══════════════════════════════════════════════════════════
# STARTUP RESEARCH MODE
# Used when someone says "I want to start a business in X"
# ═══════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────
# STARTUP IDEA EXTRACTION PROMPT
# ─────────────────────────────────────────────────────────

EXTRACT_STARTUP_IDEA_PROMPT = """You are a startup advisor and business analyst.

Read the following input carefully. The user wants to START a new business and needs research on it.

Extract:
1. Business idea / concept (what they want to do)
2. Industry / sector
3. Target market (who they want to sell to, if mentioned)
4. Geography / location (if mentioned, else assume India or Global)
5. Business model hint (online, offline, SaaS, marketplace, D2C, etc.)
6. Any unique angle or differentiator they mentioned
7. Budget or scale hint (if mentioned)

Respond in this exact JSON format:
{{
  "business_idea": "...",
  "industry": "...",
  "target_market": "...",
  "geography": "...",
  "business_model": "...",
  "unique_angle": "...",
  "budget_hint": "..."
}}

USER INPUT:
{user_input}
"""


# ─────────────────────────────────────────────────────────
# STARTUP RESEARCH SECTIONS
# 9 sections focused on market entry intelligence
# ─────────────────────────────────────────────────────────

STARTUP_RESEARCH_SECTIONS = {

    "market_landscape": {
        "title": "Market Landscape",
        "instruction": """
Research the current market for this business idea:
- Market size (TAM, SAM, SOM if available)
- Market growth rate and trend direction
- Key industry players and market leaders
- Is this market growing, mature, or declining?
- Recent news, investments, and funding in this space
- Indian market specifics (if applicable) vs global
- Any regulatory environment relevant to this business

Business Idea: {business_idea}
Industry: {industry}
Geography: {geography}

Search for market reports, industry news, investment news, and recent statistics.
"""
    },

    "competitor_benchmarking": {
        "title": "Competitor Benchmarking",
        "instruction": """
Find the top 5 existing competitors in this space.
For each competitor:
- Company name and website
- What they offer (products/services)
- Their pricing model (if available)
- Their strengths (what they do well)
- Their weaknesses (what gaps they leave)
- Their target customer
- Funding/scale (startup, SME, enterprise?)

Business Idea: {business_idea}
Industry: {industry}
Geography: {geography}

Search for competitors, comparison articles, review platforms, and industry directories.
"""
    },

    "customer_profile": {
        "title": "Target Customer Profile",
        "instruction": """
Define the ideal target customer for this new business:
- Who is the primary buyer? (demographics, role, income, behavior)
- Who is the secondary buyer?
- What specific pain points do they face that this business solves?
- Where do they currently find solutions? (which platforms/services)
- What motivates them to switch or try something new?
- What are their buying behaviors online?
- How do they discover new products/services?
- Which social platforms are they active on?

Business Idea: {business_idea}
Industry: {industry}
Target Market: {target_market}

Search for consumer research, Reddit discussions, LinkedIn, and review sites.
"""
    },

    "business_model_options": {
        "title": "Business Model & Revenue Options",
        "instruction": """
Research and recommend the best business model(s) for this idea:
- What business models work in this industry? (subscription, one-time, marketplace, freemium, etc.)
- How do successful competitors monetize?
- What is the typical pricing range in this space?
- What revenue streams could this business have?
- B2B vs B2C vs B2B2C — which fits best and why?
- What is the typical customer acquisition cost (CAC) in this space?
- What is the typical lifetime value (LTV) of a customer?
- Unit economics: what does profitability look like?

Business Idea: {business_idea}
Industry: {industry}
Business Model Hint: {business_model}

Search for competitor pricing pages, SaaS economics articles, and industry revenue model breakdowns.
"""
    },

    "tech_and_tools": {
        "title": "Tech Stack & Tools Required",
        "instruction": """
Research what technology, tools, and infrastructure are needed to build and run this business:
- What platform/website technology is typically used? (Shopify, custom, WordPress, etc.)
- What software tools are needed for operations?
- What third-party integrations are essential? (payments, CRM, logistics, etc.)
- What is the estimated monthly tech cost for a small-scale launch?
- Are there no-code/low-code options for an MVP?
- What hosting and infrastructure is typically used?
- Are there industry-specific platforms or tools?

Business Idea: {business_idea}
Industry: {industry}

Search for tech stacks used by similar companies, tool comparison articles, and startup tech blogs.
"""
    },

    "marketing_channels": {
        "title": "Marketing Channels & Customer Acquisition",
        "instruction": """
Research the most effective marketing and customer acquisition channels for this business:
- Which digital marketing channels work best in this industry?
- What SEO keywords should this business target? (search intent, volume)
- Is paid advertising (Google Ads, Meta Ads) effective here?
- What social media platforms matter most for this audience?
- What content strategy works for this niche? (blogs, videos, reels, etc.)
- Are there influencers or communities in this space?
- What is the typical cost-per-click (CPC) or customer acquisition cost?
- Are there offline channels that complement online?

Business Idea: {business_idea}
Industry: {industry}
Target Market: {target_market}
Geography: {geography}

Search for marketing strategy articles, digital marketing guides for this niche, and community forums.
"""
    },

    "risk_analysis": {
        "title": "Risk Analysis",
        "instruction": """
Identify key risks for someone starting this business:
- Market risks (saturation, declining demand, changing trends)
- Competitive risks (large funded competitors, commoditization)
- Operational risks (supply chain, logistics, staffing)
- Regulatory & legal risks (licenses, compliance, GST/taxes)
- Financial risks (cash flow, high CAC, thin margins)
- Technology risks (platform dependency, cybersecurity)
- External risks (economic downturn, seasonality)

For each risk, also identify potential mitigations.

Business Idea: {business_idea}
Industry: {industry}
Geography: {geography}

Search for failure case studies in this space, regulatory requirements, and market risk reports.
"""
    },

    "startup_swot": {
        "title": "SWOT Analysis for New Entrant",
        "instruction": """
Perform a SWOT analysis specifically for someone ENTERING this market as a new startup:

STRENGTHS (of entering now):
- Market timing advantages
- Technology enablers available today
- Gaps left by existing players

WEAKNESSES (of a new entrant):
- Lack of brand recognition
- Limited resources vs incumbents
- Barriers to entry

OPPORTUNITIES:
- Underserved niches or geographies
- Trends creating new demand
- Technology disruption possibilities

THREATS:
- Established competitor responses
- Market saturation risks
- Regulatory changes

Business Idea: {business_idea}
Industry: {industry}
Geography: {geography}

Be specific and evidence-based. Reference real market trends and competitor behaviors.
"""
    },

    "go_to_market_strategy": {
        "title": "Go-To-Market Strategy",
        "instruction": """
Develop a realistic go-to-market (GTM) strategy for this business idea:

Phase 1 — Launch (Month 1-3):
- MVP definition: what is the minimum viable product?
- First customer acquisition approach
- Budget allocation recommendation

Phase 2 — Growth (Month 4-12):
- Scaling channels that worked
- Partnership opportunities
- Brand building activities

Phase 3 — Scale (Year 2+):
- Expansion opportunities
- Team/hiring plan
- Technology investment priorities

Also include:
- Recommended launch platforms (marketplace vs own website vs both)
- Recommended pricing strategy for first 3 months
- Key metrics to track (KPIs)

Business Idea: {business_idea}
Industry: {industry}
Target Market: {target_market}
Geography: {geography}
Budget Hint: {budget_hint}

Search for startup GTM strategies in this space, founder playbooks, and launch case studies.
"""
    },
}


# ─────────────────────────────────────────────────────────
# STARTUP FINAL ASSESSMENT PROMPT
# ─────────────────────────────────────────────────────────

STARTUP_FINAL_ASSESSMENT_PROMPT = """
You are a senior startup advisor. Based on all research conducted on this business idea,
write a concise executive-level viability assessment covering:

1. Market Viability — Is the market large enough and accessible?
2. Competitive Feasibility — Can a new entrant realistically compete?
3. Revenue Potential — What does the financial opportunity look like?
4. Execution Complexity — How hard is this to build and operate?
5. Verdict — Should they pursue this idea? What is the #1 thing to focus on first?

Be direct, honest, and evidence-based. Under 350 words.
Do not be falsely optimistic. If the idea has serious problems, say so clearly.

Business Idea: {business_idea}
Industry: {industry}
Research findings: {research_summary}
"""

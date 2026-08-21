# 🚀 MASTER AI PROMPT: ADVANCED ENTERPRISE COMPANY DOMAIN CRAWLER & UI

> **How to use this file:**  
> Copy the contents inside the **MASTER PROMPT** section below and paste it directly into **Google AI Studio** (`https://aistudio.google.com`), **Gemini 1.5 Pro / Flash**, **Claude 3.5 Sonnet**, or **Antigravity**.

---

## 📌 Context: Current Project Architecture Analyzed

The existing project located at `company_domain_crawler` consists of the following core modules:
1. `src/main.py`: CLI entry point running the crawler pipeline.
2. `src/web_app.py`: FastAPI web server streaming progress via Server-Sent Events (SSE) `/crawl`.
3. `src/crawler.py`: Crawl4AI + `httpx` fallback browser engine with Playwright stealth mode.
4. `src/url_discovery.py`: Discovers URLs via `robots.txt`, sitemaps, and homepage HTML link extraction.
5. `src/page_selector.py`: Scores URLs based on heuristic keywords (`about`, `contact`, `legal`, `imprint`, etc.).
6. `src/extractor.py`: Extracts JSON-LD, microdata, phone numbers, emails, addresses, and corporate metadata.
7. `src/parser.py`: HTML structure parser extracting clean text, headers, footers, and schema tags.
8. `src/validator.py`: Normalizes and validates extracted company identity data.
9. `src/wikipedia_fallback.py`: Enriches missing data by querying Wikipedia / Wikidata APIs.
10. `src/models.py`: Pydantic models for `CompanyData`, `URLDiscoveryResult`, etc.
11. `src/telemetry.py`: Pipeline execution telemetry and timing tracking.
12. `src/templates/index.html`: Modern Tailwind CSS Web UI with 3-column live progress and JSON viewer.

---

# ✂️ COPY FROM HERE TO THE END & PASTE INTO GOOGLE AI STUDIO:

```markdown
# SYSTEM PROMPT: BUILD AN ADVANCED ENTERPRISE COMPANY DOMAIN CRAWLER & DATA EXTRACTION PLATFORM

You are an elite Senior Python & Full-Stack AI Engineer. Your mission is to take an existing `company_domain_crawler` project and build a significantly upgraded, **Enterprise-Grade Company Intelligence & Web Crawling Platform** with a modern Web UI, real-time streaming, and automatic per-domain local file storage.

---

## 🎯 KEY REQUIREMENTS & NEW FEATURES TO BUILD

### 1. Dynamic Per-Domain Local Storage (CRITICAL REQUIREMENT)
- **NO EXTERNAL PAID LLM / GEMINI API DEPENDENCY**: Do NOT use Google Gemini API, OpenAI API, or any paid LLM service in the Python backend. The crawler and extractor MUST run 100% locally and for free using Crawl4AI, Playwright, BeautifulSoup4, JSON-LD microdata parser, Regex patterns, and free Wikipedia/Wikidata REST APIs.
- When a user enters any domain (e.g. `microsoft.com` or `https://stripe.com`) and submits:
  - Sanitize the domain into a clean string (e.g. `microsoft_com` or `stripe_com_20260819_1630`).
  - Create a dedicated folder automatically under `output/<sanitized_domain>/`.
  - Save the following files inside that specific domain's folder:
    1. `company_data.json`: Full structured JSON payload of extracted identity intelligence.
    2. `discovered_urls.json`: All discovered sitemap and web page URLs with relevance scores.
    3. `summary.csv`: Tabular 1-line summary row containing key company fields.
    4. `crawl_log.txt`: Complete execution log and timestamp trace.
- Provide a **"Saved Crawls / Past History"** drawer or panel in the Web UI:
  - List all previously crawled domains saved in the local `output/` folder.
  - Allow the user to click any domain from history to view its stored `company_data.json` or download its full report package.

### 2. Multi-Domain & Batch Scraping Support
- Support single domain input as well as **Batch Processing** (comma-separated domains or `.txt`/`.csv` file upload in the UI).
- Process batch items sequentially or with a worker queue, saving each domain into its own separate output directory.

### 3. Advanced Crawling & Stealth Browser Engine
- **Crawl4AI + Playwright Integration**: Dynamic DOM rendering, handling single-page applications (SPAs), scroll-to-load, and modal overlay removal.
- **Anti-Bot & Stealth**: Custom User-Agents, stealth evasion, polite crawl delays (0.2s - 1s), and automatic fallback to `httpx` HTTP fetching if Playwright is blocked.
- **Intelligent URL Discovery**:
  - Parse `robots.txt`, `sitemap.xml`, `sitemap_index.xml`, and recursive internal links.
  - Filter out media files (`.pdf`, `.png`, `.jpg`, `.mp4`, `.zip`).
- **Heuristic & NLP Page Scoring**:
  - Automatically prioritize high-value pages: `/about`, `/contact`, `/imprint`, `/legal`, `/terms`, `/privacy`, `/locations`, `/team`, `/leadership`, `/investors`.

### 4. Deep Multi-Layer Intelligence Extractor
- **JSON-LD & Schema.org**: Extract `Organization`, `Corporation`, `LocalBusiness`, `PostalAddress` nodes.
- **Regex & Pattern Engine**:
  - Tax & Registration IDs (US EIN, UK CRN, EU VAT, DE HRB, India CIN/GSTIN).
  - Phone Numbers (International E.164 formats).
  - Email Addresses (Filtering out generic `example@domain.com` or webmaster emails).
  - Physical Addresses, Social Media Links (LinkedIn, Twitter/X, GitHub, Facebook, YouTube), Key Executives & Leadership.
- **Wikipedia & External API Fallback**:
  - Query Wikipedia/Wikidata API if core data is incomplete to verify legal name, founding year, parent company, and subsidiaries.
- **Strict Data Provenance**:
  - Track `source_pages` array for every data point so users know exactly which page provided the data.
  - Return `null` for unknown fields; never fabricate or guess.

### 5. Modern Glassmorphic Web UI & Dashboard
- Built using **FastAPI + HTML5 + Tailwind CSS + Vanilla JS (No build step required)**.
- Features:
  - **Header & Input Bar**: Target Domain input, Max Pages slider (1-50), Advanced Toggles (Wikipedia ON/OFF, Headless Mode ON/OFF, Concurrency limit).
  - **Live Progress Console (Server-Sent Events)**: Real-time phase updates (Discovery -> Scoring -> Crawling -> Extraction -> Wikipedia -> File Saving).
  - **Multi-Tab Result Panel**:
    - **Card View**: Styled badges, logos, contact card, address map link, leadership list.
    - **JSON Viewer**: Syntax-highlighted interactive JSON view with a "Copy to Clipboard" button.
    - **History & File Manager Drawer**: Search past crawls, view saved files, and download JSON/CSV.

---

## 🏗️ TARGET PROJECT ARCHITECTURE

```
company_domain_crawler_v2/
├── output/                          # Auto-created per-domain folders
│   └── microsoft_com/
│       ├── company_data.json
│       ├── discovered_urls.json
│       ├── summary.csv
│       └── crawl_log.txt
├── src/
│   ├── __init__.py
│   ├── main.py                      # CLI runner
│   ├── web_app.py                   # FastAPI server & SSE streaming routes
│   ├── config.py                    # Configuration constants & output paths
│   ├── models.py                    # Pydantic schemas
│   ├── crawler/
│   │   ├── discovery.py             # Robots.txt, sitemaps & link extractor
│   │   ├── selector.py              # Heuristic relevance page selector
│   │   └── fetcher.py               # Crawl4AI + Playwright + HTTP fallback
│   ├── extractors/
│   │   ├── jsonld_extractor.py      # Schema.org & JSON-LD parser
│   │   ├── pattern_extractor.py     # Regex for Tax IDs, Phone, Email, Address
│   │   └── core_extractor.py       # Aggregator merging all extraction layers
│   ├── enrichers/
│   │   └── wikipedia.py             # Wikipedia API verification
│   ├── utils/
│   │   ├── file_manager.py          # Per-domain folder creation & writers
│   │   └── logger.py                # Logger helper
│   └── templates/
│       └── index.html               # Tailwind CSS Single Page Application
├── requirements.txt
├── README.md
└── run_app.py                       # One-click launcher script
```

---

## 📋 PYDANTIC DATA MODEL (`src/models.py`)

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict

class CompanyData(BaseModel):
    domain: str
    company_name: Optional[str] = None
    legal_name: Optional[str] = None
    brand_name: Optional[str] = None
    registration_number: Optional[str] = None
    vat_tax_number: Optional[str] = None
    country: Optional[str] = None
    state_province: Optional[str] = None
    city: Optional[str] = None
    full_address: Optional[str] = None
    postal_code: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website_url: Optional[str] = None
    social_links: Dict[str, str] = Field(default_factory=dict)
    industry: Optional[str] = None
    business_description: Optional[str] = None
    business_activities: Optional[str] = None
    parent_company: Optional[str] = None
    subsidiaries: List[str] = Field(default_factory=list)
    key_executives: List[str] = Field(default_factory=list)
    verified_via_wikipedia: bool = False
    source_pages: List[str] = Field(default_factory=list)
    extracted_at: str = ""
```

---

## ⚙️ REQUIRED DEPENDENCIES (`requirements.txt`)

```txt
fastapi>=0.100.0
uvicorn>=0.22.0
crawl4ai>=0.3.0
playwright>=1.35.0
beautifulsoup4>=4.12.0
httpx>=0.24.0
pydantic>=2.0.0
jinja2>=3.1.0
pandas>=2.0.0
lxml>=4.9.0
python-multipart>=0.0.6
```

---

## 🛠️ SPECIFIC IMPLEMENTATION INSTRUCTIONS FOR AI

1. Write COMPLETE, fully executable Python code for every file. Do NOT use code snippets, placeholders (`...`), or incomplete implementations.
2. Implement `file_manager.py` such that when domain `example.com` is processed, it automatically creates `output/example_com/` and writes `company_data.json`, `discovered_urls.json`, `summary.csv`, and `crawl_log.txt`.
3. In `web_app.py`, implement endpoints:
   - `GET /` -> Render main Web UI.
   - `GET /crawl` -> EventSource SSE stream emitting real-time logs and final JSON.
   - `GET /history` -> Return JSON list of past saved domain directories in `output/`.
   - `GET /history/{domain_folder}` -> Return saved files content for that past domain.
   - `GET /download/{domain_folder}/{file_type}` -> Download JSON, CSV, or ZIP file.
4. Ensure `index.html` has a modern dark-mode glassmorphic theme with a domain submission box, live streaming logs, interactive results cards, copy JSON button, and a History panel to inspect saved domain files.
5. Generate a **complete `README.md`** file for the project root with the following sections:
   - Project title, description, and feature highlights.
   - **Local Setup & Installation** instructions for:
     - **Windows (PowerShell)** — virtual environment creation, activation, `pip install`, `playwright install chromium`, and running the server.
     - **macOS / Linux** — same steps with `source .venv/bin/activate`.
   - How to run the **Web UI** (browser URL, port number).
   - How to run the **CLI** mode with example commands.
   - The full **Output Data Schema** (JSON example output).
   - How to view the **History Panel** and download past crawl files.
   - Compliance & Safety rules.

The `README.md` must be written in clean Markdown, easy to follow for a non-developer user.

---

## 🐛 CRITICAL BUG FIXES REQUIRED (Based on Real Extraction Audit)

The following bugs were identified from a real crawl of `brewdog.com` where many fields returned `null` despite the company having public data. Fix ALL of these:

### BUG FIX 1: Deep Page Crawling Not Working (Most Critical)
- **Problem**: `source_pages` contained only `["https://brewdog.com/"]` — the crawler only visited the homepage.
- **Root Cause**: The URL discovery or page selector failed to select deep company pages like `/about`, `/imprint`, `/contact`, `/legal-notice`, `/privacy`.
- **Fix**: 
  - Ensure `url_discovery.py` extracts ALL internal links from the homepage HTML in addition to sitemaps.
  - Ensure `page_selector.py` always includes at minimum the homepage + top 3 scoring pages even if `max_pages=1`.
  - In `web_app.py` and `main.py`, set the **default `max_pages` to at least 15**.
  - After URL discovery, log all selected URLs to the console for debugging.

### BUG FIX 2: Wikipedia Enrichment Missing Many Fields
- **Problem**: `verified_via_wikipedia: true` was set but `country`, `city`, `industry`, `brand_name`, `phone` still returned `null`.
- **Root Cause 1**: In `web_app.py`, the enrichment loop only listed these fields:
  ```python
  important_fields = ["legal_name", "registration_number", "vat_tax_number", "industry", "full_address", "parent_company"]
  ```
  Fields like `country`, `city`, `brand_name`, `phone`, `email`, `business_activities` were missing from this list.
- **Fix**: Expand the enrichment list to include ALL fields:
  ```python
  important_fields = [
      "legal_name", "brand_name", "registration_number", "vat_tax_number",
      "industry", "full_address", "country", "city", "state_province",
      "postal_code", "phone", "email", "parent_company", "business_activities",
      "business_description", "website_url"
  ]
  ```

### BUG FIX 3: Wikipedia FIELD_MAP Missing Country, City, Phone
- **Problem**: `wikipedia_fallback.py` `FIELD_MAP` did not map `country`, `city`, `phone`, `email`, `founded`, `num_employees` fields from Wikipedia infoboxes.
- **Fix**: Expand `FIELD_MAP` in `wikipedia_fallback.py`:
  ```python
  FIELD_MAP = {
      "name": "legal_name",
      "legal_name": "legal_name",
      "trade_name": "brand_name",
      "brand": "brand_name",
      "type": "industry",
      "industry": "industry",
      "genre": "industry",
      "founded": "founded_year",
      "hq_location": "full_address",
      "headquarters": "full_address",
      "location": "full_address",
      "location_country": "country",
      "country": "country",
      "city": "city",
      "num_employees": "num_employees",
      "revenue": "revenue",
      "parent": "parent_company",
      "owner": "parent_company",
      "subsid": "subsidiaries",
      "subsidiaries": "subsidiaries",
      "key_people": "key_executives",
      "homepage": "website_url",
      "website": "website_url",
      "telephone": "phone",
      "phone": "phone",
      "email": "email",
  }
  ```

### BUG FIX 4: Wikipedia Domain Match Too Strict (Blocks Valid Enrichment)
- **Problem**: When `_domain_match = False`, ALL Wikipedia data was discarded even though partial enrichment (industry, country, description) is still valuable.
- **Fix**: In `web_app.py`, implement **two-tier Wikipedia enrichment**:
  - If `_domain_match = True`: Enrich ALL fields with high confidence.
  - If `_domain_match = False`: Still enrich safe non-identity fields: `industry`, `country`, `city`, `business_description`, `founded_year`, `parent_company` — but mark them as `unverified`.

### BUG FIX 5: Phone Regex Too Restrictive
- **Problem**: Phone regex only matched phones prefixed with keywords like `Tel:`, `Phone:`, missing bare phone numbers in contact blocks.
- **Fix**: In `extractor.py`, also add a broad international phone regex:
  ```python
  bare_phones = re.findall(
      r"(?<!\d)(\+?(?:\d[\s\-\.]?){7,15}\d)(?!\d)",
      page.text
  )
  ```
  Apply this on `/contact` and `/imprint` pages only (high-confidence context).

### BUG FIX 6: `website_url` Never Set
- **Problem**: `website_url` always returned `null` even though the domain is known.
- **Fix**: In `extract_all()` in `extractor.py`, after candidate selection, always set:
  ```python
  if not data.website_url:
      data.website_url = self.target_url
  ```

Generate all code files and the README.md now. Output every file completely with no placeholders.
```

# 🏢 Company Intelligence & Due Diligence Crawler

An advanced OSINT tool to extract verified company identity data from websites, enriched with **Official UK Companies House** records and **Wikipedia Intelligence**.

## 🚀 Features
- **Heuristic Page Discovery**: Finds About, Legal, and Contact pages automatically.
- **Multi-Source Extraction**: Uses JSON-LD, Meta Tags, and Regex to find legal names, tax IDs, and contacts.
- **UK Registry Integration**: Manual/Auto verification with Companies House API.
- **Wikipedia Enrichment**: Cross-references brand names with verified Wikipedia Infoboxes.
- **Modern Web UI**: Professional 3-column dashboard with real-time SSE logging.
- **Local History**: Automatically saves every crawl as a JSON file in `output/history/`.

## 🛠️ Setup & Installation

1. **Clone the project**
2. **Create a Virtual Environment**
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   ```
3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   playwright install
   ```
4. **Configure Environment**
   Create a `.env` file in the root directory:
   ```env
   COMPANIES_HOUSE_API_KEY=your_api_key_here
   ```

## 🖥️ Usage

### Run Web Interface (Recommended)
```bash
python src/web_app.py
```
Open [http://localhost:8080](http://localhost:8080) in your browser.

### Run CLI
```bash
python src/main.py stripe.com
```

## ☁️ Deployment Notes (Vercel/Cloud)
This project uses **Playwright (Crawl4AI)** which requires a full Chromium browser. 
- **Vercel**: Not recommended for the crawler part (Serverless limits).
- **Railway/Render**: Recommended. Use a `Dockerfile` to ensure `playwright install-deps` runs during deployment.

## 📂 Project Structure
- `src/pipeline.py`: Centralized research logic.
- `src/uk/`: Companies House API integration.
- `src/web_app.py`: FastAPI server & SSE streaming.
- `output/history/`: Saved JSON reports.

---
*Built for Professional Due Diligence Automation.*

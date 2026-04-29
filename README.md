# Domain Email Intelligence Engine (V2.0)

![Premium Dashboard](https://raw.githubusercontent.com/your-username/EmailS/main/app/static/mockup_preview.png)

A high-performance, autonomous intelligence gathering system designed to discover, verify, and pattern-match professional email addresses at scale. Featuring a modern Glassmorphism dashboard and real-time data streaming.

## 🚀 Features
- **Autonomous Discovery:** Automatically crawls top-tier domain lists (Tranco, etc.) to find company intelligence.
- **Deep Verification:** Multi-stage verification process to ensure high-quality, valid leads.
- **Pattern Matching:** Advanced inference engine that derives email patterns for large organizations.
- **Modern Dashboard:** Sleek, premium dark-mode interface with real-time system metrics.
- **Data Export:** Instant CSV export of verified intelligence for your CRM or outreach tools.
- **Admin Control:** Fine-grained control over crawl rates, daily limits, and search queries.

## 🛠️ Technology Stack
- **Backend:** FastAPI (Python 3.10+)
- **Database:** PostgreSQL (Production) / SQLite (Development)
- **Caching/Queuing:** Redis
- **Frontend:** Vanilla JS, HTML5, CSS3 (Modern Glassmorphism)
- **Deployment:** Docker & Docker Compose

## 📦 Quick Start

### Local Development (SQLite)
1. Clone the repository.
2. Create a virtual environment: `python -m venv venv`.
3. Activate: `.\venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Linux).
4. Install dependencies: `pip install -r requirements.txt`.
5. Start the app: `uvicorn app.main:app --reload`.

### Production Deployment (Docker)
1. Set up your `.env` file with production PostgreSQL credentials.
2. Run `docker-compose up -d`.
3. Access the dashboard on port `8000`.

## 🔒 Security
- This project is configured with a `.gitignore` to prevent sensitive credentials (`.env`) and large databases (`.db`) from being exposed in version control.

## 📜 License
Internal Enterprise Use Only.


# Company Profiling and Review Analysis Tool

## 1. Project Overview

### Description

This project automates the collection and analysis of company information to provide comprehensive company profiles. It addresses the challenge of manually gathering and verifying company data, which is time-consuming and prone to errors. By using web scraping, LLMs, and APIs, the tool extracts and processes information from various sources to deliver structured company profiles.

### Key Features

- Retrieves company profiles using minimal input (company name, location, industry)
- Google Search scraping using Custom Search API (20 URLs)
- Structured extraction of:
  - Website, Email, LinkedIn
  - Founding Year, Employees, Revenue
  - Top Executives
- Summarizes and classifies sentiment of news articles using GPT-4o Mini
- Scrapes and analyzes employee reviews from Glassdoor and Indeed
- Presents data in JSON and user-friendly UI
- Includes preview screenshot and structured documentation

### Technologies Used

- Backend: Python 3, FastAPI
- Frontend: HTML, CSS, JavaScript (Vanilla)
- Web Scraping: BeautifulSoup, Selenium
- API Integration: Google Custom Search API, OpenAI GPT-4o Mini
- Packaging: libraries.txt (pip)

---

## 2. Setup and Installation

### Prerequisites

- Python 3.x
- pip (Python package installer)

### Installation Instructions

1. Clone the repository.
2. Create a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate  # On Linux/macOS
venv\Scripts\activate   # On Windows
```

3. Install dependencies:

```bash
pip install -r libraries.txt
```

4. Add your API keys in a `.env` file:

```
GO_API_KEY=YOUR_GOOGLE_API_KEY
GO_CSE_ID=YOUR_GOOGLE_CSE_ID
OAI_API_KEY=YOUR_OPENAI_API_KEY
```

---

## 3. Usage

### Run the Application

```bash
uvicorn app:app --reload
```

Go to: `http://localhost:8000`

### Example Flow

1. Enter company details in UI
2. View matching companies
3. Select one to see full profile
4. Review includes: basic info, links, executives, revenue, news, sentiment, reviews

---

## 4. API Endpoints

- `GET /similar_companies/` – Find company matches  
- `GET /company_profile/` – Get full company profile  
- `GET /` – Load UI from index.html  

---

## 5. UI Preview

Screenshot of the web interface:

![Company Profile UI](UI_Sample.png)

---

## 6. Project Structure

```
CompPro/
├── app.py                               # FastAPI backend
├── index.html                           # Frontend HTML
├── script.js                            # JS logic for frontend interactions
├── libraries.txt                        # Python dependencies
├── UI_Samplle.png                       # UI screenshot
└── README.md                            # Documentation
```

---

## 7. Challenges Faced

| Challenge                      | Solution                                                              |
|-------------------------------|-----------------------------------------------------------------------|
| CAPTCHA blocks during scraping| Used Selenium, user-agent rotation, and headless browsers             |
| Inconsistent data across sites| Fallback scrapers and OpenAI inference for gaps                       |
| Rate limits on OpenAI API     | Batching with exponential backoff                                     |
| Review access restrictions    | Selenium with login automation                                        |

---

## 8. Future Enhancements

- Add OpenAI Deep Search integration
- Save profiles to MongoDB or SQLite
- Enable user login/dashboard
- Export profiles to PDF/Excel
- Docker support
- Async job queue for scraping
- Include Employee Reviews
- MCP Server

---

## 9. Contact

- **Email:** [i-dhruv.chawla@affine.ai](mailto:i-dhruv.chawla@affine.ai)
- **GitHub:** [github.com/dhruvchawla01](https://github.com/dhruvchawla01)
- **LinkedIn:** [linkedin.com/in/dhruvchawla01](https://linkedin.com/in/dhruvchawla01)

---

## 10. License

This project is licensed under the MIT License.

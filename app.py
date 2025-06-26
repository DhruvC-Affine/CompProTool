from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from openai import OpenAI
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
import json
import re
import uvicorn
import asyncio
import os
import httpx
import time
import nest_asyncio


nest_asyncio.apply()

app = FastAPI()

# API Keys
load_dotenv()

GOOGLE_API_KEY = os.getenv("GO_API_KEY")
GOOGLE_CSE_ID = os.getenv("GO_CSE_ID")
OPENAI_API_KEY = os.getenv("OAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}

# --- Helper Functions from Code 1 ---

async def search_google(query: str, num_results: int = 10) -> List[str]:
    """Search Google using Custom Search API and return top results."""
    url = f"https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "cx": GOOGLE_CSE_ID,
        "key": GOOGLE_API_KEY,
        "num": num_results
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
    return [item["link"] for item in data.get("items", [])]

async def get_company_website(company_name: str) -> Optional[str]:
    """Finds the company's official website using Google Custom Search."""
    search_results = await search_google(f"{company_name} official website", num_results=3)
    for url in search_results:
        if not any(excluded in url for excluded in ["linkedin.com", "crunchbase.com", "bloomberg.com"]):
            return url
    return None

async def find_leadership_page(website_url: str) -> Optional[str]:
    """Finds the leadership or executives page from the company website."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(website_url, headers=HEADERS, timeout=10)
            response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for link in soup.find_all("a", href=True):
            if re.search(r"(leadership|team|executives|management|about-us|board)", link.text, re.IGNORECASE):
                return urljoin(website_url, link["href"])
    except httpx.RequestError as e:
        print(f"Error fetching website: {e}")
    return None

async def summarize_with_openai_leadership(text: str, retries: int = 3, timeout: int = 30) -> List[Dict[str, str]]:
    """Summarizes and structures leadership data using OpenAI."""
    prompt = """Extract executive names and titles from the following text. Format the response in structured JSON as: [{"name": "John Doe", "title": "CEO"}, {"name": "Jane Smith", "title": "COO"}] TEXT:""" + text
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    openai_url = "https://api.openai.com/v1/chat/completions"
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "system", "content": "You are an AI that extracts structured leadership information."}, {"role": "user", "content": prompt}],
        "max_tokens": 500,
        "temperature": 0.7
    }
    for attempt in range(retries):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(openai_url, json=payload, headers=headers)
                response.raise_for_status()
            openai_response = response.json()
            if "choices" not in openai_response or not openai_response["choices"]:
                raise ValueError("Unexpected OpenAI API response format.")
            raw_content = openai_response["choices"][0]["message"]["content"]
            clean_content = re.sub(r"```json|```", "", raw_content).strip()
            try:
                structured_data = json.loads(clean_content)
                if not isinstance(structured_data, list) or not all(isinstance(item, dict) and "name" in item and "title" in item for item in structured_data):
                    raise ValueError("Parsed OpenAI response is not in expected JSON format.")
                return structured_data
            except json.JSONDecodeError as e:
                print(f"JSON decoding error: {e}, Raw Response: {raw_content}")
                return []
        except (httpx.HTTPStatusError, httpx.TimeoutException) as e:
            print(f"Attempt {attempt+1}: OpenAI API request failed - {str(e)}")
        except (KeyError, ValueError) as e:
            print(f"Attempt {attempt+1}: Failed to parse OpenAI response - {str(e)}, Raw Response: {response.text if 'response' in locals() else ''}")
        await asyncio.sleep(2)
    raise HTTPException(status_code=500, detail="Failed to fetch structured leadership data after retries.")

async def extract_executives_from_page(leadership_url: str) -> Optional[List[Dict[str, str]]]:
    """Extracts leadership details and structures the data using OpenAI."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(leadership_url, headers=HEADERS, timeout=10)
            response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        raw_text = []
        for section in soup.find_all(["h2", "h3", "h4"]):
            name = section.get_text(strip=True)
            description = section.find_next("p")
            if name:
                raw_text.append(f"{name}: {description.get_text(strip=True) if description else ''}")
        for div in soup.find_all("div"):
            if re.search(r"(CEO|CTO|CFO|Founder|Executive|Director|Board|Leadership|Manager|Officer)", div.get_text(), re.IGNORECASE):
                raw_text.append(div.get_text(strip=True))
        extracted_text = "\n".join(raw_text)
        if not extracted_text.strip():
            return None
        return await summarize_with_openai_leadership(extracted_text)
    except httpx.RequestError as e:
        print(f"Error fetching leadership page: {e}")
        return None

async def get_executive_linkedin(executive_names: List[str]) -> Dict[str, str]:
    """Searches for LinkedIn profiles of executives using Google Custom Search."""
    executive_linkedin_profiles = {}
    for name in executive_names:
        search_results = await search_google(f"{name} LinkedIn", num_results=1)
        linkedin_url = next((url for url in search_results if "linkedin.com/in/" in url), None)
        executive_linkedin_profiles[name] = linkedin_url or "Not found"
    return executive_linkedin_profiles

# --- Helper Functions from Code 2 ---

def init_driver():
    """Initializes Selenium WebDriver."""
    try:
        chrome_service = Service(ChromeDriverManager().install())
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(service=chrome_service, options=options)
        return driver
    except Exception as e:
        print(f"Error initializing WebDriver: {e}")
        return None

def scrape_website_selenium(url: str) -> str:
    """Extract text from a webpage using Selenium."""
    driver = init_driver()
    if driver is None:
        return f"Error: WebDriver failed to initialize for {url}"
    try:
        driver.get(url)
        time.sleep(3)  # Allow time for JavaScript rendering
        elements = driver.find_elements(By.TAG_NAME, "p")
        paragraphs = [e.text.strip() for e in elements if len(e.text.strip()) > 50]
        return " ".join(paragraphs[:5]) if paragraphs else "No relevant data found."
    except Exception as e:
        return f"Error scraping {url}: {str(e)}"
    finally:
        if driver:
            driver.quit()

async def find_similar_company_names(company_name: str, location: Optional[str] = None, industry: Optional[str] = None) -> List[Dict]:
    """Fetches similar company names using GPT-4o."""
    query = f"List 10 companies with name (lexically or semantically) similar to '{company_name}' with name, location, and industry in JSON format. Include the queried company if it exists."
    if location:
        query += f" Prefer companies in {location}."
    if industry:
        query += f" Prefer companies in {industry}."
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Return a JSON list of companies with fields: name, location, industry."},
                {"role": "user", "content": query}
            ],
            response_format={"type": "json_object"},
            max_tokens=600
        )
        return json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        return []

async def analyze_sentiment(text: str) -> str:
    """Analyzes sentiment of text using OpenAI."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Analyze the sentiment of the following text and return either 'Positive', 'Negative', or 'Neutral'."},
                {"role": "user", "content": text}
            ],
            max_tokens=50,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Sentiment analysis error: {e}")
        return "Sentiment analysis failed."
import json

async def generate_company_profile(name: str, scraped_data: Dict[str, str], executive_data: Optional[List[Dict[str, str]]] = None) -> Dict:
    """Use GPT to structure company profile with enhanced extraction and sentiment analysis."""
    context = "\n\n".join([f"Source: {url}\n{text}" for url, text in scraped_data.items() if text])

    prompt = f"""
    Based on the following extracted information, generate a structured company profile for {name}:
    {context}

    """
    if executive_data:
        prompt += f"\n\nHere is executive data to use:\n {executive_data}\n\n"

    prompt += """
    Provide the profile in JSON format with fields:
    - Name
    - Location
    - Industry
    - Website
    - LinkedIn
    - Email
    - Founded Year
    - Stock Price (if available)
    - Number of Employees
    - Revenue
    - Top Executives (strictly upto 6 executives, with Name, Position, LinkedIn, Email if available)
    - Latest News (atleast 4 financial news of last 3 months with detailed summaries and sentiment)
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Extract and structure company data."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=3000
        )
        profile = json.loads(response.choices[0].message.content)

        # Enhance News with Sentiment Analysis and Debugging
        if "Latest News" in profile and isinstance(profile["Latest News"], list):
            print("Latest News before sentiment analysis:", profile["Latest News"])  # Debug print 1
            for news_item in profile["Latest News"]:
                if "summary" in news_item:
                    sentiment = await analyze_sentiment(news_item["summary"])
                    news_item["sentiment"] = sentiment
                    print("News Item with Sentiment:", news_item)  # Debug print 2
            print("Latest News after sentiment analysis:", profile["Latest News"]) # Debug print 3
        else:
            print("Latest News not found or not a list.") # Debug print 4

        return profile
    except json.JSONDecodeError:
        print("JSON Decode Error") # Debug print 5
        return {}
    except Exception as e:
        print(f"Error in generate_company_profile: {e}") # Debug print 6
        return {}

# --- API Endpoints ---



@app.get("/similar_companies/")
async def search_companies(
    name: str = Query(..., description="Company name"),
    location: Optional[str] = Query(None, description="Company location"),
    industry: Optional[str] = Query(None, description="Industry")
):
    """Find similar companies."""
    similar_companies = await find_similar_company_names(name, location, industry)
    if not similar_companies:
        raise HTTPException(status_code=404, detail="No similar companies found.")
    return {"similar_companies": similar_companies}

@app.get("/company_profile/")
async def get_company_profile(
    name: str = Query(..., description="Selected company name"),
    location: Optional[str] = Query(None, description="Company location"),
    industry: Optional[str] = Query(None, description="Industry")
):
    """Fetch and structure detailed company details, including executives."""
    search_query = f"{name} {location or ''} {industry or ''} company profile"

    try:
        urls = await search_google(search_query, num_results=10)        # change value here for finding more relevant urls
    except HTTPException as e:
        return {"error": e.detail}

    scraped_data = {}
    for url in urls[:8]:        # change the value here for more visited urls
        scraped_data[url] = scrape_website_selenium(url)

    # Attempt to extract executive data
    executive_data = None
    website = await get_company_website(name)
    if website:
        leadership_page = await find_leadership_page(website)
        if leadership_page:
            executive_data = await extract_executives_from_page(leadership_page)
            if executive_data:
                executive_names = [exec["name"] for exec in executive_data]
                executive_linkedin_profiles = await get_executive_linkedin(executive_names)
                for exec in executive_data:
                    exec["linkedin"] = executive_linkedin_profiles.get(exec["name"], "Not found")

    profile = await generate_company_profile(name, scraped_data, executive_data)

    return {"company": name, "profile": profile, "sources": list(scraped_data.keys())}

app.mount("/static", StaticFiles(directory="."), name="static")#serves static files from current directory.
templates = Jinja2Templates(directory=".")#sets the template directory to the current directory.

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serves the index.html file."""
    return templates.TemplateResponse("index.html", {"request": request})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
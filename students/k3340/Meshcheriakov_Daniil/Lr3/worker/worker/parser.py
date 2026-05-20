import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (Lr3 celery worker)"}


def fetch_and_extract(url: str) -> tuple[str, str]:
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    h1 = soup.find("h1")
    if not h1:
        raise ValueError("No <h1> on the page")
    title = h1.get_text(strip=True)

    description = ""
    content_div = soup.find("div", class_="mw-parser-output")
    if content_div:
        for p in content_div.find_all("p", recursive=False):
            text = p.get_text(strip=True)
            if len(text) > 50:
                description = text
                break

    return title, description

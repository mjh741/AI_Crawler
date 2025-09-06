import re
import asyncio
import json
import time
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

from playwright.sync_api import sync_playwright

def fetch_robots_txt(root, log=lambda m: None):
    try:
        robots_url = urljoin(root, "/robots.txt")
        r = requests.get(robots_url, timeout=10)
        if r.status_code == 200:
            return r.text
        return ""
    except Exception as e:
        log(f"robots.txt fetch error: {e}")
        return ""

def extract_json_ld(html):
    soup = BeautifulSoup(html, "html.parser")
    payloads = []
    for tag in soup.find_all("script", {"type": "application/ld+json"}):
        try:
            data = json.loads(tag.string or "{}")
            payloads.append(data)
        except Exception:
            pass
    return payloads

def extract_headings(html):
    soup = BeautifulSoup(html, "html.parser")
    h1 = [h.get_text(strip=True) for h in soup.find_all("h1")]
    h2 = [h.get_text(strip=True) for h in soup.find_all("h2")]
    return h1, h2

def is_question(s):
    s2 = s.strip().lower()
    return s2.endswith("?") or s2.startswith(("what ","how ","why ","when ","which ","who ","where "))

def score_answerability(h1, h2):
    allh = h1 + h2
    if not allh:
        return 0, 0.0
    questions = sum(1 for x in allh if is_question(x))
    pct = questions/len(allh)
    pts = min(10, int(pct*10))
    return pts, pct

def run_scan(url, max_pages=10, max_depth=2, page_timeout_sec=25, log=lambda m: None):
    t0 = time.time()
    parsed = urlparse(url)
    root = f"{parsed.scheme}://{parsed.netloc}"
    visited = set()
    queue = [(url, 0)]
    pages = []
    robots_text = fetch_robots_txt(root, log=log)

    log("Launching headless browser")
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox"])
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        while queue and len(pages) < max_pages:
            cur, depth = queue.pop(0)
            if cur in visited or depth > max_depth:
                continue
            visited.add(cur)
            log(f"Rendering {cur}")
            try:
                page = context.new_page()
                page.set_default_timeout(page_timeout_sec * 1000)
                page.goto(cur, wait_until="domcontentloaded")
                html = page.content()
                title = page.title()
                soup = BeautifulSoup(html, "html.parser")
                desc_tag = soup.find("meta", {"name":"description"})
                description = desc_tag.get("content","") if desc_tag else ""
                og_title = ""
                og_tag = soup.find("meta", {"property":"og:title"})
                if og_tag: og_title = og_tag.get("content","")
                json_ld = extract_json_ld(html)
                h1, h2 = extract_headings(html)

                pages.append({
                    "url": cur,
                    "title": title,
                    "description": description,
                    "og_title": og_title,
                    "h1": h1,
                    "h2": h2,
                    "json_ld_types": [x.get("@type") for x in json_ld if isinstance(x, dict) and x.get("@type")]
                })

                for a in soup.find_all("a", href=True):
                    href = a["href"].strip()
                    if href.startswith("#"): continue
                    child = urljoin(cur, href)
                    if urlparse(child).netloc == urlparse(root).netloc:
                        if child not in visited and len(pages)+len(queue) < max_pages:
                            queue.append((child, depth+1))
                page.close()
            except Exception as e:
                log(f"Error rendering {cur}: {e}")

        context.close()
        browser.close()

    a_score = 5 if robots_text else 0
    b_score = 0
    for pg in pages:
        if pg["json_ld_types"]:
            b_score = 10
            break
    all_h1 = [h for pg in pages for h in pg["h1"]]
    all_h2 = [h for pg in pages for h in pg["h2"]]
    c_raw, c_pct = score_answerability(all_h1, all_h2)
    d_score = 0
    for pg in pages:
        text = " ".join(pg["h1"] + pg["h2"]).lower()
        if any(k in text for k in ["privacy","contact","about","terms"]):
            d_score = 5
            break
    e_score = 5
    f_score = 0

    overall = a_score + b_score + c_raw + d_score + e_score + f_score
    results = {
        "root": url,
        "duration_sec": round(time.time()-t0, 2),
        "scores": {
            "A_crawlability": a_score,
            "B_structured_data": b_score,
            "C_answerability": c_raw,
            "D_authority": d_score,
            "E_technical": e_score,
            "F_agent_endpoints": f_score,
            "overall": overall
        },
        "answerability_ratio": c_pct,
        "robots_present": bool(robots_text),
        "pages": pages[:max_pages],
        "limits": {"max_pages": max_pages, "max_depth": max_depth, "timeout_sec": page_timeout_sec}
    }
    return results

#!/usr/bin/env python3
"""
tools/score_accounts.py
Landing page crawler, tracking pixel scanner, and tier classifier.
Cleaned for production-grade use.
"""

import os
import csv
import re
import urllib.request
from urllib.error import URLError, HTTPError
from dotenv import load_dotenv

load_dotenv()

CSV_PATH = os.path.join(".tmp", "companies.csv")

CORE_VERTICALS = {"HVAC", "Plumbing", "Roofing", "Medical", "Legal"}
SECONDARY_VERTICALS = {"Landscaping", "Cleaning", "Pest Control", "Janitorial"}

def download_html(url):
    """
    Downloads webpage HTML content using standard headers to bypass basic blocks.
    Returns empty string if any error occurs.
    """
    if not url.startswith("http"):
        url = "https://" + url
        
    print(f"[Scoring Engine] Crawling landing page: {url}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }
        
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as response:
            return response.read().decode('utf-8', errors='ignore')
    except (URLError, HTTPError, Exception) as e:
        print(f"[Scoring Engine] Error crawling {url}: {e}")
        return ""

def analyze_html(html, vertical):
    """
    Analyzes website HTML and returns flags for Google Ads and Yelp Ads pixels,
    along with identified lead response channels.
    """
    has_google = False
    has_yelp = False
    response_channels = ["calls"]  # Default base channel
    
    if not html:
        return has_google, has_yelp, response_channels

    # 1. Google Ads Checking
    google_signatures = [
        r"googletagmanager\.com/gtag/js",
        r"googleadservices\.com/pagead/conversion",
        r"google_ad_client",
        r"gtag\s*\(\s*['\"]config['\"],\s*['\"]AW-"
    ]
    for sig in google_signatures:
        if re.search(sig, html, re.IGNORECASE):
            has_google = True
            break
            
    # 2. Yelp Ads Checking
    yelp_signatures = [
        r"yelp\.com/biz_attribute",
        r"yelp-widget",
        r"yelp\.com/embed/widget"
    ]
    for sig in yelp_signatures:
        if re.search(sig, html, re.IGNORECASE):
            has_yelp = True
            break

    # 3. Lead Capture Gaps (Live chat or form check)
    chat_patterns = [
        r"livechat", r"chat-widget", r"drift\.com", r"intercomcdn", 
        r"tawk\.to", r"tidio", r"click-to-chat", r"text-back"
    ]
    has_live_chat = False
    for pat in chat_patterns:
        if re.search(pat, html, re.IGNORECASE):
            has_live_chat = True
            break
            
    form_patterns = [
        r"<form", r"contact-form", r"input name=\"email\"", r"submit-lead"
    ]
    has_form = False
    for pat in form_patterns:
        if re.search(pat, html, re.IGNORECASE):
            has_form = True
            break

    if has_live_chat:
        response_channels.append("webchat")
    if has_form:
        response_channels.append("forms")

    return has_google, has_yelp, response_channels

def calculate_score(vertical, has_google, has_yelp, response_channels):
    """
    Calculates scoring points (out of 100) based on scoring-criteria.md weights.
    """
    points = 0
    
    # 1. Vertical Alignment (Max 30)
    if vertical in CORE_VERTICALS:
        points += 30
    elif vertical in SECONDARY_VERTICALS:
        points += 15
        
    # 2. Marketing Spend (Max 30)
    if has_google and has_yelp:
        points += 30
    elif has_google or has_yelp:
        points += 20
        
    # 3. Lead Leak & Gaps (Max 40)
    if "webchat" not in response_channels:
        if "forms" in response_channels:
            points += 20
        else:
            points += 40
            
    points = min(points, 100)
    
    # Tier classification
    if points >= 80:
        tier = 1
    elif points >= 50:
        tier = 2
    else:
        tier = 3
        
    return points, tier

def score_accounts():
    if not os.path.exists(CSV_PATH):
        print(f"[Scoring Engine] Error: {CSV_PATH} not found.")
        return False
        
    updated_rows = []
    headers = []
    
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        new_fields = ["has_google_ads", "has_yelp_ads", "scoring_points", "tier"]
        for field in new_fields:
            if field not in headers:
                headers.append(field)
                
        for row in reader:
            website = row.get("website", "")
            vertical = row.get("vertical", "")
            
            html = download_html(website)
            has_google, has_yelp, response_channels = analyze_html(html, vertical)
            
            points, tier = calculate_score(vertical, has_google, has_yelp, response_channels)
            
            row["has_google_ads"] = str(has_google)
            row["has_yelp_ads"] = str(has_yelp)
            row["response_channels"] = ",".join(response_channels)
            row["scoring_points"] = str(points)
            row["tier"] = str(tier)
            
            print(f"[Scoring Engine] Scored {row.get('company_name')}: Points={points}, Tier={tier}")
            updated_rows.append(row)

    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(updated_rows)
        
    print(f"[Scoring Engine] Finished scoring leads. File updated at {CSV_PATH}")
    return True

if __name__ == "__main__":
    score_accounts()

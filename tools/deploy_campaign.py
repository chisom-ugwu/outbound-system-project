#!/usr/bin/env python3
"""
tools/deploy_campaign.py
Generates compliant problem-focused outreach copy and pushes enriched prospects
to Instantly.ai and HubSpot CRM.
Cleaned for production-grade use.
"""

import os
import csv
import json
import re
import urllib.request
from urllib.error import URLError, HTTPError
from dotenv import load_dotenv

load_dotenv()

CSV_PATH = os.path.join(".tmp", "companies.csv")

INSTANTLY_KEY = os.getenv("INSTANTLY_API_KEY")
HUBSPOT_TOKEN = os.getenv("HUBSPOT_ACCESS_TOKEN")

BANNED_BUZZWORDS = ["streamline", "synergize", "disrupt", "revolutionary", "cutting-edge", "innovative", "optimum", "paradigm-shift"]

def validate_outreach_copy(copy_text):
    """
    Asserts copy compliance with strict brand guidelines:
    - No em-dashes
    - No quotation marks (single/double)
    - No buzzwords
    """
    if "—" in copy_text or "\u2014" in copy_text:
        copy_text = copy_text.replace("—", "").replace("\u2014", "")
        
    if '"' in copy_text or "'" in copy_text or "`" in copy_text:
        copy_text = copy_text.replace('?', '').replace('"', '').replace("'", "").replace("`", "")
        
    for word in BANNED_BUZZWORDS:
        if word in copy_text.lower():
            pattern = re.compile(re.escape(word), re.IGNORECASE)
            copy_text = pattern.sub("improve", copy_text)
            
    return copy_text

def generate_outreach_copy(company_name, vertical):
    """
    Generates a high-converting, 5-part cold outreach copy block.
    Strictly follows copy-framework.md layout.
    """
    subject = "Quick question on lead response"
    line1 = f"I noticed you are currently running marketing ads for {vertical} services at {company_name}."
    line2 = "It looks like there is no option to text your team directly from the landing page, which means missed calls are likely going straight to voicemail."
    line3 = "CoreAI helps local businesses automatically follow up with missed callers via SMS, turning up to 30 percent of missed calls into booked jobs."
    cta = "I put together a quick lead response audit comparing your sites response speed to 2 local competitors. Would you like me to send over the PDF?"
    
    body = f"{line1}\n\n{line2}\n\n{line3}\n\n{cta}"
    validated_body = validate_outreach_copy(body)
    
    return subject, validated_body

def deploy_to_instantly(name, email, company, subject, body):
    """Pushes a prospect to Instantly.ai campaigns API."""
    if not INSTANTLY_KEY:
        print("[Instantly Sync] Error: INSTANTLY_API_KEY is not configured in .env.")
        return False
        
    print(f"[Instantly Sync] Pushing {email} to Instantly campaign...")
    url = "https://api.instantly.ai/1/lead/add"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {INSTANTLY_KEY}"
    }
    data = {
        "api_key": INSTANTLY_KEY,
        "campaign_id": "coreai_outreach_campaign_1",
        "skip_if_in_workspace": True,
        "leads": [
            {
                "email": email,
                "first_name": name.split(" ")[0],
                "last_name": name.split(" ")[-1] if len(name.split(" ")) > 1 else "",
                "company_name": company,
                "custom_variables": {
                    "email_subject": subject,
                    "email_body": body
                }
            }
        ]
    }
    
    try:
        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            print(f"[Instantly Sync] Instantly Success: {res_data}")
            return True
    except Exception as e:
        print(f"[Instantly Sync] Error pushing to Instantly: {e}")
        return False

def deploy_to_hubspot(name, email, company):
    """Upserts prospect to HubSpot CRM under Active Outreach."""
    if not HUBSPOT_TOKEN:
        print("[HubSpot Sync] Error: HUBSPOT_ACCESS_TOKEN is not configured in .env.")
        return False
        
    print(f"[HubSpot Sync] Upserting contact {email} in HubSpot CRM...")
    url = "https://api.hubapi.com/crm/v3/objects/contacts"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {HUBSPOT_TOKEN}"
    }
    data = {
        "properties": {
            "email": email,
            "firstname": name.split(" ")[0],
            "lastname": name.split(" ")[-1] if len(name.split(" ")) > 1 else "",
            "company": company,
            "lifecyclestage": "lead",
            "hs_lead_status": "Active Outreach"
        }
    }
    
    try:
        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=10) as response:
            print(f"[HubSpot Sync] HubSpot Success: Status {response.status}")
            return True
    except Exception as e:
        print(f"[HubSpot Sync] Error pushing to HubSpot: {e}")
        return False

def deploy_campaign():
    if not os.path.exists(CSV_PATH):
        print(f"[Deploy Campaign] Error: {CSV_PATH} not found.")
        return False
        
    updated_rows = []
    headers = []
    
    total_processed = 0
    total_synced = 0
    
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        if "sync_status" not in headers:
            headers.append("sync_status")
            
        for row in reader:
            email = row.get("lead_owner_email", "")
            name = row.get("lead_owner_name", "")
            company = row.get("company_name", "")
            vertical = row.get("vertical", "")
            tier = row.get("tier", "3")
            
            if tier in ["1", "2"] and email:
                total_processed += 1
                subject, body = generate_outreach_copy(company, vertical)
                
                instantly_ok = deploy_to_instantly(name, email, company, subject, body)
                hubspot_ok = deploy_to_hubspot(name, email, company)
                
                if instantly_ok and hubspot_ok:
                    row["sync_status"] = "Synced"
                    total_synced += 1
                else:
                    row["sync_status"] = "Failed"
            else:
                row["sync_status"] = "Skipped"
                
            updated_rows.append(row)

    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(updated_rows)
        
    print(f"[Deploy Campaign] Deploy complete. Processed: {total_processed}, Synced: {total_synced}. File updated at {CSV_PATH}")
    return True

if __name__ == "__main__":
    deploy_campaign()

#!/usr/bin/env python3
"""
tools/send_notification.py
Aggregates run metrics from .tmp/companies.csv and triggers a Slack Webhook
notification with an operational summary digest.
Cleaned for production-grade use.
"""

import os
import csv
import json
import urllib.request
from dotenv import load_dotenv

load_dotenv()

CSV_PATH = os.path.join(".tmp", "companies.csv")
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK_URL")

def build_summary():
    """Reads companies.csv and aggregates operational metrics."""
    if not os.path.exists(CSV_PATH):
        return None
        
    total_leads = 0
    tiers = {1: 0, 2: 0, 3: 0}
    enriched_contacts = 0
    synced_contacts = 0
    
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_leads += 1
            
            tier_str = row.get("tier", "3")
            try:
                tier_val = int(tier_str)
                if tier_val in tiers:
                    tiers[tier_val] += 1
            except ValueError:
                tiers[3] += 1
                
            email = row.get("lead_owner_email", "")
            if email:
                enriched_contacts += 1
                
            sync_status = row.get("sync_status", "")
            if sync_status == "Synced":
                synced_contacts += 1
                
    return {
        "total_leads": total_leads,
        "tier1": tiers[1],
        "tier2": tiers[2],
        "tier3": tiers[3],
        "enriched": enriched_contacts,
        "synced": synced_contacts
    }

def send_slack_notification(summary):
    """Fires a Slack message block with the digest summary."""
    text_message = (
        "🤖 *CoreAI Outbound System - Run Summary Digest*\n\n"
        f"• *Total Leads Received:* {summary['total_leads']}\n"
        f"• *Tier Breakdown:*\n"
        f"  - Tier 1 (High Priority): {summary['tier1']}\n"
        f"  - Tier 2 (Medium Priority): {summary['tier2']}\n"
        f"  - Tier 3 (Low Priority): {summary['tier3']}\n"
        f"• *Enriched Contacts:* {summary['enriched']}\n"
        f"• *Synced to Campaign & CRM:* {summary['synced']}\n\n"
        "✅ *Outbound run successfully closed.*"
    )
    
    if not SLACK_WEBHOOK:
        print("[Notification] Error: SLACK_WEBHOOK_URL is not configured in .env.")
        print("Run Digest Summary:\n" + text_message)
        return False
        
    print("[Notification] Sending Slack Webhook payload...")
    payload = {"text": text_message}
    headers = {"Content-Type": "application/json"}
    
    try:
        req = urllib.request.Request(
            SLACK_WEBHOOK, 
            data=json.dumps(payload).encode('utf-8'), 
            headers=headers, 
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            print(f"[Notification] Slack Webhook delivered. Response status: {response.status}")
            return True
    except Exception as e:
        print(f"[Notification] Failed to trigger Slack Webhook: {e}")
        return False

def main():
    import sys
    if sys.stdout.encoding != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except AttributeError:
            pass
            
    summary = build_summary()
    if summary:
        send_slack_notification(summary)
    else:
        print("[Notification] No data available to summarize.")

if __name__ == "__main__":
    main()

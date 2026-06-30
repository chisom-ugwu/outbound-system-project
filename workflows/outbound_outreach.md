# SOP: Outbound Outreach Campaign Orchestration

This SOP governs the end-to-end automated pipeline for identifying, scoring, enriching, and launching outreach campaigns targeting high-value SMB prospects under the **CoreAI** outbound system.

## 🏁 Workflow Inputs
- **Drive CSV Payload:** Incoming file reference containing raw leads.
- **Environment variables:** Valid tokens for enrichment APIs and CRM sync (.env).

## 🚀 Execution Steps

### Step 1: Real-time File Intake
1. Execute the listener `tools/fetch_latest_leads.py` to catch incoming webhook requests.
2. The listener downloads the raw leads CSV matching the payload's `file_id`.
3. The downloaded file is streamed locally to `.tmp/companies.csv`.
4. The tool deletes the source cloud file immediately after download.
5. *Command:* `python tools/fetch_latest_leads.py <file_id>`

### Step 2: Account Scoring & Classification
1. Run the Account Scoring tool.
2. It reads `.tmp/companies.csv` and crawls the landing page of each company.
3. Programmatically scans page HTML for Google Ads gtag/conversion pixels and Yelp ad widgets.
4. Calculates point-based scores out of 100 and assigns Tiers:
   - Tier 1: Score >= 80
   - Tier 2: Score 50 - 79
   - Tier 3: Score < 50
5. *Command:* `python tools/score_accounts.py`

### Step 3: Decision Maker Enrichment (Waterfall)
1. Run the Enrichment tool to find verified Owner/Founder contact details.
2. This runs a waterfall search (Saleshandy -> Explorium -> Deepline) *only* on Tier 1 and Tier 2 leads.
3. Scrubs catch-all or generic email addresses (e.g. info@, contact@).
4. *Command:* `python tools/enrich_leads.py`

### Step 4: Compliant Copy Generation & CRM Deployment Sync
1. Run the Deployment tool to compose custom emails and sync platforms.
2. Generates conversion copy matching strict guidelines (no em-dashes, no quotation marks, no buzzwords).
3. Inserts customOpportunity Audit offer CTA.
4. Pushes lead data to Instantly.ai campaigns and HubSpot CRM contact records.
5. *Command:* `python tools/deploy_campaign.py`

### Step 5: Operational Notification
1. Run the notification script to summarize execution metrics.
2. Reads the finalized `.tmp/companies.csv` and compiles counts for processed leads, tier breakdown, and successful campaign pushes.
3. Triggers Slack Webhook payload to notify the team.
4. *Command:* `python tools/send_notification.py`

## ⚠️ Exception Handling & Recovery
- **Landing Page Crawler Blocks:** If a website fails to crawl (due to bot blocking or downtime), the scoring engine logs the failure and falls back to a neutral 15-point vertical score without ad/leak points to prevent pipeline stalls.
- **Enrichment Failures:** If all waterfall APIs return empty or catch-all contacts, the lead is marked `sync_status = Skipped` and omitted from Instantly/HubSpot uploads.

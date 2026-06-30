# CoreAI Lead Scoring Criteria

We target localized SMBs in service-based verticals (HVAC, plumbing, roofing, medical, legal). The goal is to identify businesses spending marketing dollars (Ads) but losing leads due to a lack of automated text response / speed-to-lead automation.

### 1. Scoring Weights

The scoring system assigns a percentage-based score (out of 100 points maximum) across three primary categories:

| Criteria Category | Weight / Max Points | Description |
| :--- | :--- | :--- |
| **Vertical Alignment** | **30 Points** | HVAC, Plumbing, Roofing, Medical, Legal = **30 points**.<br>Other Home Services (landscaping, cleaning) = **15 points**.<br>All other verticals = **0 points**. |
| **Marketing Spend** | **30 Points** | Google Ads Conversion/Remarketing Tags AND Yelp tracking pixels detected = **30 points**.<br>Google Ads OR Yelp tracking pixel detected only = **20 points**.<br>No ad tracking code detected on site HTML = **0 points**. |
| **Lead Leak & Response Gaps** | **40 Points** | No SMS click-to-chat, no webchat widget, or high Yelp/Google profile response latency (>1 hour listed) = **40 points**.<br>Standard contact form present but no live chat/SMS = **20 points**.<br>Fully functional, responsive live webchat/SMS text-back widget = **0 points** (No leak). |

### 2. Detection logic
The `tools/score_accounts.py` crawler scans website HTML and headers for:
- **Google Ads:** Matches signatures like `googletagmanager.com/gtag/js`, `googleadservices.com/pagead/conversion`, or global site tags (`gtag`).
- **Yelp Ads:** Matches signatures like `yelp.com/biz_attribute` tracking codes or Yelp widget/conversion scripts.

### 3. Tier Assignment based on Total Score

- **Tier 1 (High Priority):** **Score >= 80%** (80-100 points)
  - *Typically*: Core vertical + active advertising + severe speed-to-lead leak.
- **Tier 2 (Medium Priority):** **Score 50% - 79%** (50-79 points)
  - *Typically*: Home service vertical + active ads but moderate response options.
- **Tier 3 (Low Priority):** **Score < 50%** (<50 points)
  - *Typically*: Non-target vertical or no active ad spend.

---
name: seo-audit
description: "SEO analysis and reporting using Google Search Console data and external sources. Use when the user asks about SEO, search rankings, keywords, CTR, impressions, search console data, Google Trends, SERP analysis, competitor analysis, geo/country data, seasonal trends, or wants an SEO report. Covers keyword analysis, ranking tracking, CTR gap analysis, cannibalization detection, content gaps, geo analysis, branded/non-branded split, autocomplete research, and HTML dashboard report generation."
license: MIT
context: fork
---

# SEO Audit Skill — Google Search Console + External Sources

Comprehensive SEO analysis toolkit powered by Google Search Console API data and external sources (Google Trends, Autocomplete). Provides actionable insights about search performance, keyword opportunities, ranking trends, geographic distribution, and competitor landscape.

## Configuration

The user MUST provide a configuration before any analysis can run. Check for a config file at the project root:

**`seo-config.json`** (in the current working directory):
```json
{
  "service_account_file": "path/to/service-account-key.json",
  "site_url": "sc-domain:example.com",
  "site_display_name": "example.com",
  "brand_terms": ["mybrand", "my brand"],
  "relevant_terms": ["topic1", "topic2"],
  "locale": "de"
}
```

Required fields: `service_account_file`, `site_url`, `site_display_name`
Optional fields: `brand_terms` (for branded/non-branded split), `relevant_terms` (for irrelevant traffic detection), `locale` (default "de")

If no `seo-config.json` exists, ask the user for the required fields and create it. Do NOT hardcode credentials.

### Prerequisites
```bash
pip install google-api-python-client google-auth pytrends --break-system-packages
```

## Capabilities

When the user asks for SEO help, choose the appropriate analysis. Combine multiple analyses or run them all at once.

---

### CORE ANALYSES (Google Search Console)

#### 1. Connection Test
**Trigger:** "test connection", "GSC verbinden", "Search Console testen"
Verify service account access. List available properties and permissions.

#### 2. Top Keywords / Search Analytics
**Trigger:** "top keywords", "beste suchanfragen", "search analytics", "welche keywords"
Top search queries for a given period. Clicks, impressions, CTR, average position.
Parameters: period (default 28 days), limit (up to 25000), filters (device, country, page).

#### 3. Weak Rankings / Striking Distance
**Trigger:** "schwache rankings", "weak rankings", "seite 2", "striking distance", "quick wins"
Keywords on page 2+ (position > 10) sorted by impressions.
- Striking Distance (Pos 11-20): nearly page 1
- Page 2-3 (Pos 11-30): realistic with content improvements
- Deep (Pos 30+): need dedicated content

#### 4. Page-Level Analysis
**Trigger:** "seiten analyse", "page analysis", "welche seiten", "page performance"
Performance per URL with keyword mapping. Uses `['page', 'query']` dimensions.

#### 5. CTR Gap Analysis
**Trigger:** "CTR", "click-through rate", "verschenkte klicks", "titel optimieren", "meta description"
Actual CTR vs. industry benchmarks per position. Identifies where better snippets = more clicks.
```
Pos 1: 30%, Pos 2: 18%, Pos 3: 12%, Pos 4: 8%, Pos 5: 6%
Pos 6: 5%, Pos 7: 4%, Pos 8: 3%, Pos 9: 2.5%, Pos 10: 2%
```
Calculate: `missed_clicks = impressions * (expected_ctr - actual_ctr)`

#### 6. Keyword Cannibalization
**Trigger:** "kannibalisierung", "cannibalization", "mehrere seiten gleiches keyword"
Multiple URLs ranking for the same query. Uses `['query', 'page']` dimensions.

#### 7. Content Gaps
**Trigger:** "content gaps", "neue inhalte", "content ideen"
High impressions + poor rankings (pos > 15) + low CTR. Opportunities for new content.

#### 8. Ranking Changes / Trend Analysis
**Trigger:** "trend", "veraenderungen", "verschlechtert", "verbessert", "vergleich", "impact"
Compare two periods (default: 4 weeks vs. 4 weeks before):
- Improved / Declined keywords (position change >= 2)
- New / Disappeared keywords

#### 9. Device Split
**Trigger:** "mobile", "desktop", "tablet", "device", "geraete"
Performance per device. Keywords with significant mobile vs. desktop position differences.

---

### EXTENDED ANALYSES (GSC Advanced Dimensions)

#### 10. Geo / Country Analysis
**Trigger:** "geo", "laender", "countries", "DACH", "international", "wo ranken wir"
Uses `country` dimension for geographic distribution.
- Country-level clicks, impressions, CTR, position
- DACH breakdown (DE, AT, CH) with top keywords per country
- International traffic share

Country codes are ISO 3166-1 alpha-3 lowercase (e.g., `deu`, `aut`, `che`, `usa`, `gbr`).

#### 11. Seasonal Trends
**Trigger:** "saisonal", "seasonal", "monatlich", "jahresvergleich", "winter", "sommer"
Monthly aggregation over 16 months (max GSC history). Shows seasonal patterns.
Combine with Google Trends data for broader context.

#### 12. Long-Tail Discovery
**Trigger:** "long tail", "long-tail", "spezifische keywords", "nischen keywords"
Keywords with 4+ words — specific search intent, easier to rank for.
Also surfaces 3-word combinations as medium-tail opportunities.

#### 13. Branded vs. Non-Branded Split
**Trigger:** "branded", "non-branded", "markenname", "brand awareness"
Separates brand searches from organic discovery. Uses `brand_terms` from config.
Zero branded searches = no brand awareness (needs PR/social/newsletter).

#### 14. Keyword-to-Page Mapping (Intent Mismatches)
**Trigger:** "intent", "mismatch", "welche seite rankt", "mapping", "falsche seite"
Which keywords land on which page? Detects mismatches:
- "garnstärken" landing on /glossar instead of /garnstaerken
- Core keywords landing on /about instead of homepage
These mismatches hurt CTR and conversions.

#### 15. Search Appearance (Rich Results)
**Trigger:** "rich results", "rich snippets", "schema", "structured data", "search appearance"
Uses `searchAppearance` dimension to check if FAQ, Breadcrumb, Product, or other rich results appear in Google.
If empty: schema is not being picked up — validate with Google Rich Results Test.

#### 16. Irrelevant Traffic Detection
**Trigger:** "irrelevant", "falscher traffic", "unpassende keywords"
Identifies keywords unrelated to the site's topic using `relevant_terms` from config.
Helps focus on quality over vanity metrics.

---

### EXTERNAL DATA SOURCES

#### 17. Google Trends
**Trigger:** "google trends", "trends", "saisonalitaet", "suchvolumen", "trend vergleich"
Uses `pytrends` library (no API key needed). Provides:
- Interest over time (12 months) for configurable keywords
- Related/rising queries (content ideas)
- Geographic interest breakdown
- Comparison across keyword variants

```python
from pytrends.request import TrendReq
pytrends = TrendReq(hl='de-DE', tz=360)
pytrends.build_payload(['keyword1', 'keyword2'], timeframe='today 12-m', geo='DE')
trends = pytrends.interest_over_time()
related = pytrends.related_queries()
```

#### 18. Google Autocomplete
**Trigger:** "autocomplete", "vorschlaege", "keyword ideen", "was suchen leute"
Queries Google's autocomplete API for seed keywords. Free, no key needed.
Returns what Google suggests when users start typing — gold for content ideas.

```python
url = f"https://suggestqueries.google.com/complete/search?client=firefox&q={seed}&hl=de&gl=de"
```

Seed keywords should include core terms + partial phrases like "garn ähnlich wie", "garnstärke".

#### 19. SERP Competitor Check
**Trigger:** "wettbewerber", "konkurrenz", "competitor", "wer rankt", "SERP"
For top keywords, check who ranks on page 1. Note: Google may block with CAPTCHA — use respectfully with delays between requests. Alternative: use the user's browser to manually check, or integrate SerpAPI/ValueSERP if API key available.

---

### RECOMMENDATIONS ENGINE

#### 20. Automated Recommendations
**Trigger:** Automatically included in HTML report. Also standalone: "empfehlungen", "was sollen wir tun", "recommendations", "action items", "massnahmen"

The engine analyzes all collected data and derives **prioritized, concrete action items**. Each recommendation includes:
- **Priority level** (Kritisch / Hoch / Mittel / Niedrig) — color-coded left-border cards
- **Problem description** with supporting data
- **📊 Data evidence** — the specific metric that triggered it
- **→ Concrete action** — exactly what to do

Recommendations generated from these patterns:

| Priority | Trigger Condition | Recommendation |
|----------|------------------|----------------|
| Kritisch | CTR < benchmark for keywords with impressions >= 3 | Optimize title tags and meta descriptions, calculate missed clicks |
| Kritisch | Keywords land on wrong page (intent mismatch) | Fix internal linking, canonical tags, content consolidation |
| Hoch | searchAppearance dimension returns 0 results | Validate JSON-LD schema via Rich Results Test |
| Hoch | 0 branded searches detected | Build brand awareness (social, newsletters, communities) |
| Hoch | Keywords in position 11-20 with impressions | Push to page 1 via internal links + content optimization |
| Hoch | Multiple URLs rank for same keyword | Consolidate via canonical/redirect, differentiate content |
| Mittel | High impressions + position > 15 + CTR < 2% | Create dedicated landing pages or blog posts |
| Mittel | Non-DACH traffic share > 15% | Optimize EN pages with standalone meta/H1, check hreflang |
| Mittel | Long-tail keywords (4+ words) in top 5 | Expand with dedicated blog articles per keyword |
| Mittel | Keywords declined > 2 positions | Update content, audit internal links, analyze competitors |
| Niedrig | Seasonal peaks detected in Google Trends | Prepare content 4-6 weeks before peak season |
| Niedrig | Autocomplete suggestions not covered by existing content | Use as basis for new blog/FAQ content |

The engine is **data-driven** — recommendations appear/disappear based on current data. If CTR improves, that recommendation drops. If new cannibalization appears, it gets flagged.

---

### REPORTS & DASHBOARDS

#### 21. Full SEO Audit (Terminal)
**Trigger:** "audit", "vollstaendige analyse", "alles analysieren", "full audit"
Run all applicable analyses in sequence with terminal output.

#### 22. HTML Dashboard Report
**Trigger:** "report", "bericht", "html", "dashboard", "visualisierung"

Dark-theme HTML dashboard with all sections:

**Data Sections:**
- KPI cards (clicks, impressions, CTR, position) with trend arrows
- Traffic trend chart (Chart.js, 8 weeks)
- Geo / country analysis with DACH breakdown
- Striking distance keywords with impression bars
- CTR gap analysis with missed clicks calculation
- Keyword cannibalization groups
- Content gaps
- Keyword movements (improved / declined / new / disappeared)
- Device split + Branded vs. Non-Branded (side-by-side)
- Seasonal trends (monthly aggregation, up to 16 months)
- Keyword → page mapping with ⚠ mismatch warnings
- Search appearance (Rich Results status)
- Long-tail keywords + Google Autocomplete ideas (side-by-side)
- Google Trends chart (12 months) with related/rising queries

**Recommendations Section:**
- Prioritized action items derived from all data above
- Color-coded cards: red border = critical, orange = high, blue = medium, green = low
- Each card: title + priority badge, problem description, 📊 data evidence, → concrete action
- Dynamically generated — adapts to current data on every run

**Summary Grid:**
- 10 color-coded metric tiles at a glance

Output: `reports/seo-report-YYYYMMDD-HHMM.html` + `reports/latest.html`

---

## Implementation Pattern

All scripts follow this pattern:

```python
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

with open('seo-config.json') as f:
    config = json.load(f)

SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']
credentials = service_account.Credentials.from_service_account_file(
    config['service_account_file'], scopes=SCOPES
)
service = build('searchconsole', 'v1', credentials=credentials)
SITE_URL = config['site_url']
```

### GSC Query Helper
```python
def query_gsc(dimensions, start, end, row_limit=25000, filters=None, device=None):
    body = {
        'startDate': start, 'endDate': end,
        'dimensions': dimensions, 'rowLimit': row_limit,
    }
    filter_list = []
    if device:
        filter_list.append({'dimension': 'device', 'expression': device})
    if filters:
        filter_list.extend(filters)
    if filter_list:
        body['dimensionFilterGroups'] = [{'filters': filter_list}]
    return service.searchanalytics().query(
        siteUrl=SITE_URL, body=body
    ).execute().get('rows', [])
```

### API Reference
- Dimensions: `query`, `page`, `device`, `country`, `date`, `searchAppearance`
- Combinable: `['query', 'page']`, `['date', 'device']`, `['query', 'country']`, etc.
- Max 25,000 rows per request
- Data delay: 2-3 days
- History: up to 16 months
- Rate limit: 1,200 queries/minute

## Response Style

- Well-formatted tables (terminal) or styled HTML (report)
- Sort by most actionable metric (impressions for opportunities, position change for trends)
- Concrete recommendations with each analysis, not just data dumps
- German output when user communicates in German
- Include specific URLs/pages so user can act immediately
- Color-code changes: green = improved, red = declined
- Flag mismatches and anomalies prominently

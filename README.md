# SEO Audit Toolkit

Comprehensive SEO analysis and reporting using Google Search Console API, Google Trends, and Google Autocomplete.

## Setup

1. Install dependencies:
   ```bash
   pip install google-api-python-client google-auth pytrends
   ```

2. Create a Google Cloud service account with Search Console API access

3. Copy and configure:
   ```bash
   cp seo-config.example.json seo-config.json
   # Edit seo-config.json with your credentials and site URL
   ```

## Scripts

| Script | Description |
|--------|-------------|
| `test_connection.py` | Verify GSC API connection and list properties |
| `search_analytics.py` | Top search queries for a given period |
| `weak_rankings.py` | Keywords ranking on page 2+ (position > 10) |
| `page_analysis.py` | Page-level performance with keyword mapping |
| `seo_impact.py` | Before/after comparison of SEO changes |
| `seo_audit.py` | Full terminal audit (striking distance, CTR gaps, cannibalization, etc.) |
| `seo_deep_analysis.py` | Extended analyses (geo, seasonal, long-tail, branded, intent mismatches) |
| `seo_external.py` | External data (Google Trends, Autocomplete, SERP check) |
| `seo_report.py` | **HTML dashboard report** with all analyses + recommendations |

## HTML Report

```bash
python3 seo_report.py
```

Generates `reports/latest.html` — a dark-theme dashboard with:
- KPI cards with trend comparison
- Traffic trend chart
- 15 data analysis sections
- Automated recommendations engine (prioritized action items)
- Summary grid

## Claude Code Skill

This toolkit is also available as a Claude Code skill at `~/.claude/skills/seo-audit/`.
In any project with a `seo-config.json`, just ask Claude about SEO and the skill triggers automatically.

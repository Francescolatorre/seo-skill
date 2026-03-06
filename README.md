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

This toolkit includes a Claude Code skill that lets you run all analyses conversationally. Just ask Claude about SEO and it triggers automatically.

### Install the Skill

```bash
# Clone the repo (if you haven't already)
git clone git@github.com:Francescolatorre/seo-skill.git

# Copy the skill definition into your Claude Code skills directory
mkdir -p ~/.claude/skills/seo-audit
cp seo-skill/SKILL.md ~/.claude/skills/seo-audit/SKILL.md
```

Or manually create `~/.claude/skills/seo-audit/SKILL.md` with the content from [`SKILL.md`](https://github.com/Francescolatorre/seo-skill/blob/main/SKILL.md) in this repo.

### Configure Your Project

In any project directory where you want to use the skill, create a `seo-config.json`:

```bash
cp seo-config.example.json /path/to/your/project/seo-config.json
```

Edit it with your Google Search Console credentials:

```json
{
  "service_account_file": "path/to/your-service-account-key.json",
  "site_url": "sc-domain:yourdomain.com",
  "site_display_name": "yourdomain.com",
  "brand_terms": ["yourbrand"],
  "relevant_terms": ["your", "niche", "keywords"],
  "locale": "de"
}
```

### Usage

Once installed, just talk to Claude in any project with a `seo-config.json`:

```
> "mach einen SEO Report"
> "welche Keywords ranken schlecht?"
> "zeig mir die CTR-Lücken"
> "gibt es Keyword-Kannibalisierung?"
> "wie sieht der Traffic nach Ländern aus?"
```

The skill supports 22 analyses — from simple keyword queries to a full HTML dashboard with automated recommendations. See the [SKILL.md](https://github.com/Francescolatorre/seo-skill/blob/main/SKILL.md) for the complete list of triggers.

### Google Search Console Service Account Setup

If you don't have a service account yet:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project (or select existing)
3. Enable the **Google Search Console API**
4. Create a **Service Account** under IAM & Admin → Service Accounts
5. Create a JSON key for the service account and download it
6. In [Google Search Console](https://search.google.com/search-console/), add the service account email as a user (Settings → Users and permissions → Add user) with **Full** or **Restricted** permission

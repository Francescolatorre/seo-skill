from google.oauth2 import service_account
from googleapiclient.discovery import build

SERVICE_ACCOUNT_FILE = 'oleks-488616-4fe597a49127.json'
SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
service = build('searchconsole', 'v1', credentials=credentials)

SITE_URL = 'sc-domain:maschenhub.de'

# 1) Performance nach Seiten
print("=== Performance nach Seiten (Dez 2025 - Feb 2026) ===\n")

response_pages = service.searchanalytics().query(
    siteUrl=SITE_URL,
    body={
        'startDate': '2025-12-01',
        'endDate': '2026-02-28',
        'dimensions': ['page'],
        'rowLimit': 50
    }
).execute()

pages = response_pages.get('rows', [])
pages.sort(key=lambda r: r['impressions'], reverse=True)

print(f"{'Seite':<70} {'Klicks':>7} {'Impr.':>7} {'CTR':>8} {'Pos.':>6}")
print("-" * 100)

for row in pages:
    url = row['keys'][0].replace('https://maschenhub.de', '')
    clicks = row['clicks']
    impressions = row['impressions']
    ctr = row['ctr'] * 100
    position = row['position']
    print(f"{url:<70} {clicks:>7.0f} {impressions:>7.0f} {ctr:>7.1f}% {position:>6.1f}")

# 2) Schwache Keywords pro Seite
print("\n\n=== Schwache Keywords pro Seite (Position > 10) ===\n")

response_detail = service.searchanalytics().query(
    siteUrl=SITE_URL,
    body={
        'startDate': '2025-12-01',
        'endDate': '2026-02-28',
        'dimensions': ['page', 'query'],
        'rowLimit': 500
    }
).execute()

rows = response_detail.get('rows', [])
weak = [r for r in rows if r['position'] > 10]

# Gruppieren nach Seite
from collections import defaultdict
by_page = defaultdict(list)
for row in weak:
    page = row['keys'][0].replace('https://maschenhub.de', '')
    by_page[page].append(row)

# Sortieren nach Gesamtimpressions pro Seite
page_totals = [(page, sum(r['impressions'] for r in kws), kws) for page, kws in by_page.items()]
page_totals.sort(key=lambda x: x[1], reverse=True)

for page, total_impr, keywords in page_totals:
    print(f"--- {page} ({total_impr} Impressionen verschenkt) ---")
    keywords.sort(key=lambda r: r['impressions'], reverse=True)
    for row in keywords[:10]:
        query = row['keys'][1]
        impressions = row['impressions']
        position = row['position']
        print(f"  {query:<45} Impr: {impressions:>5}  Pos: {position:>5.1f}")
    print()

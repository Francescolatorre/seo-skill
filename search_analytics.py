from google.oauth2 import service_account
from googleapiclient.discovery import build

SERVICE_ACCOUNT_FILE = 'oleks-488616-4fe597a49127.json'
SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
service = build('searchconsole', 'v1', credentials=credentials)

SITE_URL = 'sc-domain:maschenhub.de'

# Top Suchanfragen der letzten 28 Tage
response = service.searchanalytics().query(
    siteUrl=SITE_URL,
    body={
        'startDate': '2026-02-01',
        'endDate': '2026-02-28',
        'dimensions': ['query'],
        'rowLimit': 20
    }
).execute()

print("=== Top Suchanfragen (Feb 2026) ===\n")
print(f"{'Suchanfrage':<40} {'Klicks':>7} {'Impressionen':>13} {'CTR':>8} {'Position':>9}")
print("-" * 80)

rows = response.get('rows', [])
if rows:
    for row in rows:
        query = row['keys'][0]
        clicks = row['clicks']
        impressions = row['impressions']
        ctr = row['ctr'] * 100
        position = row['position']
        print(f"{query:<40} {clicks:>7.0f} {impressions:>13.0f} {ctr:>7.1f}% {position:>9.1f}")
else:
    print("Keine Daten fuer diesen Zeitraum gefunden.")

print(f"\nGesamt: {len(rows)} Suchanfragen")

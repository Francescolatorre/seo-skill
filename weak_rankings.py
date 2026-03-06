from google.oauth2 import service_account
from googleapiclient.discovery import build

SERVICE_ACCOUNT_FILE = 'oleks-488616-4fe597a49127.json'
SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
service = build('searchconsole', 'v1', credentials=credentials)

SITE_URL = 'sc-domain:maschenhub.de'

# Alle Suchanfragen der letzten 3 Monate holen
response = service.searchanalytics().query(
    siteUrl=SITE_URL,
    body={
        'startDate': '2025-12-01',
        'endDate': '2026-02-28',
        'dimensions': ['query'],
        'rowLimit': 500
    }
).execute()

rows = response.get('rows', [])

# Nur schlechte Rankings: Position > 10 (= ab Seite 2)
weak = [r for r in rows if r['position'] > 10]
weak.sort(key=lambda r: r['impressions'], reverse=True)

print("=== Schwache Rankings (Position > 10) ===")
print("=== Sortiert nach Impressionen (hohes Potenzial oben) ===\n")
print(f"{'Suchanfrage':<45} {'Klicks':>7} {'Impr.':>7} {'CTR':>8} {'Pos.':>6}")
print("-" * 76)

for row in weak:
    query = row['keys'][0]
    clicks = row['clicks']
    impressions = row['impressions']
    ctr = row['ctr'] * 100
    position = row['position']
    print(f"{query:<45} {clicks:>7.0f} {impressions:>7.0f} {ctr:>7.1f}% {position:>6.1f}")

print(f"\nGesamt: {len(weak)} Keywords mit schwachem Ranking")
print(f"Davon auf Seite 2 (Pos 11-20): {len([r for r in weak if r['position'] <= 20])}")
print(f"Davon auf Seite 3+ (Pos > 20): {len([r for r in weak if r['position'] > 20])}")

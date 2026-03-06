from google.oauth2 import service_account
from googleapiclient.discovery import build

SERVICE_ACCOUNT_FILE = 'oleks-488616-4fe597a49127.json'
SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
service = build('searchconsole', 'v1', credentials=credentials)

SITE_URL = 'sc-domain:maschenhub.de'

# PR #92 (SEO Phase 2) wurde am 24. Feb gemergt, unsere H1/Meta-Fixes am 5. Maerz
# Vergleich: 3 Wochen vorher vs. letzte Woche

periods = {
    'Vorher (10.-23. Feb)': ('2026-02-10', '2026-02-23'),
    'Nach PR#92 (24. Feb - 1. Maerz)': ('2026-02-24', '2026-03-01'),
    'Aktuell (2.-6. Maerz)': ('2026-03-02', '2026-03-06'),
}

# 1. Gesamtueberblick pro Zeitraum
print("=" * 70)
print("GESAMTUEBERBLICK - Klicks, Impressionen, CTR, Position")
print("=" * 70)

for label, (start, end) in periods.items():
    response = service.searchanalytics().query(
        siteUrl=SITE_URL,
        body={
            'startDate': start,
            'endDate': end,
            'dimensions': ['date'],
            'rowLimit': 25000
        }
    ).execute()
    rows = response.get('rows', [])
    total_clicks = sum(r['clicks'] for r in rows)
    total_impressions = sum(r['impressions'] for r in rows)
    days = len(rows) if rows else 1
    avg_ctr = (total_clicks / total_impressions * 100) if total_impressions else 0
    avg_pos = sum(r['position'] for r in rows) / days if rows else 0

    print(f"\n{label}:")
    print(f"  Klicks:       {total_clicks:>6.0f}  ({total_clicks/days:.1f}/Tag)")
    print(f"  Impressionen: {total_impressions:>6.0f}  ({total_impressions/days:.1f}/Tag)")
    print(f"  CTR:          {avg_ctr:>6.1f}%")
    print(f"  Avg Position: {avg_pos:>6.1f}")

# 2. Top-Queries Vergleich: vorher vs. jetzt
print("\n" + "=" * 70)
print("TOP QUERIES - Vorher vs. Aktuell")
print("=" * 70)

query_data = {}
for label, (start, end) in [('vorher', ('2026-02-10', '2026-02-23')),
                              ('aktuell', ('2026-02-24', '2026-03-06'))]:
    response = service.searchanalytics().query(
        siteUrl=SITE_URL,
        body={
            'startDate': start,
            'endDate': end,
            'dimensions': ['query'],
            'rowLimit': 100
        }
    ).execute()
    for row in response.get('rows', []):
        q = row['keys'][0]
        if q not in query_data:
            query_data[q] = {}
        query_data[q][label] = {
            'clicks': row['clicks'],
            'impressions': row['impressions'],
            'ctr': row['ctr'] * 100,
            'position': row['position']
        }

# Queries die in beiden Zeitraeumen vorkommen
both = {q: d for q, d in query_data.items() if 'vorher' in d and 'aktuell' in d}

# Sortiert nach groesstem Positions-Gewinn
print(f"\n{'Suchanfrage':<35} {'Pos vorher':>10} {'Pos jetzt':>10} {'Diff':>7} {'Impr v':>7} {'Impr j':>7}")
print("-" * 90)

sorted_queries = sorted(both.items(), key=lambda x: x[1]['vorher']['position'] - x[1]['aktuell']['position'], reverse=True)
for q, d in sorted_queries[:25]:
    pos_before = d['vorher']['position']
    pos_after = d['aktuell']['position']
    diff = pos_before - pos_after  # positiv = besser
    imp_before = d['vorher']['impressions']
    imp_after = d['aktuell']['impressions']
    arrow = "+" if diff > 0 else ""
    print(f"{q:<35} {pos_before:>10.1f} {pos_after:>10.1f} {arrow}{diff:>6.1f} {imp_before:>7.0f} {imp_after:>7.0f}")

# 3. Seiten-Performance
print("\n" + "=" * 70)
print("SEITEN-PERFORMANCE - Vorher vs. Aktuell")
print("=" * 70)

page_data = {}
for label, (start, end) in [('vorher', ('2026-02-10', '2026-02-23')),
                              ('aktuell', ('2026-02-24', '2026-03-06'))]:
    response = service.searchanalytics().query(
        siteUrl=SITE_URL,
        body={
            'startDate': start,
            'endDate': end,
            'dimensions': ['page'],
            'rowLimit': 50
        }
    ).execute()
    for row in response.get('rows', []):
        p = row['keys'][0]
        if p not in page_data:
            page_data[p] = {}
        page_data[p][label] = {
            'clicks': row['clicks'],
            'impressions': row['impressions'],
            'ctr': row['ctr'] * 100,
            'position': row['position']
        }

both_pages = {p: d for p, d in page_data.items() if 'vorher' in d and 'aktuell' in d}
sorted_pages = sorted(both_pages.items(), key=lambda x: x[1]['aktuell']['impressions'], reverse=True)

print(f"\n{'Seite':<55} {'Klicks v/j':>11} {'Impr v/j':>13} {'Pos v/j':>12}")
print("-" * 95)
for p, d in sorted_pages[:15]:
    short = p.replace('https://www.maschenhub.de', '')
    cv = d['vorher']['clicks']
    ca = d['aktuell']['clicks']
    iv = d['vorher']['impressions']
    ia = d['aktuell']['impressions']
    pv = d['vorher']['position']
    pa = d['aktuell']['position']
    print(f"{short:<55} {cv:>4.0f}/{ca:<5.0f} {iv:>5.0f}/{ia:<6.0f} {pv:>5.1f}/{pa:<5.1f}")

# 4. Neue Queries (nur in aktuellem Zeitraum)
new_queries = {q: d for q, d in query_data.items() if 'aktuell' in d and 'vorher' not in d}
if new_queries:
    print("\n" + "=" * 70)
    print("NEUE QUERIES (erst seit kurzem sichtbar)")
    print("=" * 70)
    sorted_new = sorted(new_queries.items(), key=lambda x: x[1]['aktuell']['impressions'], reverse=True)
    print(f"\n{'Suchanfrage':<40} {'Klicks':>7} {'Impr':>7} {'CTR':>8} {'Position':>9}")
    print("-" * 75)
    for q, d in sorted_new[:15]:
        a = d['aktuell']
        print(f"{q:<40} {a['clicks']:>7.0f} {a['impressions']:>7.0f} {a['ctr']:>7.1f}% {a['position']:>9.1f}")

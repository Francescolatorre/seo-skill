"""
Umfassendes SEO-Audit aus Google Search Console Daten
=====================================================
1. Striking Distance Keywords (Position 11-20, Quick Wins)
2. CTR Gap Analysis (erwartete vs. tatsaechliche CTR)
3. Keyword Cannibalization (mehrere URLs fuer gleichen Query)
4. Content Gaps (hohe Impressionen, keine dedizierte Seite)
5. Declining Keywords (Ranking-Verluste erkennen)
6. Device-Split (Mobile vs. Desktop)
"""

from google.oauth2 import service_account
from googleapiclient.discovery import build
from collections import defaultdict

SERVICE_ACCOUNT_FILE = 'oleks-488616-4fe597a49127.json'
SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
service = build('searchconsole', 'v1', credentials=credentials)

SITE_URL = 'sc-domain:maschenhub.de'

# Zeitraeume: 4 Wochen vorher vs. 4 Wochen aktuell
PERIOD_OLD = ('2026-01-27', '2026-02-16')
PERIOD_NEW = ('2026-02-17', '2026-03-06')


def query_gsc(dimensions, start, end, row_limit=25000, device=None):
    """GSC API Query Helper."""
    body = {
        'startDate': start,
        'endDate': end,
        'dimensions': dimensions,
        'rowLimit': row_limit,
    }
    if device:
        body['dimensionFilterGroups'] = [{
            'filters': [{'dimension': 'device', 'expression': device}]
        }]
    response = service.searchanalytics().query(
        siteUrl=SITE_URL, body=body
    ).execute()
    return response.get('rows', [])


def print_header(title):
    print(f"\n{'=' * 90}")
    print(f"  {title}")
    print(f"{'=' * 90}")


# ============================================================
# 1. STRIKING DISTANCE KEYWORDS (Position 11-20)
# ============================================================
print_header("1. STRIKING DISTANCE KEYWORDS (Position 11-20 = Seite 2)")
print("   Diese Keywords sind fast auf Seite 1 — kleine Optimierungen koennen grossen Impact haben.\n")

rows = query_gsc(['query'], *PERIOD_NEW)
striking = [r for r in rows if 11 <= r['position'] <= 20]
striking.sort(key=lambda r: r['impressions'], reverse=True)

print(f"{'Suchanfrage':<45} {'Klicks':>7} {'Impr':>7} {'CTR':>8} {'Position':>9}")
print("-" * 80)
for r in striking[:20]:
    q = r['keys'][0]
    print(f"{q:<45} {r['clicks']:>7.0f} {r['impressions']:>7.0f} {r['ctr']*100:>7.1f}% {r['position']:>9.1f}")

if not striking:
    print("  Keine Keywords in Position 11-20 gefunden.")
print(f"\n  Gesamt: {len(striking)} Keywords in Striking Distance")


# ============================================================
# 2. CTR GAP ANALYSIS (Erwartete vs. tatsaechliche CTR)
# ============================================================
print_header("2. CTR GAP ANALYSIS (Verschenkte Klicks)")
print("   Keywords wo die CTR unter dem Benchmark liegt — Titel/Meta-Description optimieren.\n")

# Branchenuebliche CTR-Benchmarks nach Position (konservativ)
CTR_BENCHMARKS = {
    1: 0.30, 2: 0.18, 3: 0.12, 4: 0.08, 5: 0.06,
    6: 0.05, 7: 0.04, 8: 0.03, 9: 0.025, 10: 0.02,
}

rows = query_gsc(['query'], *PERIOD_NEW)
ctr_gaps = []
for r in rows:
    pos = int(round(r['position']))
    if pos < 1 or pos > 10:
        continue
    expected_ctr = CTR_BENCHMARKS.get(pos, 0.02)
    actual_ctr = r['ctr']
    gap = expected_ctr - actual_ctr
    expected_clicks = r['impressions'] * expected_ctr
    missed_clicks = expected_clicks - r['clicks']
    if gap > 0.01 and r['impressions'] >= 3:
        ctr_gaps.append({
            'query': r['keys'][0],
            'position': r['position'],
            'impressions': r['impressions'],
            'actual_ctr': actual_ctr * 100,
            'expected_ctr': expected_ctr * 100,
            'gap': gap * 100,
            'missed_clicks': missed_clicks,
        })

ctr_gaps.sort(key=lambda x: x['missed_clicks'], reverse=True)

print(f"{'Suchanfrage':<40} {'Pos':>5} {'Impr':>6} {'CTR ist':>8} {'CTR soll':>9} {'Luecke':>7} {'Verpasst':>9}")
print("-" * 90)
for g in ctr_gaps[:20]:
    print(f"{g['query']:<40} {g['position']:>5.1f} {g['impressions']:>6.0f} {g['actual_ctr']:>7.1f}% {g['expected_ctr']:>8.1f}% {g['gap']:>6.1f}% {g['missed_clicks']:>8.1f}")

if not ctr_gaps:
    print("  Keine signifikanten CTR-Luecken gefunden.")
print(f"\n  Gesamt: {len(ctr_gaps)} Keywords mit CTR unter Benchmark")
if ctr_gaps:
    total_missed = sum(g['missed_clicks'] for g in ctr_gaps)
    print(f"  Geschaetzte verpasste Klicks: {total_missed:.0f}")


# ============================================================
# 3. KEYWORD CANNIBALIZATION
# ============================================================
print_header("3. KEYWORD CANNIBALIZATION")
print("   Queries fuer die mehrere Seiten ranken — die konkurrieren gegeneinander.\n")

rows = query_gsc(['query', 'page'], *PERIOD_NEW)

# Gruppiere nach Query
query_pages = defaultdict(list)
for r in rows:
    query_pages[r['keys'][0]].append({
        'page': r['keys'][1],
        'clicks': r['clicks'],
        'impressions': r['impressions'],
        'position': r['position'],
        'ctr': r['ctr'],
    })

cannibalized = {q: pages for q, pages in query_pages.items() if len(pages) > 1}

# Sortiert nach Gesamtimpressionen
sorted_cannibal = sorted(
    cannibalized.items(),
    key=lambda x: sum(p['impressions'] for p in x[1]),
    reverse=True
)

for q, pages in sorted_cannibal[:15]:
    total_impr = sum(p['impressions'] for p in pages)
    total_clicks = sum(p['clicks'] for p in pages)
    print(f"\n  Query: \"{q}\" ({total_clicks} Klicks, {total_impr} Impressionen, {len(pages)} URLs)")
    pages.sort(key=lambda p: p['impressions'], reverse=True)
    for p in pages:
        short_url = p['page'].replace('https://www.maschenhub.de', '').replace('https://maschenhub.de', '')
        print(f"    {short_url:<55} Pos {p['position']:>5.1f}  Impr {p['impressions']:>4.0f}  Klicks {p['clicks']:>3.0f}")

if not cannibalized:
    print("  Keine Kannibalisierung gefunden.")
print(f"\n  Gesamt: {len(cannibalized)} Queries mit mehreren rankenden URLs")


# ============================================================
# 4. CONTENT GAPS (Hohe Impressionen, keine passende Seite)
# ============================================================
print_header("4. CONTENT GAPS (Hohe Impressionen, schwache Performance)")
print("   Keywords mit vielen Impressionen aber wenig Klicks — fehlt dedizierter Content?\n")

rows = query_gsc(['query'], *PERIOD_NEW)
content_gaps = [r for r in rows if r['impressions'] >= 3 and r['ctr'] < 0.02 and r['position'] > 15]
content_gaps.sort(key=lambda r: r['impressions'], reverse=True)

print(f"{'Suchanfrage':<45} {'Impr':>7} {'Klicks':>7} {'CTR':>8} {'Position':>9}")
print("-" * 80)
for r in content_gaps[:20]:
    q = r['keys'][0]
    print(f"{q:<45} {r['impressions']:>7.0f} {r['clicks']:>7.0f} {r['ctr']*100:>7.1f}% {r['position']:>9.1f}")

if not content_gaps:
    print("  Keine Content Gaps gefunden.")
print(f"\n  Gesamt: {len(content_gaps)} Keywords mit ungenutztem Potenzial")


# ============================================================
# 5. DECLINING KEYWORDS (Ranking-Verluste)
# ============================================================
print_header("5. DECLINING KEYWORDS (Ranking-Verschlechterungen)")
print("   Keywords die sich verschlechtert haben — fruehzeitig gegensteuern.\n")

rows_old = query_gsc(['query'], *PERIOD_OLD)
rows_new = query_gsc(['query'], *PERIOD_NEW)

old_data = {r['keys'][0]: r for r in rows_old}
new_data = {r['keys'][0]: r for r in rows_new}

# Keywords in beiden Zeitraeumen
both_queries = set(old_data.keys()) & set(new_data.keys())
declines = []
improvements = []

for q in both_queries:
    old = old_data[q]
    new = new_data[q]
    pos_change = new['position'] - old['position']  # positiv = schlechter
    impr_change = new['impressions'] - old['impressions']
    click_change = new['clicks'] - old['clicks']
    if old['impressions'] >= 2 or new['impressions'] >= 2:
        entry = {
            'query': q,
            'pos_old': old['position'],
            'pos_new': new['position'],
            'pos_change': pos_change,
            'impr_old': old['impressions'],
            'impr_new': new['impressions'],
            'impr_change': impr_change,
            'click_change': click_change,
        }
        if pos_change > 2:
            declines.append(entry)
        elif pos_change < -2:
            improvements.append(entry)

declines.sort(key=lambda x: x['pos_change'], reverse=True)
improvements.sort(key=lambda x: x['pos_change'])

print("  VERSCHLECHTERUNGEN (Position gefallen):")
print(f"  {'Suchanfrage':<40} {'Pos alt':>8} {'Pos neu':>8} {'Diff':>7} {'Impr alt':>9} {'Impr neu':>9}")
print("  " + "-" * 85)
for d in declines[:15]:
    print(f"  {d['query']:<40} {d['pos_old']:>8.1f} {d['pos_new']:>8.1f} {d['pos_change']:>+7.1f} {d['impr_old']:>9.0f} {d['impr_new']:>9.0f}")

if not declines:
    print("  Keine signifikanten Verschlechterungen gefunden.")

print(f"\n  VERBESSERUNGEN (Position gestiegen):")
print(f"  {'Suchanfrage':<40} {'Pos alt':>8} {'Pos neu':>8} {'Diff':>7} {'Impr alt':>9} {'Impr neu':>9}")
print("  " + "-" * 85)
for d in improvements[:15]:
    print(f"  {d['query']:<40} {d['pos_old']:>8.1f} {d['pos_new']:>8.1f} {d['pos_change']:>+7.1f} {d['impr_old']:>9.0f} {d['impr_new']:>9.0f}")

if not improvements:
    print("  Keine signifikanten Verbesserungen gefunden.")

# Verschwundene Keywords (vorher da, jetzt weg)
disappeared = set(old_data.keys()) - set(new_data.keys())
disappeared_with_traffic = [
    (q, old_data[q]) for q in disappeared if old_data[q]['impressions'] >= 3
]
disappeared_with_traffic.sort(key=lambda x: x[1]['impressions'], reverse=True)

if disappeared_with_traffic:
    print(f"\n  VERSCHWUNDENE KEYWORDS ({len(disappeared_with_traffic)} mit >= 3 Impressionen vorher):")
    print(f"  {'Suchanfrage':<40} {'Klicks':>7} {'Impr':>7} {'Position':>9}")
    print("  " + "-" * 67)
    for q, d in disappeared_with_traffic[:10]:
        print(f"  {q:<40} {d['clicks']:>7.0f} {d['impressions']:>7.0f} {d['position']:>9.1f}")

# Neue Keywords (jetzt da, vorher nicht)
new_only = set(new_data.keys()) - set(old_data.keys())
new_keywords = [(q, new_data[q]) for q in new_only if new_data[q]['impressions'] >= 2]
new_keywords.sort(key=lambda x: x[1]['impressions'], reverse=True)

if new_keywords:
    print(f"\n  NEUE KEYWORDS ({len(new_keywords)} mit >= 2 Impressionen):")
    print(f"  {'Suchanfrage':<40} {'Klicks':>7} {'Impr':>7} {'Position':>9}")
    print("  " + "-" * 67)
    for q, d in new_keywords[:10]:
        print(f"  {q:<40} {d['clicks']:>7.0f} {d['impressions']:>7.0f} {d['position']:>9.1f}")


# ============================================================
# 6. DEVICE-SPLIT (Mobile vs. Desktop)
# ============================================================
print_header("6. DEVICE-SPLIT (Mobile vs. Desktop)")
print("   Unterschiede in Rankings zwischen Geraetetypen.\n")

for device in ['MOBILE', 'DESKTOP', 'TABLET']:
    rows = query_gsc(['date'], *PERIOD_NEW, device=device)
    if not rows:
        continue
    total_clicks = sum(r['clicks'] for r in rows)
    total_impr = sum(r['impressions'] for r in rows)
    avg_ctr = (total_clicks / total_impr * 100) if total_impr else 0
    avg_pos = sum(r['position'] for r in rows) / len(rows) if rows else 0
    days = len(rows)
    label = {'MOBILE': 'Mobile', 'DESKTOP': 'Desktop', 'TABLET': 'Tablet'}[device]
    print(f"  {label:<10} Klicks: {total_clicks:>5.0f} ({total_clicks/days:.1f}/Tag)  "
          f"Impr: {total_impr:>6.0f} ({total_impr/days:.1f}/Tag)  "
          f"CTR: {avg_ctr:>5.1f}%  Pos: {avg_pos:>5.1f}")

# Device-spezifische Query-Unterschiede
print("\n  Groesste Positions-Unterschiede Mobile vs. Desktop:")

mobile_rows = query_gsc(['query'], *PERIOD_NEW, device='MOBILE')
desktop_rows = query_gsc(['query'], *PERIOD_NEW, device='DESKTOP')

mobile_data = {r['keys'][0]: r for r in mobile_rows}
desktop_data = {r['keys'][0]: r for r in desktop_rows}

both_devices = set(mobile_data.keys()) & set(desktop_data.keys())
device_diffs = []
for q in both_devices:
    m = mobile_data[q]
    d = desktop_data[q]
    diff = m['position'] - d['position']
    total_impr = m['impressions'] + d['impressions']
    if total_impr >= 3:
        device_diffs.append({
            'query': q,
            'mobile_pos': m['position'],
            'desktop_pos': d['position'],
            'diff': diff,
            'mobile_impr': m['impressions'],
            'desktop_impr': d['impressions'],
        })

device_diffs.sort(key=lambda x: abs(x['diff']), reverse=True)

if device_diffs:
    print(f"  {'Suchanfrage':<40} {'Mobile':>8} {'Desktop':>9} {'Diff':>7} {'Impr M':>7} {'Impr D':>7}")
    print("  " + "-" * 82)
    for dd in device_diffs[:10]:
        print(f"  {dd['query']:<40} {dd['mobile_pos']:>8.1f} {dd['desktop_pos']:>9.1f} {dd['diff']:>+7.1f} {dd['mobile_impr']:>7.0f} {dd['desktop_impr']:>7.0f}")
else:
    print("  Nicht genug Daten fuer Device-Vergleich.")


# ============================================================
# ZUSAMMENFASSUNG
# ============================================================
print_header("ZUSAMMENFASSUNG")
print(f"""
  Striking Distance Keywords:   {len(striking):>3} (Position 11-20, schnelle Gewinne)
  CTR-Luecken:                  {len(ctr_gaps):>3} (Titel/Meta optimieren)
  Kannibalisierte Keywords:     {len(cannibalized):>3} (mehrere URLs konkurrieren)
  Content Gaps:                 {len(content_gaps):>3} (neuer Content noetig)
  Verschlechterte Keywords:     {len(declines):>3} (Gegensteuern)
  Verbesserte Keywords:         {len(improvements):>3} (Trend beibehalten)
  Verschwundene Keywords:       {len(disappeared_with_traffic):>3} (untersuchen)
  Neue Keywords:                {len(new_keywords):>3} (Chancen nutzen)
""")

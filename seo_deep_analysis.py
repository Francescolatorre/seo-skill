"""
Deep SEO Analysis — Erweiterte Analysen aus GSC + externen Quellen
==================================================================
1. Geo/Laender-Analyse
2. Saisonale Trends (12+ Monate)
3. Long-Tail Discovery
4. Branded vs. Non-Branded
5. Keyword-zu-Seite Mapping (Intent Mismatches)
6. Search Appearance (Rich Results)
7. Irrelevanter Traffic
"""

import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from collections import defaultdict
from datetime import datetime, timedelta

# Config
with open('seo-config.json') as f:
    config = json.load(f)

SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']
credentials = service_account.Credentials.from_service_account_file(
    config['service_account_file'], scopes=SCOPES
)
service = build('searchconsole', 'v1', credentials=credentials)
SITE_URL = config['site_url']
SITE_NAME = config.get('site_display_name', SITE_URL)

today = datetime.now().date()
end_date = (today - timedelta(days=2)).isoformat()  # GSC Verzoegerung

# Maximaler Zeitraum fuer saisonale Analyse
seasonal_start = (today - timedelta(days=480)).isoformat()  # ~16 Monate
recent_start = (today - timedelta(days=28)).isoformat()


def query_gsc(dimensions, start, end, row_limit=25000, filters=None):
    body = {
        'startDate': start, 'endDate': end,
        'dimensions': dimensions, 'rowLimit': row_limit,
    }
    if filters:
        body['dimensionFilterGroups'] = [{'filters': filters}]
    return service.searchanalytics().query(
        siteUrl=SITE_URL, body=body
    ).execute().get('rows', [])


def header(title):
    print(f"\n{'=' * 90}")
    print(f"  {title}")
    print(f"{'=' * 90}")


# ============================================================
# 1. GEO / LAENDER-ANALYSE
# ============================================================
header("1. GEO / LAENDER-ANALYSE")
print("   In welchen Laendern rankt maschenhub.de?\n")

rows = query_gsc(['country'], recent_start, end_date)
rows.sort(key=lambda r: r['impressions'], reverse=True)

total_impr = sum(r['impressions'] for r in rows)
total_clicks = sum(r['clicks'] for r in rows)

COUNTRY_NAMES = {
    'deu': 'Deutschland', 'aut': 'Oesterreich', 'che': 'Schweiz',
    'usa': 'USA', 'gbr': 'Grossbritannien', 'nld': 'Niederlande',
    'fra': 'Frankreich', 'bel': 'Belgien', 'dnk': 'Daenemark',
    'swe': 'Schweden', 'nor': 'Norwegen', 'fin': 'Finnland',
    'pol': 'Polen', 'ita': 'Italien', 'esp': 'Spanien',
    'can': 'Kanada', 'aus': 'Australien', 'jpn': 'Japan',
    'ind': 'Indien', 'bra': 'Brasilien', 'cze': 'Tschechien',
    'hun': 'Ungarn', 'irl': 'Irland', 'prt': 'Portugal',
    'nzl': 'Neuseeland', 'lux': 'Luxemburg', 'sgp': 'Singapur',
}

print(f"{'Land':<25} {'Klicks':>7} {'Impr':>8} {'Anteil':>8} {'CTR':>8} {'Position':>9}")
print("-" * 70)
for r in rows[:20]:
    code = r['keys'][0]
    name = COUNTRY_NAMES.get(code, code.upper())
    pct = r['impressions'] / total_impr * 100 if total_impr else 0
    ctr = r['ctr'] * 100
    print(f"{name:<25} {r['clicks']:>7.0f} {r['impressions']:>8.0f} {pct:>7.1f}% {ctr:>7.1f}% {r['position']:>9.1f}")

print(f"\nGesamt: {len(rows)} Laender, {total_clicks:.0f} Klicks, {total_impr:.0f} Impressionen")

# Top Keywords pro DACH-Land
for country_code, country_name in [('deu', 'Deutschland'), ('aut', 'Oesterreich'), ('che', 'Schweiz')]:
    rows_c = query_gsc(['query'], recent_start, end_date, row_limit=10,
                       filters=[{'dimension': 'country', 'expression': country_code}])
    if rows_c:
        rows_c.sort(key=lambda r: r['impressions'], reverse=True)
        print(f"\n  Top Keywords in {country_name}:")
        for r in rows_c[:5]:
            print(f"    {r['keys'][0]:<40} Impr {r['impressions']:>4.0f}  Pos {r['position']:>5.1f}")


# ============================================================
# 2. SAISONALE TRENDS
# ============================================================
header("2. SAISONALE TRENDS")
print("   Monatliche Aggregation — gibt es saisonale Muster?\n")

rows = query_gsc(['date'], seasonal_start, end_date)
if rows:
    monthly = defaultdict(lambda: {'clicks': 0, 'impressions': 0, 'pos_sum': 0, 'days': 0})
    for r in rows:
        month_key = r['keys'][0][:7]  # YYYY-MM
        monthly[month_key]['clicks'] += r['clicks']
        monthly[month_key]['impressions'] += r['impressions']
        monthly[month_key]['pos_sum'] += r['position']
        monthly[month_key]['days'] += 1

    print(f"{'Monat':<12} {'Klicks':>8} {'Impr':>9} {'CTR':>8} {'Avg Pos':>9} {'Klicks/Tag':>11}")
    print("-" * 60)
    for month in sorted(monthly.keys()):
        d = monthly[month]
        ctr = (d['clicks'] / d['impressions'] * 100) if d['impressions'] else 0
        avg_pos = d['pos_sum'] / d['days'] if d['days'] else 0
        cpd = d['clicks'] / d['days'] if d['days'] else 0
        # Einfacher Balken
        bar = '#' * min(int(d['impressions'] / 20), 40)
        print(f"{month:<12} {d['clicks']:>8.0f} {d['impressions']:>9.0f} {ctr:>7.1f}% {avg_pos:>9.1f} {cpd:>10.1f}  {bar}")
else:
    print("  Nicht genug historische Daten fuer saisonale Analyse.")


# ============================================================
# 3. LONG-TAIL DISCOVERY
# ============================================================
header("3. LONG-TAIL DISCOVERY")
print("   Keywords mit 4+ Woertern — spezifische Suchabsicht, leichter zu ranken.\n")

rows = query_gsc(['query'], recent_start, end_date)
long_tail = [r for r in rows if len(r['keys'][0].split()) >= 4]
long_tail.sort(key=lambda r: r['impressions'], reverse=True)

# Auch 3-Wort Keywords die interessant sind
medium_tail = [r for r in rows if len(r['keys'][0].split()) == 3]
medium_tail.sort(key=lambda r: r['impressions'], reverse=True)

print(f"{'Long-Tail Keyword (4+ Woerter)':<50} {'Impr':>6} {'Klicks':>7} {'Pos':>7}")
print("-" * 75)
for r in long_tail[:15]:
    print(f"{r['keys'][0]:<50} {r['impressions']:>6.0f} {r['clicks']:>7.0f} {r['position']:>7.1f}")

if not long_tail:
    print("  Keine Long-Tail Keywords gefunden.")

if medium_tail:
    print(f"\n  3-Wort Keywords ({len(medium_tail)} gefunden):")
    for r in medium_tail[:10]:
        print(f"    {r['keys'][0]:<45} Impr {r['impressions']:>4.0f}  Pos {r['position']:>5.1f}")


# ============================================================
# 4. BRANDED vs. NON-BRANDED
# ============================================================
header("4. BRANDED vs. NON-BRANDED")
print("   Wie viel Traffic kommt ueber den Markennamen?\n")

BRAND_TERMS = ['maschenhub', 'maschen hub', 'maschenhub.de']

branded = [r for r in rows if any(b in r['keys'][0].lower() for b in BRAND_TERMS)]
non_branded = [r for r in rows if not any(b in r['keys'][0].lower() for b in BRAND_TERMS)]

branded_clicks = sum(r['clicks'] for r in branded)
branded_impr = sum(r['impressions'] for r in branded)
nb_clicks = sum(r['clicks'] for r in non_branded)
nb_impr = sum(r['impressions'] for r in non_branded)

print(f"  {'Segment':<20} {'Keywords':>9} {'Klicks':>8} {'Impr':>9} {'CTR':>8}")
print("  " + "-" * 58)
bctr = (branded_clicks / branded_impr * 100) if branded_impr else 0
nbctr = (nb_clicks / nb_impr * 100) if nb_impr else 0
print(f"  {'Branded':<20} {len(branded):>9} {branded_clicks:>8.0f} {branded_impr:>9.0f} {bctr:>7.1f}%")
print(f"  {'Non-Branded':<20} {len(non_branded):>9} {nb_clicks:>8.0f} {nb_impr:>9.0f} {nbctr:>7.1f}%")

if branded:
    print(f"\n  Branded Keywords:")
    for r in sorted(branded, key=lambda r: r['impressions'], reverse=True)[:5]:
        print(f"    {r['keys'][0]:<40} Impr {r['impressions']:>4.0f}  Klicks {r['clicks']:>3.0f}  Pos {r['position']:>5.1f}")

print(f"\n  Anteil Non-Branded: {nb_impr/(branded_impr+nb_impr)*100:.1f}% der Impressionen" if (branded_impr + nb_impr) else "")


# ============================================================
# 5. KEYWORD-ZU-SEITE MAPPING (Intent Mismatches)
# ============================================================
header("5. KEYWORD-ZU-SEITE MAPPING")
print("   Welche Keywords landen auf welcher Seite? Gibt es Mismatches?\n")

rows_qp = query_gsc(['query', 'page'], recent_start, end_date)

# Gruppiere: welche Seite rankt fuer welche Keywords
page_keywords = defaultdict(list)
for r in rows_qp:
    page_keywords[r['keys'][1]].append({
        'query': r['keys'][0],
        'clicks': r['clicks'],
        'impressions': r['impressions'],
        'position': r['position'],
    })

# Sortiere Seiten nach Impressionen
sorted_pages = sorted(page_keywords.items(),
                      key=lambda x: sum(k['impressions'] for k in x[1]), reverse=True)

for page, keywords in sorted_pages[:8]:
    short = page.replace('https://www.maschenhub.de', '').replace('https://maschenhub.de', '')
    total_i = sum(k['impressions'] for k in keywords)
    total_c = sum(k['clicks'] for k in keywords)
    keywords.sort(key=lambda k: k['impressions'], reverse=True)
    print(f"\n  {short}  ({total_c} Klicks, {total_i} Impr)")
    for k in keywords[:5]:
        intent_flag = ""
        # Einfache Mismatch-Erkennung
        if 'garnstärk' in k['query'] and '/garnstaerken' not in page:
            intent_flag = " ⚠ MISMATCH (sollte /garnstaerken sein)"
        elif 'glossar' in k['query'] and '/glossar' not in page:
            intent_flag = " ⚠ MISMATCH (sollte /glossar sein)"
        elif 'blog' in k['query'] and '/blog' not in page:
            intent_flag = " ⚠ MISMATCH (sollte /blog sein)"
        elif 'faq' in k['query'] and '/faq' not in page:
            intent_flag = " ⚠ MISMATCH (sollte /faq sein)"
        print(f"    {k['query']:<40} Impr {k['impressions']:>4.0f}  Pos {k['position']:>5.1f}{intent_flag}")


# ============================================================
# 6. SEARCH APPEARANCE
# ============================================================
header("6. SEARCH APPEARANCE (Rich Results)")
print("   Werden Rich Results (FAQ, etc.) angezeigt?\n")

try:
    rows_sa = query_gsc(['searchAppearance'], recent_start, end_date)
    if rows_sa:
        print(f"{'Typ':<35} {'Klicks':>7} {'Impr':>8} {'CTR':>8} {'Position':>9}")
        print("-" * 70)
        rows_sa.sort(key=lambda r: r['impressions'], reverse=True)
        for r in rows_sa:
            ctr = r['ctr'] * 100
            print(f"{r['keys'][0]:<35} {r['clicks']:>7.0f} {r['impressions']:>8.0f} {ctr:>7.1f}% {r['position']:>9.1f}")
    else:
        print("  Keine Search Appearance Daten gefunden.")
        print("  Das bedeutet: Noch keine Rich Results in der Google-Suche.")
        print("  Tipp: FAQ-Schema, Breadcrumb-Schema und Product-Schema koennen helfen.")
except Exception as e:
    print(f"  Fehler: {e}")


# ============================================================
# 7. IRRELEVANTER TRAFFIC
# ============================================================
header("7. IRRELEVANTER TRAFFIC")
print("   Keywords die nichts mit Garn/Stricken zu tun haben.\n")

RELEVANT_TERMS = [
    'garn', 'yarn', 'wolle', 'wool', 'strick', 'knit', 'häkel', 'crochet',
    'nadel', 'needle', 'maschen', 'faser', 'fiber', 'fibre', 'alpaka', 'alpaca',
    'merino', 'cotton', 'baumwoll', 'kaschmir', 'cashmere', 'mohair', 'seide', 'silk',
    'alternative', 'finder', 'vergleich', 'compare', 'similar', 'ersatz',
    'lace', 'fingering', 'sport', 'worsted', 'bulky', 'aran', 'dk',
    'häkeln', 'stricken', 'glossar', 'faq', 'maschenhub',
    'sandnes', 'katia', 'schachenmayr', 'grundl', 'drops', 'lang yarns',
    'peer gynt', 'filcolana',
]

irrelevant = []
for r in rows:
    q = r['keys'][0].lower()
    if not any(term in q for term in RELEVANT_TERMS):
        irrelevant.append(r)

irrelevant.sort(key=lambda r: r['impressions'], reverse=True)

if irrelevant:
    print(f"{'Keyword':<45} {'Impr':>6} {'Klicks':>7} {'Pos':>7}")
    print("-" * 70)
    for r in irrelevant[:15]:
        print(f"{r['keys'][0]:<45} {r['impressions']:>6.0f} {r['clicks']:>7.0f} {r['position']:>7.1f}")
    print(f"\n  Gesamt: {len(irrelevant)} potenziell irrelevante Keywords")
    print(f"  Impressionen: {sum(r['impressions'] for r in irrelevant):.0f}")
else:
    print("  Alle Keywords scheinen relevant zu sein.")


# ============================================================
# ZUSAMMENFASSUNG
# ============================================================
header("ZUSAMMENFASSUNG")

dach_rows = [r for r in query_gsc(['country'], recent_start, end_date)
             if r['keys'][0] in ('deu', 'aut', 'che')]
dach_pct = sum(r['impressions'] for r in dach_rows) / total_impr * 100 if total_impr else 0

print(f"""
  Laender gesamt:         {len(query_gsc(['country'], recent_start, end_date)):>3}
  DACH-Anteil:            {dach_pct:>5.1f}%
  Long-Tail Keywords:     {len(long_tail):>3} (4+ Woerter)
  Branded Keywords:       {len(branded):>3}
  Non-Branded Keywords:   {len(non_branded):>3}
  Irrelevante Keywords:   {len(irrelevant):>3}
  Seiten mit Keywords:    {len(page_keywords):>3}
""")

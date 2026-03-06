"""
Externe SEO-Datenquellen
========================
1. Google Trends — Saisonalitaet und verwandte Suchanfragen
2. SERP-Check — Wer rankt ueber uns fuer unsere Top-Keywords?
3. Google Autocomplete — Long-Tail Ideen
"""

import json
import urllib.request
import urllib.parse
import ssl
import re
from datetime import datetime

# SSL context fuer urllib
ctx = ssl.create_default_context()

def header(title):
    print(f"\n{'=' * 90}")
    print(f"  {title}")
    print(f"{'=' * 90}")


# ============================================================
# 1. GOOGLE TRENDS
# ============================================================
header("1. GOOGLE TRENDS — Saisonalitaet & verwandte Themen")

try:
    from pytrends.request import TrendReq

    pytrends = TrendReq(hl='de-DE', tz=360)

    # Unsere Top-Keywords
    keywords_to_check = [
        'Garn Alternative',
        'Wolle vergleichen',
        'Strickgarn',
        'Garnstärke',
    ]

    print(f"\n  Trend-Vergleich (12 Monate, Deutschland):\n")

    pytrends.build_payload(keywords_to_check, cat=0, timeframe='today 12-m', geo='DE')
    trends = pytrends.interest_over_time()

    if not trends.empty:
        # Monatliche Durchschnitte
        monthly = trends.resample('ME').mean()
        print(f"  {'Monat':<12}", end='')
        for kw in keywords_to_check:
            print(f"  {kw:<20}", end='')
        print()
        print("  " + "-" * (12 + 22 * len(keywords_to_check)))
        for idx, row in monthly.iterrows():
            print(f"  {idx.strftime('%Y-%m'):<12}", end='')
            for kw in keywords_to_check:
                val = row.get(kw, 0)
                bar = '#' * int(val / 5) if val > 0 else '-'
                print(f"  {val:>3.0f} {bar:<15}", end='')
            print()
    else:
        print("  Keine Trend-Daten verfuegbar.")

    # Verwandte Suchanfragen
    print(f"\n  Verwandte Suchanfragen (rising):")
    pytrends.build_payload(['Garn Alternative'], cat=0, timeframe='today 12-m', geo='DE')
    related = pytrends.related_queries()

    if 'Garn Alternative' in related and related['Garn Alternative']['rising'] is not None:
        rising = related['Garn Alternative']['rising']
        print(f"\n  {'Suchanfrage':<45} {'Anstieg':>10}")
        print("  " + "-" * 58)
        for _, row in rising.head(10).iterrows():
            print(f"  {row['query']:<45} {row['value']:>10}")
    else:
        print("  Keine rising queries gefunden.")

    if 'Garn Alternative' in related and related['Garn Alternative']['top'] is not None:
        top = related['Garn Alternative']['top']
        print(f"\n  Top verwandte Suchanfragen:")
        print(f"  {'Suchanfrage':<45} {'Relevanz':>10}")
        print("  " + "-" * 58)
        for _, row in top.head(10).iterrows():
            print(f"  {row['query']:<45} {row['value']:>10}")

except ImportError:
    print("  pytrends nicht installiert. Ueberspringe Google Trends.")
except Exception as e:
    print(f"  Google Trends Fehler: {e}")


# ============================================================
# 2. GOOGLE AUTOCOMPLETE — Keyword-Ideen
# ============================================================
header("2. GOOGLE AUTOCOMPLETE — Keyword-Ideen")
print("   Was schlaegt Google fuer unsere Kern-Keywords vor?\n")

SEED_KEYWORDS = [
    'garn alternative',
    'wolle vergleichen',
    'garnstärke',
    'strickgarn ersatz',
    'yarn finder',
    'garn ähnlich wie',
]

for seed in SEED_KEYWORDS:
    try:
        url = f"https://suggestqueries.google.com/complete/search?client=firefox&q={urllib.parse.quote(seed)}&hl=de&gl=de"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            suggestions = data[1] if len(data) > 1 else []
            if suggestions:
                print(f"  \"{seed}\":")
                for s in suggestions[:6]:
                    if s.lower() != seed.lower():
                        print(f"    → {s}")
                print()
    except Exception as e:
        print(f"  \"{seed}\": Fehler ({e})")


# ============================================================
# 3. SERP-CHECK — Wer rankt fuer unsere Top-Keywords?
# ============================================================
header("3. SERP-CHECK — Wettbewerber-Analyse")
print("   Wer rankt auf Seite 1 fuer unsere wichtigsten Keywords?\n")
print("   (Hinweis: Nutzt Google-Suche direkt, kann rate-limited sein)\n")

TOP_KEYWORDS = [
    'garnalternativen finden',
    'garn alternative finden',
    'yarn alternative finder',
    'garnstärken tabelle',
]

for kw in TOP_KEYWORDS:
    try:
        encoded = urllib.parse.quote(kw)
        url = f"https://www.google.de/search?q={encoded}&hl=de&gl=de&num=10"
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'de-DE,de;q=0.9',
        })
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')

        # Einfacher URL-Extraktor aus Google-Ergebnissen
        # Sucht nach /url?q= Pattern
        urls = re.findall(r'/url\?q=(https?://[^&"]+)', html)
        # Alternativ: direkte URLs in cite-Tags oder Ergebnis-Links
        if not urls:
            urls = re.findall(r'<a href="(https?://(?!www\.google)[^"]+)"', html)

        # Filtern: nur echte Ergebnisse, keine Google-internen Links
        clean_urls = []
        seen_domains = set()
        for u in urls:
            u = urllib.parse.unquote(u).split('&')[0]
            if any(skip in u for skip in ['google.com', 'google.de', 'gstatic', 'youtube.com', 'schema.org']):
                continue
            domain = urllib.parse.urlparse(u).netloc
            if domain not in seen_domains:
                seen_domains.add(domain)
                clean_urls.append(u)

        print(f"  \"{kw}\":")
        if clean_urls:
            our_pos = None
            for i, u in enumerate(clean_urls[:10], 1):
                is_ours = 'maschenhub' in u
                marker = " ◀ WIR" if is_ours else ""
                if is_ours:
                    our_pos = i
                domain = urllib.parse.urlparse(u).netloc
                path = urllib.parse.urlparse(u).path[:40]
                print(f"    {i:>2}. {domain}{path}{marker}")
            if our_pos:
                print(f"    → Unsere Position: #{our_pos}")
            else:
                print(f"    → maschenhub.de nicht in Top 10 gefunden")
        else:
            print(f"    Konnte keine Ergebnisse parsen (evtl. CAPTCHA/Rate-Limit)")
        print()

        import time
        time.sleep(2)  # Rate-Limiting

    except Exception as e:
        print(f"  \"{kw}\": Fehler ({e})")


# ============================================================
# ZUSAMMENFASSUNG & EMPFEHLUNGEN
# ============================================================
header("EMPFEHLUNGEN AUS DER ANALYSE")
print("""
  SOFORT UMSETZBAR:
  ─────────────────
  1. Rich Results aktivieren
     → FAQ-Schema ist auf /faq und /glossar implementiert, aber Google zeigt
       keine Rich Results an. Pruefen ob das Schema korrekt validiert
       (Google Rich Results Test).

  2. /de/about rankt fuer Kern-Keywords
     → "garnalternativen finden" landet auf /de/about statt auf der Startseite
     → Interne Verlinkung und Canonical-Tags pruefen

  3. Garnstaerken-Mismatch beheben
     → "garnstärken" und "garnstärken tabelle" landen auf /glossar
       statt auf /garnstaerken. Interne Verlinkung verstaerken,
       ggf. Redirect oder Canonical setzen.

  4. Brand Awareness = 0
     → Kein einziger Branded Search. Newsletter, Social Media,
       oder PR koennte helfen den Brand aufzubauen.

  MITTELFRISTIG:
  ──────────────
  5. Internationale Keywords bedienen
     → 27% der Impressionen kommen von ausserhalb DACH
     → EN-Version staerker optimieren (yarn finder, yarn alternative)

  6. Long-Tail Content erstellen
     → Spezifische Garn-Vergleiche als Blog-Artikel:
       "Tynn Peer Gynt Alternative", "Alafoss Lopi Alternative"
     → Diese Keywords ranken bereits auf Pos 2-5!

  7. Google Autocomplete-Ideen nutzen
     → Neue Content-Ideen aus den Autocomplete-Vorschlaegen ableiten
""")

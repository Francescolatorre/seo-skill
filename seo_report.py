"""
SEO Audit HTML Report Generator — Full Edition
================================================
Generates a comprehensive dark-theme HTML dashboard from GSC + external data.

Sections:
 1. KPI Overview with trend
 2. Traffic Trend Chart (8 weeks)
 3. Geo / Country Analysis
 4. Striking Distance Keywords
 5. CTR Gap Analysis
 6. Keyword Cannibalization
 7. Content Gaps
 8. Keyword Movements (improved/declined/new/disappeared)
 9. Device Split
10. Seasonal Trends
11. Branded vs Non-Branded
12. Keyword-to-Page Mapping & Intent Mismatches
13. Search Appearance (Rich Results)
14. Long-Tail Discovery
15. Google Autocomplete Ideas
16. Summary
"""

import json
import html as html_mod
import os
import urllib.request
import urllib.parse
import ssl
from google.oauth2 import service_account
from googleapiclient.discovery import build
from collections import defaultdict
from datetime import datetime, timedelta

# ── Config ──────────────────────────────────────────────────
with open('seo-config.json') as f:
    config = json.load(f)

SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']
credentials = service_account.Credentials.from_service_account_file(
    config['service_account_file'], scopes=SCOPES
)
service = build('searchconsole', 'v1', credentials=credentials)
SITE_URL = config['site_url']
SITE_DISPLAY = config.get('site_display_name', SITE_URL)
BRAND_TERMS = [t.lower() for t in config.get('brand_terms', [SITE_DISPLAY.split('.')[0]])]
RELEVANT_TERMS = [t.lower() for t in config.get('relevant_terms', [])]

# ── Time periods ────────────────────────────────────────────
today = datetime.now().date()
P_NEW_END = (today - timedelta(days=2)).isoformat()
P_NEW_START = (today - timedelta(days=29)).isoformat()
P_OLD_END = (today - timedelta(days=30)).isoformat()
P_OLD_START = (today - timedelta(days=57)).isoformat()
SEASONAL_START = (today - timedelta(days=480)).isoformat()

CTR_BENCH = {1:.30, 2:.18, 3:.12, 4:.08, 5:.06, 6:.05, 7:.04, 8:.03, 9:.025, 10:.02}

COUNTRY_NAMES = {
    'deu':'Deutschland','aut':'Österreich','che':'Schweiz','usa':'USA',
    'gbr':'UK','nld':'Niederlande','fra':'Frankreich','bel':'Belgien',
    'dnk':'Dänemark','swe':'Schweden','nor':'Norwegen','fin':'Finnland',
    'pol':'Polen','ita':'Italien','esp':'Spanien','can':'Kanada',
    'aus':'Australien','irl':'Irland','cze':'Tschechien','hun':'Ungarn',
    'prt':'Portugal','lux':'Luxemburg','bra':'Brasilien','jpn':'Japan',
    'ind':'Indien','nzl':'Neuseeland','sgp':'Singapur',
}


def qgsc(dims, s, e, lim=25000, filters=None, device=None):
    body = {'startDate':s,'endDate':e,'dimensions':dims,'rowLimit':lim}
    fl = []
    if device: fl.append({'dimension':'device','expression':device})
    if filters: fl.extend(filters)
    if fl: body['dimensionFilterGroups'] = [{'filters':fl}]
    return service.searchanalytics().query(siteUrl=SITE_URL,body=body).execute().get('rows',[])


def esc(t): return html_mod.escape(str(t))
def short_url(u): return u.replace('https://www.'+SITE_DISPLAY,'').replace('https://'+SITE_DISPLAY,'')

def pos_arrow(v):
    if v > 0: return f'<span class="red">+{v:.1f} ↓</span>'
    if v < 0: return f'<span class="green">{v:.1f} ↑</span>'
    return '<span class="muted">—</span>'

def val_arrow(v):
    if v > 0: return f'<span class="green">+{v:.1f} ↑</span>'
    if v < 0: return f'<span class="red">{v:.1f} ↓</span>'
    return '<span class="muted">—</span>'

def bar_html(val, mx, color='var(--blue)'):
    pct = min(val/mx*100,100) if mx else 0
    return f'<div class="bar-bg"><div class="bar-fill" style="width:{pct:.0f}%;background:{color}"></div></div>'

def badge(text, v='default'):
    return f'<span class="badge badge-{v}">{esc(text)}</span>'

def tbl(headers, rows_data, aligns=None):
    """Generate a table. aligns: list of 'l' or 'r'."""
    if not aligns: aligns = ['l'] * len(headers)
    h = '<table><tr>' + ''.join(f'<th class="{"num" if a=="r" else ""}">{h}</th>' for h, a in zip(headers, aligns)) + '</tr>'
    for row in rows_data:
        h += '<tr>' + ''.join(f'<td class="{"num" if aligns[i]=="r" else ""}">{c}</td>' for i, c in enumerate(row)) + '</tr>'
    return h + '</table>'


# ── Data Collection ─────────────────────────────────────────
print("Daten werden geladen...")

# Overview
overview = {}
for label, s, e in [('old',P_OLD_START,P_OLD_END),('new',P_NEW_START,P_NEW_END)]:
    rows = qgsc(['date'],s,e)
    tc=sum(r['clicks'] for r in rows); ti=sum(r['impressions'] for r in rows)
    d=len(rows) or 1
    overview[label] = {'clicks':tc,'impressions':ti,
        'ctr':(tc/ti*100) if ti else 0,
        'position':sum(r['position'] for r in rows)/d if rows else 0,
        'days':d,'cpd':tc/d,'ipd':ti/d}

# Daily trend
daily = sorted(qgsc(['date'],P_OLD_START,P_NEW_END), key=lambda r:r['keys'][0])

# Queries
q_new = qgsc(['query'],P_NEW_START,P_NEW_END)
q_old = qgsc(['query'],P_OLD_START,P_OLD_END)
qn = {r['keys'][0]:r for r in q_new}
qo = {r['keys'][0]:r for r in q_old}

# Query+Page
qp = qgsc(['query','page'],P_NEW_START,P_NEW_END)

# Pages
p_new = sorted(qgsc(['page'],P_NEW_START,P_NEW_END), key=lambda r:r['impressions'], reverse=True)

# Countries
countries = sorted(qgsc(['country'],P_NEW_START,P_NEW_END), key=lambda r:r['impressions'], reverse=True)
total_country_impr = sum(r['impressions'] for r in countries)

# Seasonal
seasonal_rows = sorted(qgsc(['date'],SEASONAL_START,P_NEW_END), key=lambda r:r['keys'][0])

# Devices
dev_data = {}
for dv in ['MOBILE','DESKTOP','TABLET']:
    rows = qgsc(['date'],P_NEW_START,P_NEW_END,device=dv)
    if rows:
        tc=sum(r['clicks'] for r in rows); ti=sum(r['impressions'] for r in rows)
        dev_data[dv]={'clicks':tc,'impressions':ti,'ctr':(tc/ti*100) if ti else 0,
                      'position':sum(r['position'] for r in rows)/len(rows)}

# Search Appearance
sa_rows = []
try: sa_rows = qgsc(['searchAppearance'],P_NEW_START,P_NEW_END)
except: pass

# ── Computed Analyses ───────────────────────────────────────
print("Analysen werden berechnet...")

# Striking Distance
striking = sorted([r for r in q_new if 11<=r['position']<=20], key=lambda r:r['impressions'], reverse=True)

# CTR Gaps
ctr_gaps = []
for r in q_new:
    pos=int(round(r['position']))
    if 1<=pos<=10:
        exp=CTR_BENCH.get(pos,0.02); gap=exp-r['ctr']; miss=r['impressions']*exp-r['clicks']
        if gap>0.01 and r['impressions']>=3:
            ctr_gaps.append({'q':r['keys'][0],'pos':r['position'],'impr':r['impressions'],
                'act':r['ctr']*100,'exp':exp*100,'gap':gap*100,'miss':miss})
ctr_gaps.sort(key=lambda x:x['miss'], reverse=True)

# Cannibalization
qp_map = defaultdict(list)
for r in qp:
    qp_map[r['keys'][0]].append({'page':r['keys'][1],'clicks':r['clicks'],'impressions':r['impressions'],'position':r['position']})
cannibal = {q:p for q,p in qp_map.items() if len(p)>1}
cannibal_sorted = sorted(cannibal.items(), key=lambda x:sum(p['impressions'] for p in x[1]), reverse=True)

# Content Gaps
content_gaps = sorted([r for r in q_new if r['impressions']>=3 and r['ctr']<0.02 and r['position']>15],
                      key=lambda r:r['impressions'], reverse=True)

# Movements
both_q = set(qo)&set(qn)
declines, improvements = [], []
for q in both_q:
    o,n=qo[q],qn[q]; pc=n['position']-o['position']
    if o['impressions']>=2 or n['impressions']>=2:
        e={'q':q,'po':o['position'],'pn':n['position'],'pc':pc,'io':o['impressions'],'in':n['impressions'],'co':o['clicks'],'cn':n['clicks']}
        if pc>2: declines.append(e)
        elif pc<-2: improvements.append(e)
declines.sort(key=lambda x:x['pc'], reverse=True)
improvements.sort(key=lambda x:x['pc'])
disappeared = sorted([(q,qo[q]) for q in set(qo)-set(qn) if qo[q]['impressions']>=3], key=lambda x:x[1]['impressions'], reverse=True)
new_kw = sorted([(q,qn[q]) for q in set(qn)-set(qo) if qn[q]['impressions']>=2], key=lambda x:x[1]['impressions'], reverse=True)

# Branded vs Non-Branded
branded = [r for r in q_new if any(b in r['keys'][0].lower() for b in BRAND_TERMS)]
non_branded = [r for r in q_new if not any(b in r['keys'][0].lower() for b in BRAND_TERMS)]
br_clicks=sum(r['clicks'] for r in branded); br_impr=sum(r['impressions'] for r in branded)
nb_clicks=sum(r['clicks'] for r in non_branded); nb_impr=sum(r['impressions'] for r in non_branded)

# Long-Tail
long_tail = sorted([r for r in q_new if len(r['keys'][0].split())>=4], key=lambda r:r['impressions'], reverse=True)
medium_tail = sorted([r for r in q_new if len(r['keys'][0].split())==3], key=lambda r:r['impressions'], reverse=True)

# Keyword-to-Page mapping with mismatch detection
page_kw_map = defaultdict(list)
for r in qp:
    page_kw_map[r['keys'][1]].append({'q':r['keys'][0],'clicks':r['clicks'],'impressions':r['impressions'],'position':r['position']})
page_kw_sorted = sorted(page_kw_map.items(), key=lambda x:sum(k['impressions'] for k in x[1]), reverse=True)

# Seasonal monthly
monthly = defaultdict(lambda:{'clicks':0,'impressions':0,'pos_sum':0,'days':0})
for r in seasonal_rows:
    mk=r['keys'][0][:7]
    monthly[mk]['clicks']+=r['clicks']; monthly[mk]['impressions']+=r['impressions']
    monthly[mk]['pos_sum']+=r['position']; monthly[mk]['days']+=1

# Autocomplete
print("Autocomplete-Ideen werden geladen...")
SEEDS = ['garn alternative','garnstärke','yarn finder','wolle vergleichen','strickgarn ersatz','garn ähnlich wie']
autocomplete = {}
ctx = ssl.create_default_context()
for seed in SEEDS:
    try:
        url=f"https://suggestqueries.google.com/complete/search?client=firefox&q={urllib.parse.quote(seed)}&hl=de&gl=de"
        req=urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(req,context=ctx,timeout=5) as resp:
            data=json.loads(resp.read().decode('utf-8'))
            suggestions=[s for s in (data[1] if len(data)>1 else []) if s.lower()!=seed.lower()]
            if suggestions: autocomplete[seed]=suggestions[:6]
    except: pass

# Google Trends
print("Google Trends werden geladen...")
trends_monthly = None
trends_related_rising = None
trends_related_top = None
try:
    from pytrends.request import TrendReq
    pytrends = TrendReq(hl='de-DE', tz=360)
    trend_kws = ['Garn Alternative','Strickgarn','Garnstärke','Wolle vergleichen']
    pytrends.build_payload(trend_kws, timeframe='today 12-m', geo='DE')
    trends_raw = pytrends.interest_over_time()
    if not trends_raw.empty:
        trends_monthly = trends_raw.resample('ME').mean()
    pytrends.build_payload(['Garn Alternative'], timeframe='today 12-m', geo='DE')
    rel = pytrends.related_queries()
    if 'Garn Alternative' in rel:
        if rel['Garn Alternative']['rising'] is not None:
            trends_related_rising = rel['Garn Alternative']['rising'].head(8)
        if rel['Garn Alternative']['top'] is not None:
            trends_related_top = rel['Garn Alternative']['top'].head(8)
except Exception as e:
    print(f"  Google Trends: {e}")


# ── HTML Generation ─────────────────────────────────────────
print("Report wird generiert...")
report_date = datetime.now().strftime('%d.%m.%Y %H:%M')
chart_dates = [r['keys'][0] for r in daily]
chart_clicks = [r['clicks'] for r in daily]
chart_impr = [r['impressions'] for r in daily]

o,n = overview['old'],overview['new']

H = f"""<!DOCTYPE html>
<html lang="de"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SEO Report – {esc(SITE_DISPLAY)} – {report_date}</title>
<style>
:root{{--bg:#0f172a;--sf:#1e293b;--sf2:#334155;--tx:#e2e8f0;--mu:#94a3b8;--hd:#f1f5f9;
--blue:#3b82f6;--green:#22c55e;--red:#ef4444;--orange:#f59e0b;--purple:#a855f7;--cyan:#06b6d4;--bd:#475569}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Inter',-apple-system,system-ui,sans-serif;background:var(--bg);color:var(--tx);line-height:1.6}}
.c{{max-width:1200px;margin:0 auto;padding:2rem 1.5rem}}
.hdr{{text-align:center;margin-bottom:2.5rem;padding:2rem 0;border-bottom:1px solid var(--bd)}}
.hdr h1{{font-size:2rem;color:var(--hd)}} .hdr .sub{{color:var(--mu);font-size:.9rem}}
.kpi{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1rem;margin-bottom:2rem}}
.kc{{background:var(--sf);border-radius:12px;padding:1.25rem;border:1px solid var(--bd)}}
.kc .lb{{font-size:.75rem;color:var(--mu);text-transform:uppercase;letter-spacing:.05em;margin-bottom:.4rem}}
.kc .vl{{font-size:1.8rem;font-weight:700;color:var(--hd)}} .kc .ch{{font-size:.85rem;margin-top:.2rem}} .kc .sb{{font-size:.78rem;color:var(--mu)}}
.s{{background:var(--sf);border-radius:12px;padding:1.5rem;margin-bottom:1.25rem;border:1px solid var(--bd)}}
.s h2{{font-size:1.15rem;color:var(--hd);margin-bottom:.2rem;display:flex;align-items:center;gap:.5rem}}
.s .sd{{color:var(--mu);font-size:.83rem;margin-bottom:.75rem}}
table{{width:100%;border-collapse:collapse;font-size:.83rem}}
th{{text-align:left;padding:.5rem .6rem;color:var(--mu);font-weight:600;font-size:.72rem;text-transform:uppercase;letter-spacing:.04em;border-bottom:1px solid var(--bd)}}
td{{padding:.5rem .6rem;border-bottom:1px solid var(--sf2)}} tr:hover td{{background:rgba(255,255,255,.02)}}
.num{{text-align:right;font-variant-numeric:tabular-nums}}
.bar-bg{{width:70px;height:5px;background:var(--sf2);border-radius:3px;display:inline-block;vertical-align:middle}}
.bar-fill{{height:100%;border-radius:3px}}
.badge{{display:inline-block;padding:.12rem .45rem;border-radius:4px;font-size:.72rem;font-weight:600}}
.badge-green{{background:rgba(34,197,94,.15);color:var(--green)}} .badge-red{{background:rgba(239,68,68,.15);color:var(--red)}}
.badge-orange{{background:rgba(245,158,11,.15);color:var(--orange)}} .badge-blue{{background:rgba(59,130,246,.15);color:var(--blue)}}
.badge-purple{{background:rgba(168,85,247,.15);color:var(--purple)}} .badge-cyan{{background:rgba(6,182,212,.15);color:var(--cyan)}}
.badge-default{{background:var(--sf2);color:var(--mu)}}
.green{{color:var(--green)}} .red{{color:var(--red)}} .muted{{color:var(--mu)}} .orange{{color:var(--orange)}}
.chart-c{{width:100%;height:200px;position:relative;margin:1rem 0}} canvas{{width:100%!important;height:100%!important}}
.dv-bars{{display:flex;gap:1rem;flex-wrap:wrap}}
.dv-bar{{flex:1;min-width:180px;background:var(--sf2);border-radius:8px;padding:1rem}}
.dv-bar .dl{{font-weight:600;margin-bottom:.3rem}} .dv-bar .dv{{font-size:1.4rem;font-weight:700;color:var(--hd)}} .dv-bar .ds{{font-size:.8rem;color:var(--mu)}}
.cn-grp{{margin-bottom:.75rem;padding:.75rem;background:var(--sf2);border-radius:8px}}
.cn-q{{font-weight:600;margin-bottom:.3rem}} .cn-url{{font-size:.78rem;color:var(--mu);padding:.15rem 0;display:flex;justify-content:space-between}}
.sg{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:.6rem}}
.si{{background:var(--sf2);border-radius:8px;padding:.75rem;text-align:center}}
.si .sv{{font-size:1.6rem;font-weight:700}} .si .sl{{font-size:.75rem;color:var(--mu)}}
.empty{{color:var(--mu);font-style:italic;padding:.75rem 0;text-align:center}}
.ft{{text-align:center;color:var(--mu);font-size:.78rem;margin-top:1.5rem;padding-top:.75rem;border-top:1px solid var(--bd)}}
.rec{{border-left:3px solid var(--blue);padding:.75rem 1rem;margin-bottom:.75rem;background:var(--sf2);border-radius:0 8px 8px 0}}
.rec.rec-critical{{border-color:var(--red)}} .rec.rec-high{{border-color:var(--orange)}} .rec.rec-medium{{border-color:var(--blue)}} .rec.rec-low{{border-color:var(--green)}}
.rec .rec-head{{display:flex;justify-content:space-between;align-items:center;margin-bottom:.3rem}}
.rec .rec-title{{font-weight:700;color:var(--hd);font-size:.9rem}} .rec .rec-pri{{font-size:.72rem}}
.rec .rec-body{{font-size:.83rem;color:var(--tx);line-height:1.5}}
.rec .rec-body strong{{color:var(--hd)}}
.rec .rec-data{{font-size:.78rem;color:var(--mu);margin-top:.3rem;font-style:italic}}
.rec .rec-action{{font-size:.83rem;color:var(--cyan);margin-top:.3rem}}
.two-col{{display:grid;grid-template-columns:1fr 1fr;gap:1.25rem}}
.ac-seed{{font-weight:600;margin:.5rem 0 .2rem;color:var(--hd)}} .ac-item{{font-size:.83rem;color:var(--mu);padding:.1rem 0 .1rem 1rem}}
.mismatch{{color:var(--orange);font-size:.75rem;font-weight:600}}
@media(max-width:768px){{.c{{padding:1rem}}.kc .vl{{font-size:1.3rem}}table{{font-size:.75rem}}.two-col{{grid-template-columns:1fr}}}}
</style></head><body><div class="c">
<div class="hdr"><h1>SEO Audit Report</h1>
<div class="sub">{esc(SITE_DISPLAY)} · {report_date} · {P_OLD_START} – {P_OLD_END} vs. {P_NEW_START} – {P_NEW_END}</div></div>
"""

# KPI Cards
dc=n['clicks']-o['clicks']; di=n['impressions']-o['impressions']; dctr=n['ctr']-o['ctr']; dp=n['position']-o['position']
H += f"""<div class="kpi">
<div class="kc"><div class="lb">Klicks</div><div class="vl">{n['clicks']:.0f}</div><div class="ch">{val_arrow(dc)}</div><div class="sb">{n['cpd']:.1f}/Tag</div></div>
<div class="kc"><div class="lb">Impressionen</div><div class="vl">{n['impressions']:.0f}</div><div class="ch">{val_arrow(di)}</div><div class="sb">{n['ipd']:.1f}/Tag</div></div>
<div class="kc"><div class="lb">CTR</div><div class="vl">{n['ctr']:.1f}%</div><div class="ch">{val_arrow(dctr)}</div><div class="sb">Benchmark Pos 1: 30%</div></div>
<div class="kc"><div class="lb">Avg. Position</div><div class="vl">{n['position']:.1f}</div><div class="ch">{pos_arrow(dp)}</div><div class="sb">Niedriger = besser</div></div></div>
"""

# Trend Chart
H += f'<div class="s"><h2>📈 Traffic-Trend (8 Wochen)</h2><div class="chart-c"><canvas id="tc"></canvas></div></div>'

# ── GEO ──
H += '<div class="s"><h2>🌍 Geo / Länder-Analyse</h2><div class="sd">Woher kommen die Impressionen?</div>'
if countries:
    dach = sum(r['impressions'] for r in countries if r['keys'][0] in ('deu','aut','che'))
    dach_pct = dach/total_country_impr*100 if total_country_impr else 0
    H += f'<div style="margin-bottom:.75rem">{badge(f"DACH: {dach_pct:.0f}%","blue")} {badge(f"{len(countries)} Länder","default")}</div>'
    rows_h = []; mx_ci = max(r['impressions'] for r in countries[:15])
    for r in countries[:15]:
        c=r['keys'][0]; nm=COUNTRY_NAMES.get(c,c.upper()); pct=r['impressions']/total_country_impr*100 if total_country_impr else 0
        rows_h.append((esc(nm),f"{r['clicks']:.0f}",f"{r['impressions']:.0f}",bar_html(r['impressions'],mx_ci),f"{pct:.1f}%",f"{r['ctr']*100:.1f}%",f"{r['position']:.1f}"))
    H += tbl(['Land','Klicks','Impr','','Anteil','CTR','Pos'],rows_h,['l','r','r','l','r','r','r'])
H += '</div>'

# ── STRIKING DISTANCE ──
H += '<div class="s"><h2>🎯 Striking Distance Keywords</h2><div class="sd">Position 11-20 — fast auf Seite 1.</div>'
if striking:
    mx=max(r['impressions'] for r in striking[:15])
    rows_h=[(esc(r['keys'][0]),f"{r['position']:.1f}",f"{r['impressions']:.0f}",bar_html(r['impressions'],mx,'var(--orange)'),f"{r['clicks']:.0f}",f"{r['ctr']*100:.1f}%") for r in striking[:15]]
    H += tbl(['Keyword','Pos','Impr','','Klicks','CTR'],rows_h,['l','r','r','l','r','r'])
else: H += '<div class="empty">Keine Keywords in Position 11-20.</div>'
H += f'{badge(f"{len(striking)} Keywords","orange")}</div>'

# ── CTR GAP ──
H += '<div class="s"><h2>🔍 CTR Gap Analysis</h2><div class="sd">CTR unter Branchen-Benchmark — Titel/Meta optimieren.</div>'
if ctr_gaps:
    tm=sum(g['miss'] for g in ctr_gaps); mx=max(g['miss'] for g in ctr_gaps[:15])
    H += f'<div style="margin-bottom:.75rem">{badge(f"~{tm:.0f} verpasste Klicks","red")}</div>'
    rows_h=[(esc(g['q']),f"{g['pos']:.1f}",f"{g['impr']:.0f}",f"{g['act']:.1f}%",f"{g['exp']:.1f}%",f'<span class="red">{g["miss"]:.1f}</span>',bar_html(g['miss'],mx,'var(--red)')) for g in ctr_gaps[:15]]
    H += tbl(['Keyword','Pos','Impr','CTR ist','CTR soll','Verpasst',''],rows_h,['l','r','r','r','r','r','l'])
else: H += '<div class="empty">Keine signifikanten CTR-Lücken.</div>'
H += '</div>'

# ── CANNIBALIZATION ──
H += '<div class="s"><h2>⚔️ Keyword Cannibalization</h2><div class="sd">Mehrere URLs für denselben Query.</div>'
if cannibal_sorted:
    for q,pages in cannibal_sorted[:10]:
        ti=sum(p['impressions'] for p in pages)
        H += f'<div class="cn-grp"><div class="cn-q">"{esc(q)}" {badge(f"{len(pages)} URLs","purple")} {badge(f"{ti} Impr","blue")}</div>'
        for p in sorted(pages,key=lambda p:p['impressions'],reverse=True):
            H += f'<div class="cn-url"><span>{esc(short_url(p["page"]))}</span><span>Pos {p["position"]:.1f} · {p["impressions"]:.0f} Impr · {p["clicks"]:.0f} Klicks</span></div>'
        H += '</div>'
else: H += '<div class="empty">Keine Kannibalisierung gefunden.</div>'
H += f'{badge(f"{len(cannibal)} Queries","purple")}</div>'

# ── CONTENT GAPS ──
H += '<div class="s"><h2>📝 Content Gaps</h2><div class="sd">Hohe Impressionen, schlechtes Ranking — dedizierter Content fehlt.</div>'
if content_gaps:
    mx=max(r['impressions'] for r in content_gaps[:15])
    rows_h=[(esc(r['keys'][0]),f"{r['impressions']:.0f}",bar_html(r['impressions'],mx,'var(--cyan)'),f"{r['position']:.1f}",f"{r['ctr']*100:.1f}%") for r in content_gaps[:15]]
    H += tbl(['Keyword','Impr','','Pos','CTR'],rows_h,['l','r','l','r','r'])
else: H += '<div class="empty">Keine Content Gaps.</div>'
H += f'{badge(f"{len(content_gaps)} Gaps","cyan")}</div>'

# ── KEYWORD MOVEMENTS ──
H += '<div class="s"><h2>📊 Keyword-Bewegungen</h2><div class="sd">Ranking-Veränderungen zwischen den Zeiträumen.</div>'
if improvements:
    H += f'<h3 style="color:var(--green);margin:.75rem 0 .4rem">Verbesserungen ({len(improvements)})</h3>'
    rows_h=[(esc(d['q']),f"{d['po']:.1f}",f"{d['pn']:.1f}",pos_arrow(d['pc']),f"{d['io']:.0f}",f"{d['in']:.0f}") for d in improvements[:10]]
    H += tbl(['Keyword','Pos alt','Pos neu','Diff','Impr alt','Impr neu'],rows_h,['l','r','r','r','r','r'])
if declines:
    H += f'<h3 style="color:var(--red);margin:.75rem 0 .4rem">Verschlechterungen ({len(declines)})</h3>'
    rows_h=[(esc(d['q']),f"{d['po']:.1f}",f"{d['pn']:.1f}",pos_arrow(d['pc']),f"{d['io']:.0f}",f"{d['in']:.0f}") for d in declines[:10]]
    H += tbl(['Keyword','Pos alt','Pos neu','Diff','Impr alt','Impr neu'],rows_h,['l','r','r','r','r','r'])
if new_kw:
    H += f'<h3 style="color:var(--cyan);margin:.75rem 0 .4rem">Neue Keywords ({len(new_kw)})</h3>'
    rows_h=[(esc(q),f"{d['impressions']:.0f}",f"{d['clicks']:.0f}",f"{d['position']:.1f}") for q,d in new_kw[:10]]
    H += tbl(['Keyword','Impr','Klicks','Pos'],rows_h,['l','r','r','r'])
if disappeared:
    H += f'<h3 style="color:var(--orange);margin:.75rem 0 .4rem">Verschwunden ({len(disappeared)})</h3>'
    rows_h=[(esc(q),f"{d['impressions']:.0f}",f"{d['clicks']:.0f}",f"{d['position']:.1f}") for q,d in disappeared[:10]]
    H += tbl(['Keyword','Impr (vorher)','Klicks','Pos'],rows_h,['l','r','r','r'])
H += '</div>'

# ── Two column: Device + Branded ──
H += '<div class="two-col">'

# Device
H += '<div class="s"><h2>📱 Device Split</h2><div class="sd">Performance nach Gerät.</div><div class="dv-bars" style="flex-direction:column">'
dev_labels = {'MOBILE':('📱','Mobile'),'DESKTOP':('🖥️','Desktop'),'TABLET':('📋','Tablet')}
tdvi = sum(d['impressions'] for d in dev_data.values()) or 1
for dv,dd in dev_data.items():
    ic,lb=dev_labels.get(dv,('',dv)); pct=dd['impressions']/tdvi*100
    H += f'<div class="dv-bar"><div class="dl">{ic} {lb} ({pct:.0f}%)</div><div class="dv">{dd["clicks"]:.0f} <span style="font-size:.75rem;color:var(--mu)">Klicks</span></div><div class="ds">{dd["impressions"]:.0f} Impr · CTR {dd["ctr"]:.1f}% · Pos {dd["position"]:.1f}</div></div>'
H += '</div></div>'

# Branded
H += '<div class="s"><h2>🏷️ Branded vs. Non-Branded</h2><div class="sd">Markenbekanntheit in der Suche.</div>'
total_bi = br_impr+nb_impr or 1
H += f'<div class="dv-bars" style="flex-direction:column">'
br_ctr = (br_clicks/br_impr*100) if br_impr else 0
nb_ctr = (nb_clicks/nb_impr*100) if nb_impr else 0
H += f'<div class="dv-bar"><div class="dl">🏷️ Branded ({br_impr/total_bi*100:.0f}%)</div><div class="dv">{br_clicks:.0f} <span style="font-size:.75rem;color:var(--mu)">Klicks</span></div><div class="ds">{br_impr:.0f} Impr · {len(branded)} Keywords · CTR {br_ctr:.1f}%</div></div>'
H += f'<div class="dv-bar"><div class="dl">🔍 Non-Branded ({nb_impr/total_bi*100:.0f}%)</div><div class="dv">{nb_clicks:.0f} <span style="font-size:.75rem;color:var(--mu)">Klicks</span></div><div class="ds">{nb_impr:.0f} Impr · {len(non_branded)} Keywords · CTR {nb_ctr:.1f}%</div></div>'
H += '</div>'
if br_impr == 0: H += '<div style="margin-top:.5rem;color:var(--orange);font-size:.83rem">⚠ Keine Branded Searches — Brand Awareness aufbauen!</div>'
H += '</div></div>'

# ── SEASONAL TRENDS ──
H += '<div class="s"><h2>📅 Saisonale Trends</h2><div class="sd">Monatliche Performance über die verfügbare Historie.</div>'
if monthly:
    mx_mi = max(m['impressions'] for m in monthly.values())
    rows_h = []
    for mk in sorted(monthly.keys()):
        m=monthly[mk]; ctr=(m['clicks']/m['impressions']*100) if m['impressions'] else 0; ap=m['pos_sum']/m['days'] if m['days'] else 0
        rows_h.append((mk,f"{m['clicks']:.0f}",f"{m['impressions']:.0f}",bar_html(m['impressions'],mx_mi,'var(--green)'),f"{ctr:.1f}%",f"{ap:.1f}"))
    H += tbl(['Monat','Klicks','Impr','','CTR','Avg Pos'],rows_h,['l','r','r','l','r','r'])
H += '</div>'

# ── INTENT MISMATCHES ──
H += '<div class="s"><h2>🔀 Keyword → Seite Mapping</h2><div class="sd">Welche Keywords landen auf welcher Seite? Mismatches werden markiert.</div>'
for page, kws in page_kw_sorted[:8]:
    short = short_url(page)
    ti=sum(k['impressions'] for k in kws); tc=sum(k['clicks'] for k in kws)
    kws.sort(key=lambda k:k['impressions'], reverse=True)
    H += f'<div class="cn-grp"><div class="cn-q">{esc(short)} {badge(f"{tc} Klicks","blue")} {badge(f"{ti} Impr","default")}</div>'
    for k in kws[:5]:
        mismatch = ''
        q = k['q'].lower()
        if 'garnstärk' in q and '/garnstaerken' not in page: mismatch = '<span class="mismatch"> ⚠ → /garnstaerken</span>'
        elif 'glossar' in q and '/glossar' not in page: mismatch = '<span class="mismatch"> ⚠ → /glossar</span>'
        elif 'blog' in q and '/blog' not in page: mismatch = '<span class="mismatch"> ⚠ → /blog</span>'
        elif 'faq' in q and '/faq' not in page: mismatch = '<span class="mismatch"> ⚠ → /faq</span>'
        H += f'<div class="cn-url"><span>{esc(k["q"])}{mismatch}</span><span>Pos {k["position"]:.1f} · {k["impressions"]:.0f} Impr</span></div>'
    H += '</div>'
H += '</div>'

# ── RICH RESULTS ──
H += '<div class="s"><h2>✨ Search Appearance</h2><div class="sd">Rich Results in der Google-Suche.</div>'
if sa_rows:
    rows_h = [(esc(r['keys'][0]),f"{r['clicks']:.0f}",f"{r['impressions']:.0f}",f"{r['ctr']*100:.1f}%",f"{r['position']:.1f}") for r in sorted(sa_rows,key=lambda r:r['impressions'],reverse=True)]
    H += tbl(['Typ','Klicks','Impr','CTR','Pos'],rows_h,['l','r','r','r','r'])
else:
    H += '<div class="empty">Keine Rich Results aktiv.</div>'
    H += '<div style="color:var(--orange);font-size:.83rem;text-align:center">Schema validieren: <a href="https://search.google.com/test/rich-results" style="color:var(--blue)" target="_blank">Google Rich Results Test</a></div>'
H += '</div>'

# ── Two column: Long-Tail + Autocomplete ──
H += '<div class="two-col">'

# Long-Tail
H += '<div class="s"><h2>🔗 Long-Tail Keywords</h2><div class="sd">4+ Wörter — spezifische Suchintention.</div>'
if long_tail:
    rows_h = [(esc(r['keys'][0]),f"{r['impressions']:.0f}",f"{r['position']:.1f}") for r in long_tail[:12]]
    H += tbl(['Keyword','Impr','Pos'],rows_h,['l','r','r'])
else: H += '<div class="empty">Keine Long-Tail Keywords.</div>'
if medium_tail:
    H += f'<div style="margin-top:.5rem;font-size:.8rem;color:var(--mu)">{len(medium_tail)} 3-Wort Keywords gefunden</div>'
H += '</div>'

# Autocomplete
H += '<div class="s"><h2>💡 Google Autocomplete Ideen</h2><div class="sd">Was Google vorschlägt — Content-Ideen.</div>'
if autocomplete:
    for seed, suggestions in autocomplete.items():
        H += f'<div class="ac-seed">"{esc(seed)}"</div>'
        for s in suggestions:
            H += f'<div class="ac-item">→ {esc(s)}</div>'
else: H += '<div class="empty">Keine Autocomplete-Daten.</div>'
H += '</div></div>'

# ── Google Trends ──
H += '<div class="s"><h2>📈 Google Trends (12 Monate, Deutschland)</h2><div class="sd">Suchinteresse im Zeitverlauf.</div>'
if trends_monthly is not None:
    H += '<div class="chart-c"><canvas id="trendsChart"></canvas></div>'
if trends_related_rising is not None or trends_related_top is not None:
    H += '<div class="two-col" style="margin-top:1rem">'
    if trends_related_top is not None:
        H += '<div><h3 style="color:var(--hd);font-size:.9rem;margin-bottom:.4rem">Top verwandte Suchanfragen</h3>'
        rows_h = [(esc(row['query']),f"{row['value']}") for _,row in trends_related_top.iterrows()]
        H += tbl(['Query','Relevanz'],rows_h,['l','r']) + '</div>'
    if trends_related_rising is not None:
        H += '<div><h3 style="color:var(--hd);font-size:.9rem;margin-bottom:.4rem">Rising Queries</h3>'
        rows_h = [(esc(row['query']),f"{row['value']}") for _,row in trends_related_rising.iterrows()]
        H += tbl(['Query','Anstieg'],rows_h,['l','r']) + '</div>'
    H += '</div>'
if trends_monthly is None: H += '<div class="empty">Google Trends nicht verfügbar (pytrends installiert?).</div>'
H += '</div>'

# ── RECOMMENDATIONS ENGINE ──────────────────────────────────
# Automatically derive actionable recommendations from the data

recs = []  # (priority, title, body, data_evidence, action)

# R1: CTR Gaps — biggest missed clicks opportunity
if ctr_gaps:
    top_gap = ctr_gaps[0]
    total_miss = sum(g['miss'] for g in ctr_gaps)
    recs.append(('critical', 'Titel & Meta-Descriptions optimieren',
        f'<strong>{len(ctr_gaps)} Keywords</strong> haben eine CTR unter dem Branchen-Benchmark. '
        f'Insgesamt werden geschätzt <strong>~{total_miss:.0f} Klicks/Monat</strong> verschenkt.',
        f'Größte Lücke: „{esc(top_gap["q"])}" auf Pos {top_gap["pos"]:.1f} — CTR {top_gap["act"]:.1f}% statt erwarteter {top_gap["exp"]:.1f}%',
        'Titel-Tags mit Power-Words und aktuellen Jahreszahlen versehen. '
        'Meta-Descriptions mit konkretem Nutzenversprechen und Call-to-Action schreiben. '
        'Google Rich Results Test durchführen um Snippet-Darstellung zu prüfen.'))

# R2: Intent Mismatches — wrong pages ranking
mismatches = []
for page, kws in page_kw_sorted:
    for k in kws:
        q = k['q'].lower()
        if ('garnstärk' in q and '/garnstaerken' not in page) or \
           ('glossar' in q and '/glossar' not in page) or \
           ('blog' in q and '/blog' not in page):
            mismatches.append((k['q'], short_url(page), k['impressions']))
if mismatches:
    mismatches.sort(key=lambda x: x[2], reverse=True)
    top_mm = mismatches[0]
    recs.append(('critical', 'Intent Mismatches beheben — falsche Seiten ranken',
        f'<strong>{len(mismatches)} Keywords</strong> landen auf der falschen Seite. '
        f'Google zeigt den Nutzern nicht die Seite mit dem besten Content.',
        f'„{esc(top_mm[0])}" rankt auf {esc(top_mm[1])} statt auf der dedizierten Seite',
        'Interne Verlinkung stärken: von allen relevanten Seiten auf die Zielseite verlinken mit dem Keyword als Anchor-Text. '
        'Canonical-Tags prüfen. Ggf. den Content der rankenden Seite kürzen damit Google die Zielseite bevorzugt.'))

# R3: No Rich Results
if not sa_rows:
    recs.append(('high', 'Rich Results aktivieren — Schema wird nicht erkannt',
        'Trotz implementierter Schema-Daten (FAQ, Breadcrumbs) zeigt Google <strong>keine Rich Results</strong> an. '
        'Rich Results erhöhen die CTR um durchschnittlich 20-30%.',
        'Search Appearance liefert 0 Ergebnisse',
        '<a href="https://search.google.com/test/rich-results" target="_blank" style="color:var(--cyan)">Google Rich Results Test</a> '
        'mit den wichtigsten URLs durchführen. JSON-LD Schema auf Syntax-Fehler prüfen. '
        'Sicherstellen dass das Schema im initialen HTML gerendert wird (nicht erst client-side).'))

# R4: Branded searches = 0
if br_impr == 0:
    recs.append(('high', 'Brand Awareness aufbauen — null Branded Searches',
        'Kein einziger Nutzer sucht nach dem Markennamen. '
        'Das bedeutet die Seite hat <strong>keine Markenbekanntheit</strong> und ist komplett von organischer Discovery abhängig.',
        f'0 Branded Keywords, 100% Non-Branded Traffic',
        'Social-Media-Präsenz aufbauen (Instagram, Pinterest — visuelle Plattformen passen zu Handarbeit). '
        'Newsletter starten. Gast-Beiträge in Strick-/Handarbeits-Communities. '
        'Auf Ravelry, Reddit r/knitting oder deutschen Strick-Foren aktiv werden.'))

# R5: Striking Distance
if striking:
    top_sd = striking[0]
    recs.append(('high', f'{len(striking)} Keywords fast auf Seite 1',
        f'Diese Keywords ranken auf Position 11-20 und brauchen nur kleine Optimierungen um auf Seite 1 zu kommen.',
        f'Top: „{esc(top_sd["keys"][0])}" auf Pos {top_sd["position"]:.1f} mit {top_sd["impressions"]:.0f} Impressionen',
        'Für jedes Striking-Distance-Keyword: (1) Internen Link von einer starken Seite setzen, '
        '(2) Content auf der Zielseite um den Suchbegriff erweitern, '
        '(3) Titel/H1 optimieren um das Keyword prominenter zu platzieren.'))

# R6: Content Gaps
if content_gaps:
    top_cg = content_gaps[0]
    recs.append(('medium', f'{len(content_gaps)} Content-Lücken schließen',
        'Diese Keywords haben Impressionen aber die Seite rankt auf Position 15+. '
        'Es fehlt dedizierter Content der die Suchintention trifft.',
        f'Top: „{esc(top_cg["keys"][0])}" mit {top_cg["impressions"]:.0f} Impr auf Pos {top_cg["position"]:.1f}',
        'Blog-Artikel oder dedizierte Landingpages erstellen. '
        'Besonders für Keywords die ein Informationsbedürfnis zeigen (z.B. Tabellen, Vergleiche, „was ist...").'))

# R7: International traffic untapped
non_dach = [r for r in countries if r['keys'][0] not in ('deu','aut','che')]
non_dach_impr = sum(r['impressions'] for r in non_dach)
non_dach_pct = non_dach_impr / total_country_impr * 100 if total_country_impr else 0
if non_dach_pct > 15:
    top_intl = non_dach[0] if non_dach else None
    top_name = COUNTRY_NAMES.get(top_intl['keys'][0], top_intl['keys'][0].upper()) if top_intl else '?'
    recs.append(('medium', f'Internationales Potenzial nutzen — {non_dach_pct:.0f}% Non-DACH Traffic',
        f'<strong>{non_dach_pct:.0f}%</strong> der Impressionen kommen von außerhalb DACH. '
        f'Die englische Version der Seite wird bereits gefunden, ist aber nicht optimiert.',
        f'Top internationales Land: {esc(top_name)} mit {top_intl["impressions"]:.0f} Impressionen' if top_intl else '',
        'EN-Seiten mit eigenständigen Meta-Descriptions und H1-Tags versehen (nicht nur übersetzen). '
        'Hreflang-Tags prüfen. EN-spezifische Keywords recherchieren und einarbeiten.'))

# R8: Long-Tail opportunities
lt_good = [r for r in long_tail if r['position'] <= 5]
if lt_good:
    recs.append(('medium', f'{len(lt_good)} Long-Tail Keywords in Top 5 — Content ausbauen',
        'Diese spezifischen Suchanfragen ranken bereits sehr gut. '
        'Mit dediziertem Content (z.B. Blog: „Alternative zu [Garn X]") kann daraus signifikanter Traffic werden.',
        ', '.join(f'„{esc(r["keys"][0])}"' for r in lt_good[:3]),
        'Pro Garn-Alternative einen kurzen Blog-Artikel schreiben (300-500 Wörter). '
        'Von der Yarn-Detail-Seite auf den Blog-Artikel verlinken und umgekehrt.'))

# R9: Declining keywords
if declines:
    top_dec = declines[0]
    recs.append(('medium', f'{len(declines)} Keywords verlieren an Position',
        'Diese Keywords haben sich in den letzten 4 Wochen verschlechtert.',
        f'Stärkster Verlust: „{esc(top_dec["q"])}" von Pos {top_dec["po"]:.1f} auf {top_dec["pn"]:.1f}',
        'Content der betroffenen Seiten aktualisieren und erweitern. '
        'Interne Verlinkung prüfen — wurden Links entfernt? '
        'Wettbewerber-Seiten für diese Keywords analysieren: was machen die besser?'))

# R10: Seasonal preparation
if trends_monthly is not None and 'Strickgarn' in trends_monthly.columns:
    vals = trends_monthly['Strickgarn'].tolist()
    peak_idx = vals.index(max(vals))
    peak_month = trends_monthly.index[peak_idx].strftime('%B')
    recs.append(('low', f'Saisonale Content-Planung — Peak in {peak_month}',
        '„Strickgarn"-Suchanfragen haben klare saisonale Muster. '
        'Der Peak liegt im Herbst/Winter.',
        f'Google Trends zeigt Peak-Interesse bei Score {max(vals):.0f}',
        'Content 4-6 Wochen vor dem Peak veröffentlichen (August/September). '
        'Saisonale Landingpages oder Blog-Posts vorbereiten: „Herbst-Garne", „Winter-Strickprojekte". '
        'Social Media Kampagnen auf den saisonalen Peak ausrichten.'))

# R11: Autocomplete content ideas
if autocomplete:
    all_suggestions = []
    for seed, suggs in autocomplete.items():
        for s in suggs:
            if s.lower() not in [r['keys'][0].lower() for r in q_new]:
                all_suggestions.append(s)
    if all_suggestions:
        recs.append(('low', f'{len(all_suggestions)} Autocomplete-Keywords nicht abgedeckt',
            'Google schlägt Suchanfragen vor, für die die Seite noch keinen Content hat.',
            ', '.join(f'„{esc(s)}"' for s in all_suggestions[:5]),
            'Diese Autocomplete-Vorschläge als Basis für neue Blog-Artikel oder FAQ-Einträge nutzen. '
            'Besonders vielversprechend sind Vorschläge mit konkreten Garn-Namen '
            '(z.B. „bobbiny garn alternative") — diese haben klare Kaufintention.'))

# R12: Cannibalization
if cannibal_sorted:
    top_cn = cannibal_sorted[0]
    recs.append(('high', f'{len(cannibal)} Keywords werden kannibalisiert',
        'Mehrere eigene Seiten konkurrieren für denselben Suchbegriff.',
        f'„{esc(top_cn[0])}" rankt auf {len(top_cn[1])} verschiedenen URLs',
        'Eine Hauptseite pro Keyword bestimmen. Andere Seiten via Canonical oder 301-Redirect konsolidieren. '
        'Alternativ: Content differenzieren sodass jede Seite eine eigene Suchintention bedient.'))

# Sort by priority
pri_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
recs.sort(key=lambda r: pri_order.get(r[0], 9))

# Generate HTML
pri_labels = {'critical': ('Kritisch', 'red'), 'high': ('Hoch', 'orange'), 'medium': ('Mittel', 'blue'), 'low': ('Niedrig', 'green')}

H += '<div class="s"><h2>🚀 Handlungsempfehlungen</h2>'
H += f'<div class="sd">{len(recs)} konkrete Maßnahmen, priorisiert nach Impact. Automatisch abgeleitet aus den Daten oben.</div>'

for pri, title, body, data, action in recs:
    plabel, pcolor = pri_labels.get(pri, ('?', 'default'))
    H += f'''<div class="rec rec-{pri}">
<div class="rec-head"><div class="rec-title">{esc(title)}</div>{badge(plabel, pcolor)}</div>
<div class="rec-body">{body}</div>
<div class="rec-data">📊 {data}</div>
<div class="rec-action">→ {action}</div></div>'''

if not recs:
    H += '<div class="empty">Keine dringenden Empfehlungen — weiter beobachten.</div>'

H += '</div>'

# ── SUMMARY ──
H += f"""<div class="s"><h2>📋 Zusammenfassung</h2><div class="sg">
<div class="si"><div class="sv" style="color:var(--blue)">{len(countries)}</div><div class="sl">Länder</div></div>
<div class="si"><div class="sv" style="color:var(--orange)">{len(striking)}</div><div class="sl">Striking Dist.</div></div>
<div class="si"><div class="sv" style="color:var(--red)">{len(ctr_gaps)}</div><div class="sl">CTR-Lücken</div></div>
<div class="si"><div class="sv" style="color:var(--purple)">{len(cannibal)}</div><div class="sl">Kannibalisiert</div></div>
<div class="si"><div class="sv" style="color:var(--cyan)">{len(content_gaps)}</div><div class="sl">Content Gaps</div></div>
<div class="si"><div class="sv" style="color:var(--green)">{len(improvements)}</div><div class="sl">Verbessert</div></div>
<div class="si"><div class="sv" style="color:var(--red)">{len(declines)}</div><div class="sl">Verschlechtert</div></div>
<div class="si"><div class="sv" style="color:var(--cyan)">{len(new_kw)}</div><div class="sl">Neue Keywords</div></div>
<div class="si"><div class="sv" style="color:var(--orange)">{len(disappeared)}</div><div class="sl">Verschwunden</div></div>
<div class="si"><div class="sv" style="color:var(--blue)">{len(long_tail)}</div><div class="sl">Long-Tail</div></div>
</div></div>
"""

H += f'<div class="ft">Generiert am {report_date} · Google Search Console API + Google Trends + Autocomplete · {esc(SITE_DISPLAY)}</div></div>'

# ── Charts JS ──
trend_kw_labels = ['Garn Alternative','Strickgarn','Garnstärke','Wolle vergleichen']
trend_colors = ['#3b82f6','#22c55e','#f59e0b','#a855f7']
trends_datasets_js = ''
if trends_monthly is not None:
    t_labels = [idx.strftime('%Y-%m') for idx in trends_monthly.index]
    for i, kw in enumerate(trend_kw_labels):
        vals = [int(trends_monthly.loc[idx, kw]) if kw in trends_monthly.columns else 0 for idx in trends_monthly.index]
        trends_datasets_js += f'{{label:"{kw}",data:{vals},borderColor:"{trend_colors[i]}",tension:.3,fill:false}},'
    trends_chart_js = f"""
const tc2=document.getElementById('trendsChart');
if(tc2){{new Chart(tc2.getContext('2d'),{{type:'line',data:{{labels:{t_labels},datasets:[{trends_datasets_js}]}},
options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{labels:{{color:'#94a3b8'}}}}}},
scales:{{x:{{ticks:{{color:'#94a3b8'}},grid:{{color:'rgba(71,85,105,.3)'}}}},y:{{ticks:{{color:'#94a3b8'}},grid:{{color:'rgba(71,85,105,.3)'}},beginAtZero:true}}}}}}}})}}"""
else:
    trends_chart_js = ''

H += f"""
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<script>
new Chart(document.getElementById('tc').getContext('2d'),{{type:'line',data:{{
labels:{chart_dates},datasets:[
{{label:'Klicks',data:{chart_clicks},borderColor:'#3b82f6',backgroundColor:'rgba(59,130,246,.1)',fill:true,tension:.3}},
{{label:'Impressionen',data:{chart_impr},borderColor:'#22c55e',backgroundColor:'rgba(34,197,94,.1)',fill:true,tension:.3}}
]}},options:{{responsive:true,maintainAspectRatio:false,interaction:{{mode:'index',intersect:false}},
plugins:{{legend:{{labels:{{color:'#94a3b8'}}}}}},
scales:{{x:{{ticks:{{color:'#94a3b8',maxTicksLimit:10}},grid:{{color:'rgba(71,85,105,.3)'}}}},
y:{{ticks:{{color:'#94a3b8'}},grid:{{color:'rgba(71,85,105,.3)'}},beginAtZero:true}}}}}}}});
{trends_chart_js}
</script></body></html>"""

# ── Save ────────────────────────────────────────────────────
out_dir = os.path.join(os.getcwd(), 'reports')
os.makedirs(out_dir, exist_ok=True)
fname = f'seo-report-{datetime.now().strftime("%Y%m%d-%H%M")}.html'
fpath = os.path.join(out_dir, fname)
latest = os.path.join(out_dir, 'latest.html')

for p in [fpath, latest]:
    with open(p, 'w', encoding='utf-8') as f:
        f.write(H)

print(f"\nReport gespeichert:")
print(f"  {fpath}")
print(f"  {latest}")

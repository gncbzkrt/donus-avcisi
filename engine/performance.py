import json
from pathlib import Path
from statistics import mean, median
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
HISTORY = ROOT / 'data' / 'history'
OUT = ROOT / 'data' / 'performance.json'
HORIZONS = {'1G':1, '5G':5, '20G':20, '60G':60}


def _load_snapshots():
    raw=[]
    for p in sorted(HISTORY.glob('*.json')):
        try:
            snap=json.loads(p.read_text(encoding='utf-8'))
            raw.append(snap)
        except Exception:
            pass
    # Aynı gün içinde birden fazla tarama yapılırsa yalnızca günün son taramasını kullan.
    by_day={}
    for snap in raw:
        ts=snap.get('generated_at')
        if not ts: continue
        day=str(ts)[:10]
        by_day[day]=snap
    return [by_day[d] for d in sorted(by_day)]


def _stats(values):
    if not values:
        return {'adet':0,'basari':None,'ortalama':None,'medyan':None,'en_iyi':None,'en_kotu':None}
    wins=sum(1 for x in values if x>0)
    return {
        'adet':len(values),
        'basari':round(100*wins/len(values),1),
        'ortalama':round(mean(values),2),
        'medyan':round(median(values),2),
        'en_iyi':round(max(values),2),
        'en_kotu':round(min(values),2),
    }


def build_performance():
    snaps=_load_snapshots()
    result={'guncellendi':None,'evren_gun_sayisi':len(snaps),'ufuklar':{},'stratejiler':{},'not':'Pozitif sonuç, ilgili ufukta fiyatın sinyal gününe göre yükselmesini ifade eder.'}
    if not snaps:
        OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        return result
    result['guncellendi']=snaps[-1].get('generated_at')
    for label,h in HORIZONS.items():
        vals=[]
        for i,snap in enumerate(snaps):
            j=i+h
            if j>=len(snaps): break
            future={x.get('symbol'):x for x in (snaps[j].get('rows') or snaps[j].get('leaders',[]))}
            for x in (snap.get('rows') or snap.get('leaders',[])):
                if x.get('state')=='NO_SETUP' or float(x.get('confidence',0))<60: continue
                cur=future.get(x.get('symbol'))
                if not cur or not x.get('price') or not cur.get('price'): continue
                vals.append((float(cur['price'])/float(x['price'])-1)*100)
        result['ufuklar'][label]=_stats(vals)
    for strategy in ['daily','swing','trend','mid_term','reversal']:
        vals=[]
        for i,snap in enumerate(snaps):
            j=i+({'daily':1,'swing':5,'trend':20,'mid_term':60,'reversal':20}[strategy])
            if j>=len(snaps): break
            future={x.get('symbol'):x for x in (snaps[j].get('rows') or snaps[j].get('leaders',[]))}
            for x in (snap.get('rows') or snap.get('leaders',[])):
                score=float(x.get('strategies',{}).get(strategy,0))
                if score<65: continue
                cur=future.get(x.get('symbol'))
                if cur and x.get('price') and cur.get('price'):
                    vals.append((float(cur['price'])/float(x['price'])-1)*100)
        result['stratejiler'][strategy]=_stats(vals)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return result

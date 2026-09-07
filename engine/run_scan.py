import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import pandas as pd
from .providers import FallbackProvider, DataUnavailable, ProviderError
from .reversal import analyze_reversal
from .strategies import strategy_scores
from .universe import load_universe
from .performance import build_performance

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'; HISTORY=DATA/'history'; CHARTS=DATA/'charts'
MAX_WORKERS=int(os.getenv('RH_WORKERS','2'))
TIMEOUT=int(os.getenv('RH_TIMEOUT','15'))
DELAY=float(os.getenv('RH_DELAY','0.45'))
LIMIT=int(os.getenv('RH_LIMIT','0'))


def market_score(provider):
    vals=[]
    for s in ['XU100','XU030']:
        try:
            result=provider.history(s,period='1y')
            df=result[0] if isinstance(result,tuple) else result
            if df.empty: continue
            c=df.close
            score=50
            if len(c)>=50: score += 20 if c.iloc[-1]>c.rolling(50).mean().iloc[-1] else -15
            if len(c)>=50: score += 15 if c.rolling(20).mean().iloc[-1]>c.rolling(50).mean().iloc[-1] else -10
            if len(c)>=200: score += 15 if c.iloc[-1]>c.rolling(200).mean().iloc[-1] else -10
            vals.append(score)
        except Exception:
            pass
    return round(sum(vals)/len(vals),1) if vals else 50.0


def scan_one(symbol):
    provider=FallbackProvider(timeout=TIMEOUT,delay=DELAY)
    try:
        result=provider.history(symbol,period='2y')
        df,source=result if isinstance(result,tuple) else (result,getattr(provider,'name','BIST'))

        if df.empty:
            return {'symbol':symbol,'status':'DATA_UNAVAILABLE','error':'Veri yok'}

        rev=analyze_reversal(df)
        strategies=strategy_scores(df,rev)

        best_strategy=max(strategies,key=strategies.get)
        best_score=float(strategies[best_strategy])

        if rev.get('ready'):
            row={'symbol':symbol,'source':source,'status':'ANALYZED',**rev}
        else:
            from .indicators import atr
            price=float(df.close.iloc[-1])
            av=float(atr(df,14).iloc[-1])
            stop=price-max(av*1.8,price*.035)
            risk=max(price-stop,price*.01)
            row={
                'symbol':symbol,
                'source':source,
                'status':'SHORT_HISTORY' if len(df)<220 else 'ANALYZED',
                'ready':False,
                'state':'NO_SETUP',
                'price':round(price,4),
                'confidence':0,
                'dip_score':0,
                'turn_score':0,
                'seller_exhaustion':0,
                'buyer_awakening':0,
                'asymmetry':0,
                'stop':round(stop,4),
                'target1':round(price+risk*1.8,4),
                'target2':round(price+risk*3,4),
                'risk_reward_1':1.8,
                'risk_reward_2':3.0,
                'reasons':[]
            }

        row['strategies']=strategies
        row['best_strategy']=best_strategy
        row['best_score']=round(best_score,1)

        if best_score>=65:
            row['state']='STRATEGY_SETUP'
            row['opportunity']=True
            names={
                'daily':'Günlük momentum',
                'swing':'Swing yapısı',
                'trend':'Trend gücü',
                'mid_term':'Orta vadeli güç',
                'reversal':'Dipten dönüş'
            }
            if best_strategy!='reversal':
                row['reasons']=[names[best_strategy]]
        else:
            row['opportunity']=False

        if not rev.get('ready'):
            row['confidence']=round(best_score,1)

        # Fırsat adayları için son 260 günlük OHLCV verisini static grafik dosyasına hazırla.
        # Grafik frontend tarafından EMA/RSI/MACD ile çizilir; TradingView bağımlılığı yoktur.
        if best_score >= 65:
            chart=[]
            for idx, bar in df.tail(260).iterrows():
                try:
                    chart.append({
                        'date':pd.Timestamp(idx).strftime('%Y-%m-%d'),
                        'open':float(bar['open']),
                        'high':float(bar['high']),
                        'low':float(bar['low']),
                        'close':float(bar['close']),
                        'volume':float(bar['volume']) if pd.notna(bar['volume']) else 0
                    })
                except Exception:
                    pass
            if len(chart)>=2:
                row['_chart']=chart

        return row

    except DataUnavailable as e:
        return {'symbol':symbol,'status':'DATA_UNAVAILABLE','error':str(e)}
    except Exception as e:
        return {'symbol':symbol,'status':'PROVIDER_ERROR','error':str(e)}

def json_safe(value):
    """JSON uyumlu hale getirir; NaN/Infinity -> None."""
    import math

    if isinstance(value, dict):
        return {k: json_safe(v) for k, v in value.items()}

    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]

    # Python float ve NumPy float tiplerini güvenli şekilde ele al
    if isinstance(value, float) or type(value).__name__ in ("float16", "float32", "float64"):
        try:
            return None if not math.isfinite(float(value)) else float(value)
        except (TypeError, ValueError):
            return None

    return value


def main():
    DATA.mkdir(exist_ok=True); HISTORY.mkdir(exist_ok=True); CHARTS.mkdir(exist_ok=True)
    symbols=list(load_universe())
    if LIMIT>0: symbols=symbols[:LIMIT]
    print(f'Veri kaynağı: İş Yatırım | Evren: {len(symbols)} | Paralel: {MAX_WORKERS} | İstek aralığı: {DELAY}s',flush=True)
    rows=[]; unavailable=[]; provider_errors=[]
    provider=FallbackProvider(timeout=TIMEOUT,delay=DELAY)
    mscore=market_score(provider)
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures={pool.submit(scan_one,s):s for s in symbols}; total=len(futures); done=0
        for f in as_completed(futures):
            done+=1; r=f.result()
            status=r.get('status')
            if status=='DATA_UNAVAILABLE': unavailable.append(r)
            elif status=='PROVIDER_ERROR': provider_errors.append(r)
            else: rows.append(r)
            if done==1 or done%10==0 or done==total:
                print(f'Tarama ilerlemesi: {done}/{total} | analiz {len(rows)} | veri yok {len(unavailable)} | hata {len(provider_errors)}',flush=True)
    # ============================================================
    # FINAL OPPORTUNITY FILTER — QUALITY RADAR
    # Her stratejinin yalnızca EN İYİ 10 adayı fırsat olabilir.
    # Kısa geçmişli hisseler hiçbir koşulda fırsat değildir.
    # Aynı hisse birden fazla stratejide yer alabilir.
    # ============================================================
    strategy_thresholds={
        'daily':80,
        'swing':80,
        'trend':82,
        'mid_term':82,
        'reversal':80
    }

    selected={}
    strategy_leaders={}
    strategy_counts={}

    for strategy,threshold in strategy_thresholds.items():
        candidates=[
            x for x in rows
            if x.get('status')!='SHORT_HISTORY'
            and float(x.get('strategies',{}).get(strategy,0))>=threshold
        ]

        candidates.sort(
            key=lambda x:float(
                x.get('strategies',{}).get(strategy,0)
            ),
            reverse=True
        )

        leaders=candidates[:10]
        strategy_leaders[strategy]=leaders
        strategy_counts[strategy]=len(leaders)

        for x in leaders:
            symbol=x['symbol']
            selected.setdefault(symbol,[]).append(strategy)

    names={
        'daily':'Günlük momentum',
        'swing':'Swing yapısı',
        'trend':'Trend gücü',
        'mid_term':'Orta vadeli güç',
        'reversal':'Dipten dönüş'
    }

    for x in rows:
        symbol=x['symbol']
        chosen=selected.get(symbol,[])

        if not chosen:
            x['opportunity']=False
            x['state']='NO_SETUP'
            x['confidence']=0
            x['eligible_strategies']={}
            continue

        eligible={
            st:float(x.get('strategies',{}).get(st,0))
            for st in chosen
        }

        best=max(eligible,key=eligible.get)

        x['opportunity']=True
        x['state']='STRATEGY_SETUP'
        x['eligible_strategies']=eligible
        x['best_strategy']=best
        x['best_score']=round(float(eligible[best]),1)
        x['confidence']=round(float(eligible[best]),1)

        x['reasons']=[
            f"En uygun: {names[best]}"
        ]

        if len(chosen)>1:
            x['reasons'].append(
                'Çoklu strateji teyidi'
            )

    rows.sort(
        key=lambda x:(
            x.get('opportunity',False),
            x.get('best_score',0),
            x.get('confidence',0)
        ),
        reverse=True
    )

    now=pd.Timestamp.now(tz='Europe/Istanbul')
    opp=sum(1 for x in rows if x.get('opportunity'))

    # Static grafik verisini latest.json'dan ayrı tut.
    chart_payloads={}
    for item in rows:
        chart=item.pop('_chart',None)
        if chart:
            chart_payloads[item['symbol']]=chart

    payload={
      'generated_at':now.isoformat(),'market':{'score':mscore,'regime':'POZİTİF' if mscore>=65 else 'NÖTR' if mscore>=45 else 'RİSK AZALT'},
      'universe_count':len(symbols),'attempted_count':len(symbols),'scanned_count':len(rows),'data_found_count':len(rows),'short_history_count':sum(1 for x in rows if x.get('status')=='SHORT_HISTORY'),'data_unavailable_count':len(unavailable),'provider_error_count':len(provider_errors),'opportunity_count':opp,'error_count':len(provider_errors),
      'rows':rows,
      'leaders':[x for x in rows if x.get('opportunity')][:50],
      'strategy_counts':strategy_counts,
      'strategy_leaders':strategy_leaders,
      'method':'DÖNÜŞ AVCISI v3.3','data_source':'TradingView WebSocket → İş Yatırım fallback','data_note':'Ana tarama kaynağı TradingView WebSocket günlük verisidir; bulunamazsa İş Yatırım tarihsel günlük verisine düşülür. TradingView ücretsiz/kimliksiz erişimde gecikmeli olabilir; sinyaller yatırım tavsiyesi değildir.',
      'unavailable_symbols':[x['symbol'] for x in unavailable],'provider_error_symbols':[x['symbol'] for x in provider_errors]
    }
    payload = json_safe(payload)
    (DATA/'latest.json').write_text(
        json.dumps(payload,ensure_ascii=False,indent=2,allow_nan=False),
        encoding='utf-8'
    )
    # Önceki taramadan kalan grafik dosyalarını temizle.
    CHARTS.mkdir(parents=True, exist_ok=True)
    for old_chart in CHARTS.glob('*.json'):
        try:
            old_chart.unlink()
        except Exception:
            pass

    for symbol,chart in chart_payloads.items():
        (CHARTS/f"{symbol}.json").write_text(
            json.dumps({
                'ok':True,
                'symbol':symbol,
                'source':'Dönüş Avcısı static OHLCV',
                'rows':chart
            },ensure_ascii=False),
            encoding='utf-8'
        )
    (HISTORY/f'{now.strftime("%Y-%m-%d_%H%M%S")}.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    build_performance()
    print(f'Tarama tamamlandı: {len(rows)}/{len(symbols)} veri bulundu | kısa geçmiş: {sum(1 for x in rows if x.get('status')=='SHORT_HISTORY')} | veri yok: {len(unavailable)} | hata: {len(provider_errors)} | fırsat: {opp}',flush=True)

if __name__=='__main__': main()

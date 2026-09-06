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
DATA=ROOT/'data'; HISTORY=DATA/'history'
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
        df, source = result if isinstance(result,tuple) else (result, getattr(provider,'name','BIST'))
        if df.empty:
            return {'symbol':symbol,'status':'DATA_UNAVAILABLE','error':'Veri yok'}
        rev=analyze_reversal(df)
        if not rev['ready']:
            return {'symbol':symbol,'source':source,'ready':False,'state':'NO_SETUP','status':'SHORT_HISTORY','history_bars':int(len(df)),'price':float(df.close.iloc[-1]),'confidence':0,'dip_score':0,'turn_score':0,'reasons':[rev.get('reason','Yeterli geçmiş yok')],'strategies':{}}
        return {'symbol':symbol,'source':source,'status':'ANALYZED',**rev,'strategies':strategy_scores(df,rev)}
    except DataUnavailable as e:
        return {'symbol':symbol,'status':'DATA_UNAVAILABLE','error':str(e)}
    except Exception as e:
        return {'symbol':symbol,'status':'PROVIDER_ERROR','error':str(e)}


def main():
    DATA.mkdir(exist_ok=True); HISTORY.mkdir(exist_ok=True)
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
    rows.sort(key=lambda x:(x.get('confidence',0),x.get('turn_score',0)),reverse=True)
    now=pd.Timestamp.now(tz='Europe/Istanbul')
    opp=sum(1 for x in rows if x.get('state')!='NO_SETUP')
    payload={
      'generated_at':now.isoformat(),'market':{'score':mscore,'regime':'POZİTİF' if mscore>=65 else 'NÖTR' if mscore>=45 else 'RİSK AZALT'},
      'universe_count':len(symbols),'attempted_count':len(symbols),'scanned_count':len(rows),'data_found_count':len(rows),'short_history_count':sum(1 for x in rows if x.get('status')=='SHORT_HISTORY'),'data_unavailable_count':len(unavailable),'provider_error_count':len(provider_errors),'opportunity_count':opp,'error_count':len(provider_errors),
      'rows':rows,'leaders':[x for x in rows if x.get('state')!='NO_SETUP'][:80],
      'method':'DÖNÜŞ AVCISI v3.3','data_source':'TradingView WebSocket → İş Yatırım fallback','data_note':'Ana tarama kaynağı TradingView WebSocket günlük verisidir; bulunamazsa İş Yatırım tarihsel günlük verisine düşülür. TradingView ücretsiz/kimliksiz erişimde gecikmeli olabilir; sinyaller yatırım tavsiyesi değildir.',
      'unavailable_symbols':[x['symbol'] for x in unavailable],'provider_error_symbols':[x['symbol'] for x in provider_errors]
    }
    (DATA/'latest.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    (HISTORY/f'{now.strftime("%Y-%m-%d_%H%M%S")}.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    build_performance()
    print(f'Tarama tamamlandı: {len(rows)}/{len(symbols)} veri bulundu | kısa geçmiş: {sum(1 for x in rows if x.get('status')=='SHORT_HISTORY')} | veri yok: {len(unavailable)} | hata: {len(provider_errors)} | fırsat: {opp}',flush=True)

if __name__=='__main__': main()

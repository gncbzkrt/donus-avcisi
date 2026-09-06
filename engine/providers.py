import json
import random
import re
import string
import time
import threading
from datetime import datetime, timedelta
import requests
import pandas as pd

try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

class ProviderError(Exception): pass
class DataUnavailable(ProviderError): pass

class TradingViewProvider:
    """BIST OHLCV via TradingView WebSocket (unauthenticated = delayed market data)."""
    name='TradingView WebSocket'
    WS_URL='wss://data.tradingview.com/socket.io/websocket'
    ORIGIN='https://www.tradingview.com'
    PERIOD_DAYS={'1d':1,'5d':5,'1mo':30,'3mo':90,'6mo':180,'1y':365,'2y':730,'5y':1825,'10y':3650,'max':3650}
    TF={'1d':'1D','1wk':'1W','1mo':'1M'}
    def __init__(self, timeout=12): self.timeout=timeout
    def _sid(self,prefix='cs'):
        return prefix+'_'+''.join(random.choice(string.ascii_lowercase+string.digits) for _ in range(12))
    def _packet(self,data): return f'~m~{len(data)}~m~{data}'
    def _msg(self,m,p): return self._packet(json.dumps({'m':m,'p':p},separators=(',',':')))
    def _parse(self,raw):
        out=[]
        for part in re.split(r'~m~\d+~m~',raw):
            if not part or part.startswith('~h~'): continue
            try: out.append(json.loads(part))
            except Exception: pass
        return out
    def history(self,symbol,period='2y',interval='1d'):
        if interval not in self.TF: raise ProviderError('TradingView adaptörü günlük veri sağlar')
        try: import websocket
        except Exception as e: raise ProviderError(f'websocket-client eksik: {e}')
        symbol=symbol.upper().replace('.IS','').replace('.E','')
        tv_symbol=f'BIST:{symbol}'; bars=max(int(self.PERIOD_DAYS.get(period,730)),10)
        session=self._sid(); periods={}; error=[None]; received=[False]
        def on_open(ws):
            ws.send(self._msg('set_auth_token',['unauthorized_user_token']))
            ws.send(self._msg('chart_create_session',[session,'']))
            cfg={'symbol':tv_symbol,'adjustment':'splits','session':'regular'}
            ws.send(self._msg('resolve_symbol',[session,'ser_1','='+json.dumps(cfg,separators=(',',':'))]))
            ws.send(self._msg('create_series',[session,'$prices','s1','ser_1',self.TF[interval],bars,'']))
        def on_message(ws,message):
            for packet in self._parse(message):
                if not isinstance(packet,dict): continue
                m=packet.get('m'); params=packet.get('p',[])
                if m=='timescale_update' and len(params)>=2 and isinstance(params[1],dict):
                    for candle in params[1].get('$prices',{}).get('s',[]):
                        v=candle.get('v',[])
                        if len(v)>=5:
                            try:
                                ts=int(v[0]); periods[ts]={'open':float(v[1]),'high':float(v[2]),'low':float(v[3]),'close':float(v[4]),'volume':float(v[5]) if len(v)>=6 and v[5] is not None else 0.0}
                            except Exception: pass
                    if periods: received[0]=True
                elif m in ('critical_error','symbol_error'):
                    error[0]=str(params); ws.close()
        def on_error(ws,err): error[0]=str(err)
        ws=websocket.WebSocketApp(f'{self.WS_URL}?type=chart',on_open=on_open,on_message=on_message,on_error=on_error,header=[f'Origin: {self.ORIGIN}'])
        t=threading.Thread(target=ws.run_forever,daemon=True); t.start(); start=time.time()
        while not received[0] and not error[0] and time.time()-start<self.timeout: time.sleep(.1)
        ws.close(); t.join(timeout=1)
        if error[0]: raise DataUnavailable(f'{symbol}: TradingView veri yok ({error[0][:180]})')
        if not periods: raise DataUnavailable(f'{symbol}: TradingView veri yok')
        df=pd.DataFrame.from_dict(periods,orient='index').sort_index()
        df.index=pd.to_datetime(df.index,unit='s',utc=True).tz_convert('Europe/Istanbul').tz_localize(None)
        return df[['open','high','low','close','volume']]


def _pick(row,names):
    for n in names:
        if n in row and row.get(n) not in (None,'','-'): return row.get(n)
    return None

def _num(v):
    if v is None:return None
    try:
        s=str(v).strip().replace('.','').replace(',','.') if isinstance(v,str) else v
        return float(s)
    except Exception:
        try:return float(v)
        except Exception:return None

class IsYatirimProvider:
    _lock=threading.Lock(); _last=0.0; name='İş Yatırım'
    BASE_URL='https://www.isyatirim.com.tr/_layouts/15/Isyatirim.Website/Common/Data.aspx/HisseTekil'
    def __init__(self,timeout=15,min_delay=.45):
        self.timeout=timeout; self.min_delay=float(min_delay); self.session=requests.Session(); self.session.headers.update({'User-Agent':'Mozilla/5.0 (Android) AppleWebKit/537.36 Chrome/140 Mobile Safari/537.36','Accept':'application/json,text/plain,*/*','Referer':'https://www.isyatirim.com.tr/'})
    def _throttle(self):
        with self._lock:
            wait=self.min_delay-(time.monotonic()-self.__class__._last)
            if wait>0: time.sleep(wait)
            self.__class__._last=time.monotonic()
    def history(self,symbol,period='2y',interval='1d'):
        days={'1y':370,'2y':760,'3y':1140,'5y':1900}.get(period,760); end=datetime.now(); start=end-timedelta(days=days)
        url=f'{self.BASE_URL}?hisse={symbol}&startdate={start.strftime("%d-%m-%Y")}&enddate={end.strftime("%d-%m-%Y")}'
        last=None
        for attempt in range(3):
            try:
                self._throttle(); r=self.session.get(url,timeout=self.timeout); r.raise_for_status(); rows=(r.json().get('value') or [])
                if not rows: raise DataUnavailable(f'{symbol}: İş Yatırım veri yok')
                parsed=[]
                for row in rows:
                    date=_pick(row,['HGDG_TARIH','TARIH','Date']); close=_num(_pick(row,['HGDG_KAPANIS','KAPANIS','Close']))
                    op=_num(_pick(row,['HGDG_ACILIS','ACILIS','OPEN','Open'])); hi=_num(_pick(row,['HGDG_EN_YUKSEK','HGDG_MAX','EN_YUKSEK','MAX','HIGH','High'])); lo=_num(_pick(row,['HGDG_EN_DUSUK','HGDG_MIN','EN_DUSUK','MIN','LOW','Low'])); vol=_num(_pick(row,['HGDG_ISLEM_HACIM','HGDG_HACIM','ISLEM_HACIM','HACIM','VOLUME','Volume']))
                    if date is None or close is None: continue
                    parsed.append({'date':date,'open':op if op is not None else close,'high':hi if hi is not None else close,'low':lo if lo is not None else close,'close':close,'volume':vol or 0.0})
                if not parsed: raise DataUnavailable(f'{symbol}: İş Yatırım veri yok')
                df=pd.DataFrame(parsed); df['date']=pd.to_datetime(df['date'],dayfirst=True,errors='coerce'); df=df.dropna(subset=['date','close']).sort_values('date').drop_duplicates('date').set_index('date')
                return df[['open','high','low','close','volume']].astype(float)
            except DataUnavailable: raise
            except Exception as e:
                last=e
                if attempt<2: time.sleep(1.25*(attempt+1))
        raise ProviderError(str(last))

class FallbackProvider:
    name='TradingView → İş Yatırım'
    def __init__(self,timeout=15,delay=.45):
        self.tv=TradingViewProvider(timeout=timeout); self.isy=IsYatirimProvider(timeout=timeout,min_delay=delay)
    def history(self,symbol,period='2y',interval='1d'):
        try: return self.tv.history(symbol,period,interval),'TradingView'
        except Exception as tv_err:
            try: return self.isy.history(symbol,period,interval),'İş Yatırım'
            except DataUnavailable: raise DataUnavailable(f'{symbol}: TradingView + İş Yatırım veri yok')
            except Exception as isy_err: raise ProviderError(f'{symbol}: TV={tv_err}; İşYatırım={isy_err}')

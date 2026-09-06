import numpy as np
from .indicators import ema, sma, atr, rsi, macd

def clamp(x):
    try:
        return float(max(0, min(100, x)))
    except Exception:
        return 0.0

def pct(a,b):
    return float(a/b-1) if b not in (0,None) else 0.0

def slope(s,n=10):
    if len(s)<=n:
        return 0.0
    return pct(float(s.iloc[-1]),float(s.iloc[-1-n]))

def strategy_scores(df,reversal=None):
    if df is None or len(df)<60:
        return {
            "daily":0.0,"swing":0.0,"trend":0.0,
            "mid_term":0.0,
            "reversal":round(float((reversal or {}).get("turn_score",0)),1)
        }

    c=df.close.astype(float)
    v=df.volume.astype(float)

    e20=ema(c,20)
    e50=ema(c,50)
    e200=ema(c,200)
    v20=sma(v,20)
    rr=rsi(c,14)
    m,ms,mh=macd(c)
    a=atr(df,14)

    price=float(c.iloc[-1])
    rsi_now=float(rr.iloc[-1]) if np.isfinite(rr.iloc[-1]) else 50
    rsi_prev=float(rr.iloc[-4]) if len(c)>=5 and np.isfinite(rr.iloc[-4]) else rsi_now
    volratio=float(v.iloc[-1]/max(float(v20.iloc[-1]),1))
    mh_now=float(mh.iloc[-1]) if np.isfinite(mh.iloc[-1]) else 0
    mh_prev=float(mh.iloc[-4]) if len(c)>=5 and np.isfinite(mh.iloc[-4]) else mh_now
    atr_ratio=float(a.iloc[-1]/max(price,1e-9)) if np.isfinite(a.iloc[-1]) else .03

    # GÜNLÜK — 1/5 seans
    ret1=pct(c.iloc[-1],c.iloc[-2])
    ret5=pct(c.iloc[-1],c.iloc[-6]) if len(c)>=6 else ret1

    daily=50
    daily+=np.clip(ret1*900,-12,12)
    daily+=np.clip(ret5*180,-12,12)
    daily+=10 if price>e20.iloc[-1] else -8
    daily+=8 if mh_now>mh_prev else -5
    daily+=10 if 45<=rsi_now<=68 else (4 if 35<=rsi_now<45 else -6)
    daily+=np.clip((volratio-1)*14,-8,12)
    daily-=6 if rsi_now>75 else 0

    # SWING — 5/20 seans
    ret20=pct(c.iloc[-1],c.iloc[-21]) if len(c)>=22 else ret5

    swing=50
    swing+=np.clip(ret20*120,-15,15)
    swing+=12 if price>e20.iloc[-1] else -8
    swing+=12 if e20.iloc[-1]>e50.iloc[-1] else -8
    swing+=8 if slope(e20,10)>0 else -5
    swing+=8 if mh_now>0 else -5
    swing+=7 if 45<=rsi_now<=70 else -5
    swing+=np.clip((volratio-1)*10,-7,10)
    swing-=5 if atr_ratio>.06 else 0

    # TREND — güçlü trend devamı
    trend=35
    trend+=22 if price>e20.iloc[-1] else -15
    trend+=18 if e20.iloc[-1]>e50.iloc[-1] else -14
    trend+=18 if e50.iloc[-1]>e200.iloc[-1] else -14
    trend+=10 if slope(e20,10)>0 else -8
    trend+=8 if slope(e50,20)>0 else -6
    trend+=8 if pct(c.iloc[-1],c.iloc[-61])>0 else -6
    trend+=5 if volratio>=.9 else 0

    # ORTA VADE — 1/6 ay
    ret60=pct(c.iloc[-1],c.iloc[-61]) if len(c)>=62 else ret20
    ret120=pct(c.iloc[-1],c.iloc[-121]) if len(c)>=122 else ret60

    mid=40
    mid+=np.clip(ret60*55,-15,18)
    mid+=np.clip(ret120*35,-12,15)
    mid+=15 if price>e200.iloc[-1] else -12
    mid+=12 if e50.iloc[-1]>e200.iloc[-1] else -10
    mid+=8 if slope(e200,40)>0 else -6
    mid+=5 if 40<=rsi_now<=72 else -4
    mid-=5 if atr_ratio>.07 else 0

    return {
        "daily":round(clamp(daily),1),
        "swing":round(clamp(swing),1),
        "trend":round(clamp(trend),1),
        "mid_term":round(clamp(mid),1),
        "reversal":round(clamp(float((reversal or {}).get("turn_score",0))),1)
    }

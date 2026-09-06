import math
import numpy as np
from .indicators import ema, sma, atr, rsi, macd

def clamp(x,lo=0,hi=100):
    try:
        return float(max(lo,min(hi,x)))
    except Exception:
        return 0.0

def pct(a,b):
    return float(a/b-1) if b not in (0,None) else 0.0

def slope(s,n):
    if len(s)<=n:
        return 0.0
    return pct(float(s.iloc[-1]),float(s.iloc[-1-n]))

def centered(v,target,width):
    return clamp(100-abs(v-target)/width*100)

def trend_score(price,e20,e50,e200,s20,s50,ret60,vol):
    vals=[
        100 if price>e20 else 0,
        100 if e20>e50 else 0,
        100 if e50>e200 else 0,
        clamp(50+s20*900),
        clamp(50+s50*700),
        clamp(50+ret60*180),
        clamp(vol*55)
    ]
    raw=sum(vals)/len(vals)
    return round(clamp(50+(raw-50)*0.90,5,95),1)

def strategy_scores(df,reversal=None):
    n=len(df)
    zero={
        "daily":0.0,
        "swing":0.0,
        "trend":0.0,
        "mid_term":0.0,
        "reversal":0.0
    }

    if n<60:
        return zero

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
    e20v=float(e20.iloc[-1])
    e50v=float(e50.iloc[-1])
    e200v=float(e200.iloc[-1])
    vr=float(v.iloc[-1]/max(float(v20.iloc[-1]),1))
    r=float(rr.iloc[-1]) if np.isfinite(rr.iloc[-1]) else 50
    atrr=float(a.iloc[-1]/max(price,1e-9)) if np.isfinite(a.iloc[-1]) else .04

    ret1=pct(c.iloc[-1],c.iloc[-2])
    ret5=pct(c.iloc[-1],c.iloc[-6]) if n>=6 else 0
    ret20=pct(c.iloc[-1],c.iloc[-21]) if n>=22 else 0
    ret60=pct(c.iloc[-1],c.iloc[-61]) if n>=62 else 0
    ret120=pct(c.iloc[-1],c.iloc[-121]) if n>=122 else 0

    mom1=clamp(50+math.tanh(ret1/.025)*40)
    mom5=clamp(50+math.tanh(ret5/.08)*40)
    mom20=clamp(50+math.tanh(ret20/.20)*40)
    mom60=clamp(50+math.tanh(ret60/.40)*40)
    mom120=clamp(50+math.tanh(ret120/.60)*40)

    ema20s=clamp(50+math.tanh((price/e20v-1)/.06)*40)
    ema50s=clamp(50+math.tanh((price/e50v-1)/.10)*40)
    volscore=clamp(50+math.tanh((vr-1)/.55)*40)

    macd_now=float(mh.iloc[-1]) if np.isfinite(mh.iloc[-1]) else 0
    macd_prev=float(mh.iloc[-5]) if n>=5 and np.isfinite(mh.iloc[-5]) else macd_now
    macd_scale=float(np.nanstd(mh.tail(60))) if n>=60 else abs(macd_now)
    macd_turn=clamp(50+math.tanh((macd_now-macd_prev)/max(macd_scale,1e-9))*40)
    macd_pos=clamp(50+math.tanh(macd_now/max(macd_scale,1e-9))*40)

    rsi_daily=centered(r,58,28)
    rsi_swing=centered(r,58,32)
    rsi_mid=centered(r,58,38)

    vol_penalty=clamp(100-atrr*900)

    daily=(
        .25*mom1+.20*mom5+.15*ema20s+
        .15*macd_turn+.15*rsi_daily+.10*volscore
    )
    daily=clamp(50+(daily-50)*.90,5,95)

    swing=(
        .25*mom20+.18*ema20s+.18*ema50s+
        .12*macd_pos+.10*rsi_swing+.10*volscore+.07*vol_penalty
    )
    swing=clamp(50+(swing-50)*.90,5,95)

    trend=trend_score(
        price,e20v,e50v,e200v,
        slope(e20,10),slope(e50,20),ret60,vr
    )

    mid=(
        .24*mom60+.18*mom120+
        .18*(100 if price>e200v else 0)+
        .15*(100 if e50v>e200v else 0)+
        .10*clamp(50+slope(e200,40)*700)+
        .08*rsi_mid+.07*vol_penalty
    )
    mid=clamp(50+(mid-50)*.90,5,95)

    rev=0.0
    if reversal and reversal.get("ready"):
        rev=clamp(float(reversal.get("turn_score",0)),5,95)

    return {
        "daily":round(daily,1),
        "swing":round(swing,1),
        "trend":round(trend,1),
        "mid_term":round(mid,1),
        "reversal":round(rev,1)
    }

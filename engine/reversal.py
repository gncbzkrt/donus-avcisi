import numpy as np
from .indicators import ema, sma, atr, rsi, macd

def clamp(x): return float(max(0, min(100, x)))

def analyze_reversal(df):
    if len(df) < 220:
        return {"ready": False, "reason": "Yeterli geçmiş yok"}

    c,h,l,v=df.close,df.high,df.low,df.volume
    a=atr(df); rr=rsi(c); m,ms,mh=macd(c)
    e20,e50,e200=ema(c,20),ema(c,50),ema(c,200); v20=sma(v,20)

    price=float(c.iloc[-1])
    low120=float(l.iloc[-120:].min()); high120=float(h.iloc[-120:].max())
    drawdown=clamp(100*(1-price/high120))
    dist_low=abs(price-low120)/max(price,1e-9)

    ret=c.pct_change()
    downside=ret.where(ret<0,0)
    down20=abs(downside.tail(20).mean())
    down60=abs(downside.tail(60).mean())+1e-9
    downside_score=clamp(60+30*(1-down20/down60))
    atr_ratio=float(a.iloc[-1]/max(price,1e-9))
    atr_score=clamp(70-500*max(0,atr_ratio-0.025))
    ste=0.65*downside_score+0.35*atr_score

    near_low=clamp(100*(1-dist_low/0.12))
    support_hits=int((l.tail(30) <= l.tail(30).rolling(10).min()*1.015).sum())
    support_score=clamp(near_low+min(20,support_hits))
    dip_pressure=0.7*near_low+0.3*support_score

    body=(c.iloc[-1]-c.iloc[-2])/max(c.iloc[-2],1e-9)
    vol_ratio=float(v.iloc[-1]/max(v20.iloc[-1],1))
    close_location=float((c.iloc[-1]-l.iloc[-1])/max(h.iloc[-1]-l.iloc[-1],1e-9))
    aue=clamp(45+25*min(max(body/0.03,-1),1)+20*min(vol_ratio/2,1)+10*close_location)

    up=ret.where(ret>0).tail(40); dn=abs(ret.where(ret<0).tail(40))
    asym=clamp(50+35*((up.mean()+1e-9)/(dn.mean()+1e-9)-1))

    prior_low=float(l.iloc[-21:-1].min())
    sweep=(l.iloc[-1] < prior_low*0.995 and c.iloc[-1] > prior_low)

    rsi_turn=clamp(50+(rr.iloc[-1]-rr.iloc[-5])*3)
    macd_turn=clamp(50+(mh.iloc[-1]-mh.iloc[-5])*150)
    trend=clamp(50+20*np.sign(e20.iloc[-1]-e20.iloc[-5])
                   +15*np.sign(e50.iloc[-1]-e50.iloc[-10])
                   +15*(1 if price>e20.iloc[-1] else -1))

    dip_score=clamp(.22*drawdown+.22*dip_pressure+.24*ste+.12*rsi_turn+.10*asym+.10*(100 if sweep else 0))
    turn_score=clamp(.30*aue+.20*rsi_turn+.18*macd_turn+.17*asym+.10*trend+.05*(100 if sweep else 0))
    confidence=clamp(.55*dip_score+.45*turn_score)

    if confidence>=85 and turn_score>=75: state="CONFIRMED_REVERSAL"
    elif dip_score>=78 and turn_score>=58: state="EARLY_REVERSAL"
    elif dip_score>=70: state="BASE_FORMING"
    else: state="NO_SETUP"

    stop=price-max(float(a.iloc[-1])*1.8,price*.035)
    risk=max(price-stop,price*.01)
    target1=price+risk*1.8; target2=price+risk*3

    reasons=[]
    if ste>=70: reasons.append("Satıcı tükenmesi")
    if dip_pressure>=70: reasons.append("Dip basıncı yüksek")
    if aue>=65: reasons.append("Alıcı uyanışı")
    if asym>=60: reasons.append("Pozitif asimetri")
    if sweep: reasons.append("Dip süpürmesi / başarısız kırılım")
    if rsi_turn>=60: reasons.append("RSI toparlanması")
    if macd_turn>=60: reasons.append("MACD momentumu iyileşiyor")

    return {
        "ready":True,"state":state,"price":round(price,4),
        "dip_score":round(dip_score,1),"turn_score":round(turn_score,1),
        "confidence":round(confidence,1),"seller_exhaustion":round(ste,1),
        "dip_pressure":round(dip_pressure,1),"buyer_awakening":round(aue,1),
        "asymmetry":round(asym,1),
        "technicals": {
            "rsi14": round(float(rr.iloc[-1]),1),
            "macd": round(float(m.iloc[-1]),4),
            "macd_signal": round(float(ms.iloc[-1]),4),
            "macd_hist": round(float(mh.iloc[-1]),4),
            "ema20": round(float(e20.iloc[-1]),4),
            "ema50": round(float(e50.iloc[-1]),4),
            "ema200": round(float(e200.iloc[-1]),4),
            "atr14": round(float(a.iloc[-1]),4),
            "volume_ratio20": round(float(vol_ratio),2),
            "close_location": round(float(close_location),2)
        },"failed_breakdown":bool(sweep),
        "reasons":reasons[:6],"stop":round(stop,4),
        "target1":round(target1,4),"target2":round(target2,4),
        "risk_reward_1":round((target1-price)/risk,2),
        "risk_reward_2":round((target2-price)/risk,2)
    }

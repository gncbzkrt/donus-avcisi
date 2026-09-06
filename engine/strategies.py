from .indicators import ema, sma

def strategy_scores(df, reversal):
    c,v=df.close,df.volume
    e20,e50,e200=ema(c,20),ema(c,50),ema(c,200)
    v20=sma(v,20); price=float(c.iloc[-1])
    volratio=float(v.iloc[-1]/max(v20.iloc[-1],1))

    trend=50
    trend += 20 if price>e20.iloc[-1] else -15
    trend += 15 if e20.iloc[-1]>e50.iloc[-1] else -10
    trend += 15 if e50.iloc[-1]>e200.iloc[-1] else -10
    trend=max(0,min(100,trend))

    swing=max(0,min(100,55+(volratio-1)*12+(10 if price>e20.iloc[-1] else -8)))
    daily=max(0,min(100,50+(volratio-1)*18+(8 if c.iloc[-1]>c.iloc[-2] else -8)))
    mid=max(0,min(100,45+.5*trend+(8 if price>e200.iloc[-1] else -8)))

    return {"daily":round(daily,1),"swing":round(swing,1),
            "trend":round(trend,1),"mid_term":round(mid,1),
            "reversal":round(reversal["turn_score"],1)}

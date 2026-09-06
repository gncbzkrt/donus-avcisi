import numpy as np
import pandas as pd

def ema(s, n): return s.ewm(span=n, adjust=False).mean()
def sma(s, n): return s.rolling(n).mean()

def atr(df, n=14):
    prev = df.close.shift(1)
    tr = pd.concat([(df.high-df.low), (df.high-prev).abs(), (df.low-prev).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()

def rsi(s, n=14):
    d=s.diff()
    up=d.clip(lower=0).ewm(alpha=1/n, adjust=False).mean()
    dn=(-d.clip(upper=0)).ewm(alpha=1/n, adjust=False).mean()
    rs=up/dn.replace(0,np.nan)
    return 100-(100/(1+rs))

def macd(s):
    m=ema(s,12)-ema(s,26)
    sig=ema(m,9)
    return m,sig,m-sig

def obv(df):
    direction=np.sign(df.close.diff()).fillna(0)
    return (direction*df.volume).cumsum()

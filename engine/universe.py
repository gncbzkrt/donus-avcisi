import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UNIVERSE_FILE = ROOT / 'data' / 'universe.json'

FALLBACK = [
    'AKBNK','ALARK','ASELS','ASTOR','BIMAS','BRSAN','CCOLA','CIMSA','DOAS','ECILC',
    'EKGYO','ENKAI','EREGL','FROTO','GARAN','HALKB','HEKTS','ISCTR','KCHOL','KRDMD',
    'MGROS','ODAS','OYAKC','PASEU','PETKM','PGSUS','SAHOL','SASA','SISE','SKBNK',
    'TAVHL','TCELL','THYAO','TOASO','TUPRS','ULKER','VAKBN','YKBNK','ARCLK','DOHOL',
    'ENJSA','ISMEN','KOZAA','KONTR','MAVI','MIATK','OYAKC','SMRTG','TABGD','TATEN',
    'TKFEN','TTKOM','TSKB','TURSG','VESBE','VESTL','YEOTK','ZOREN','AHGAZ','AKSEN',
    'AYGAZ','CANTE','CWENE','GESAN','KONYA','KONTR','KORDS','LOGO','MPARK','OTKAR',
    'SOKM','TTRAK','TURSG','VERUS','AGHOL','AKSA','AKSUE','ALBRK','ALFAS','ALCTL',
    'ALGYO','ANELE','ANGEN','ANHYT','ANSGR','ARASE','ARDYZ','ARENA','ASUZU','ATATP',
    'AVOD','AYDEM','BAGFS','BANVT','BARMA','BASGZ','BERA','BFREN','BIENY','BIOEN',
    'BIZIM','BLCYT','BMSTL','BNTAS','BOBET','BRISA','BRKO','BRKSN','BRYAT','BSOKE',
    'BTCIM','BUCIM','BURCE','BURVA','BVSAN','BYDNR','CANTE','CELHA','CEMAS','CEMTS',
    'CLEBI','CMBTN','CMENT','CONSE','CRDFA','CRFSA','CUSAN','CVKMD','CWENE','DAGI',
    'DAPGM','DARDL','DGNMO','DITAS','DMRGD','DMSAS','DNISI','DOAS','DOBUR','DOGUB',
    'DOKTA','DURDO','DYOBY','DZGYO','EBEBK','ECZYT','EDATA','EDIP','EGEEN','EGEPO',
    'EGGUB','EGPRO','EGSER','EKSUN','ELITE','EMKEL','EMNIS','ESEN','EUPWR','FADE',
    'FENER','FORTE','GENIL','GESAN','GLRMK','GOLTS','GOODY','GRSEL','GWIND','GUBRF',
    'HATSN','HDFGS','HLGYO','IHLAS','IHLGM','INDES','INVEO','IPEKE','ISDMR','ISFIN',
    'ISGYO','IZENR','IZMDC','JANTS','KAPLM','KARSN','KARTN','KCAER','KLGYO','KLRHO',
    'KMPUR','KNFRT','KONKA','KONYA','KOPOL','KORDS','KOTON','KRDMA','KRDMB','KRDMD',
    'KRVGD','KTLEV','KTSKR','KUYAS','LIDER','LINK','LMKDC','LYDHO','MAGEN','MAKIM',
    'MARBL','MARTI','MEDTR','MEGMT','MEPET','METRO','MGROS','MNDRS','MNDTR','MOBTL',
    'NETAS','NTGAZ','NUHCM','OBAMS','OBASE','OFSYM','ONCSM','ONRYT','ORGE','OSTIM',
    'OYAKC','OZKGY','PAGYO','PARSN','PCILT','PEKGY','PENTA','PETUN','PINSU','PKART',
    'PLTUR','PNLSN','PNSUT','POLHO','QUAGR','RALYH','RAYSG','REEDR','RGYAS','RNPOL',
    'RODRG','RYSAS','SAFKR','SAMAT','SANKO','SELEC','SELGD','SELVA','SILVR','SKBNK',
    'SMART','SNGYO','SOKE','SUMAS','SURGY','SUWEN','TARKM','TATGD','TBORG','TEZOL',
    'TKNSA','TMSN','TRCAS','TRGYO','TRILC','TSKB','TSPOR','TTKOM','TUKAS','TURGG',
    'ULUSE','USAK','VAKKO','VANGD','VBTYZ','VERTU','VESBE','VKGYO','VRGYO','YATAS',
    'YAYLA','YESIL','YGGYO','YKBNK','YUNSA','YYLGD','ZEDUR','ZOREN'
]

def load_universe():
    if UNIVERSE_FILE.exists():
        try:
            data = json.loads(UNIVERSE_FILE.read_text(encoding='utf-8'))
            symbols = [str(x.get('symbol','')).upper() for x in data if x.get('symbol')]
            symbols = sorted(set(s for s in symbols if 2 <= len(s) <= 6))
            if symbols:
                return symbols
        except Exception:
            pass
    return sorted(set(FALLBACK))

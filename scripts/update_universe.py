import json
import re
from pathlib import Path
import requests
try:
    from lxml import html
except Exception:
    html = None

OUT = Path(__file__).resolve().parents[1] / 'data' / 'universe.json'
KAP_URL = 'https://kap.org.tr/tr/bist-sirketler'
FALLBACK_URL = 'https://raw.githubusercontent.com/ahmeterenodaci/Istanbul-Stock-Exchange--BIST--including-symbols-and-logos/refs/heads/main/without_logo.json'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Donus-Avcisi/2.9)'}


def clean_code(text):
    # KAP can show current/previous aliases together, e.g. "A1CAP ACP".
    tokens = re.findall(r'(?<![A-Z0-9])([A-Z0-9]{2,6})(?![A-Z0-9])', str(text).upper())
    for s in tokens:
        if s.startswith('X'):
            continue
        if s in {'BIST', 'PAY', 'FON', 'KAP'}:
            continue
        return s
    return None


def fetch_kap():
    r = requests.get(KAP_URL, headers=HEADERS, timeout=30)
    r.raise_for_status()
    found = {}
    if html is not None:
        doc = html.fromstring(r.content)
        # KAP satırındaki ilk hücre şirket kodudur. Denetçi/diğer şirket
        # bağlantılarını toplamak 756 şirketi 1200+ sembole şişiriyordu.
        nodes = doc.xpath('//tr/td[1]/a[contains(@href,"/tr/sirket-bilgileri/ozet/")]')
        for a in nodes:
            raw = ' '.join(a.itertext()).strip()
            code = clean_code(raw)
            if code:
                found[code] = raw
    if len(found) < 700:
        # HTML varyantlarında tablo hücreleri farklı render edilebilir.
        text = r.text
        for m in re.finditer(r'<tr[^>]*>\s*<td[^>]*>\s*<a[^>]+href=["\'][^"\']*/tr/sirket-bilgileri/ozet/[^"\']+["\'][^>]*>(.*?)</a>', text, re.I | re.S):
            raw = re.sub(r'<[^>]+>', ' ', m.group(1))
            code = clean_code(raw)
            if code:
                found.setdefault(code, re.sub(r'\s+', ' ', raw).strip())
    if len(found) < 700:
        raise RuntimeError(f'KAP listesi beklenenden küçük: {len(found)}')
    return found


def fetch_fallback():
    r = requests.get(FALLBACK_URL, headers=HEADERS, timeout=25)
    r.raise_for_status()
    found = {}
    for x in r.json():
        s = str(x.get('symbol', '')).upper().strip()
        if 2 <= len(s) <= 6 and not s.startswith('X'):
            found[s] = x.get('name', '')
    return found


def main():
    current = json.loads(OUT.read_text(encoding='utf-8')) if OUT.exists() else []
    current_map = {str(x.get('symbol','')).upper().strip(): x.get('name','') for x in current if x.get('symbol')}
    try:
        kap = fetch_kap()
        # KAP is authoritative: replace the old broad list with the current BIST company universe.
        merged = {s: kap[s] for s in kap}
        source = f'KAP ({len(merged)} şirket)'
    except Exception as e:
        try:
            fb = fetch_fallback()
            merged = dict(current_map)
            merged.update(fb)
            source = f'fallback GitHub + mevcut ({len(merged)} sembol)'
            print(f'KAP güncellemesi alınamadı: {e}')
        except Exception as e2:
            merged = current_map
            source = f'mevcut yerel evren ({len(merged)} sembol)'
            print(f'KAP/fallback başarısız: {e2}')

    clean = [{'symbol': s, 'name': merged[s]} for s in sorted(merged)]
    OUT.write_text(json.dumps(clean, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Evren güncellendi: {len(clean)} BIST şirketi | kaynak: {source}')
    if len(clean) < 750:
        print('UYARI: KAP canlı listesi alınamadıysa yerel/yedek evren kullanılmış olabilir.')


if __name__ == '__main__':
    main()

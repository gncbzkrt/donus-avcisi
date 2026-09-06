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

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Donus-Avcisi/4.2)'
}

def clean_code(text):
    tokens = re.findall(
        r'(?<![A-Z0-9])([A-Z0-9]{2,6})(?![A-Z0-9])',
        str(text).upper()
    )
    for s in tokens:
        if s.startswith('X'):
            continue
        if s in {'BIST','PAY','FON','KAP'}:
            continue
        return s
    return None

def fetch_kap():
    r = requests.get(KAP_URL, headers=HEADERS, timeout=30)
    r.raise_for_status()

    # KAP sayfasının kendi resmi şirket sayısını oku.
    m = re.search(r'(\d+)\s+Şirket Bulundu', r.text, re.I)
    reported_count = int(m.group(1)) if m else 756

    found = {}

    if html is not None:
        doc = html.fromstring(r.content)

        nodes = doc.xpath(
            '//tr/td[1]/a[contains(@href,"/tr/sirket-bilgileri/ozet/")]'
        )

        for a in nodes:
            raw = ' '.join(a.itertext()).strip()
            code = clean_code(raw)
            if code and code not in found:
                found[code] = raw

    if len(found) < 700:
        text = r.text
        for m in re.finditer(
            r'<tr[^>]*>\s*<td[^>]*>\s*<a[^>]+href=["\'][^"\']*/tr/sirket-bilgileri/ozet/[^"\']+["\'][^>]*>(.*?)</a>',
            text,
            re.I | re.S
        ):
            raw = re.sub(r'<[^>]+>', ' ', m.group(1))
            code = clean_code(raw)
            if code:
                found.setdefault(
                    code,
                    re.sub(r'\s+', ' ', raw).strip()
                )

    if len(found) < 700:
        raise RuntimeError(
            f'KAP listesi beklenenden küçük: {len(found)}'
        )

    # KAP'ın resmi sayaç değeri bizim üst sınırımızdır.
    if len(found) > reported_count:
        print(
            f'KAP DOM fazlası temizleniyor: '
            f'{len(found)} -> {reported_count}'
        )
        found = dict(list(found.items())[:reported_count])

    if len(found) != reported_count:
        raise RuntimeError(
            f'KAP evren uyuşmazlığı: bulunan={len(found)}, '
            f'resimli_sayi={reported_count}'
        )

    return found, reported_count

def fetch_fallback():
    r = requests.get(FALLBACK_URL, headers=HEADERS, timeout=25)
    r.raise_for_status()

    found = {}

    for x in r.json():
        s = str(x.get('symbol','')).upper().strip()
        if 2 <= len(s) <= 6 and not s.startswith('X'):
            found[s] = x.get('name','')

    return found

def main():
    current = (
        json.loads(OUT.read_text(encoding='utf-8'))
        if OUT.exists() else []
    )

    current_map = {
        str(x.get('symbol','')).upper().strip(): x.get('name','')
        for x in current
        if x.get('symbol')
    }

    try:
        kap, count = fetch_kap()

        merged = dict(kap)
        source = f'KAP ({count} şirket)'

    except Exception as e:
        print(f'KAP güncellemesi alınamadı: {e}')

        # Fallback artık mevcut evreni şişirmeyecek.
        if current_map:
            merged = current_map
            source = f'mevcut yerel evren ({len(merged)} sembol)'
        else:
            fb = fetch_fallback()
            merged = dict(fb)
            source = f'fallback ({len(merged)} sembol)'

    clean = [
        {'symbol': s, 'name': merged[s]}
        for s in sorted(merged)
    ]

    OUT.write_text(
        json.dumps(clean, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )

    print(
        f'Evren güncellendi: {len(clean)} BIST şirketi | kaynak: {source}'
    )

if __name__ == '__main__':
    main()

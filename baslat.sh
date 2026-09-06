#!/data/data/com.termux/files/usr/bin/bash
set -e
cd "$(dirname "$0")"
printf "\nDÖNÜŞ AVCISI v3.7 başlatılıyor...\n"
pkg install tur-repo -y >/dev/null 2>&1 || true
pkg install python-numpy python-pandas python-scipy python-lxml -y >/dev/null 2>&1 || true
python -c "import numpy,pandas,scipy,requests,tzdata,websocket" >/dev/null 2>&1 || pip install -q -r requirements.txt
python -c "import truststore" >/dev/null 2>&1 || pip install -q truststore
mkdir -p data/history
printf "\nKAP BIST şirket evreni güncelleniyor...\n"
python scripts/update_universe.py || true
RH_WORKERS=${RH_WORKERS:-3} RH_DELAY=${RH_DELAY:-0.45} RH_TIMEOUT=${RH_TIMEOUT:-15} python -m engine.run_scan
printf "\nTarama tamamlandı.\nUygulama: http://127.0.0.1:8080/app/\n"
python server.py

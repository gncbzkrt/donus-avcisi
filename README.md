# DÖNÜŞ AVCISI v3.6

BIST için bağımsız karar destek PWA'sı.

## v3.6 veri mimarisi
- KAP: şirket evreni.
- İş Yatırım tarihsel günlük veri: ana tarama kaynağı.
- TradingView: hisse detayında canlı grafik.
- Yahoo Finance: ana tarama kaynağından çıkarıldı.

İş Yatırım verisi web sitesindeki tarihsel fiyat endpoint'i üzerinden alınır. Bu adaptör resmi bir İş Yatırım API ürünü değildir; kullanım koşulları ve makul istek hızına uyulmalıdır.

## Termux
```bash
chmod +x baslat.sh
bash baslat.sh
```
Varsayılan olarak 2 paralel iş ve 0.35 sn istek aralığı kullanılır. Amaç veri sağlayıcısını gereksiz yüklememektir.

## Sonuç sayaçları
- KAP evreni
- Denenen
- Analiz edilen
- Veri yok
- Sağlayıcı hatası
- Fırsat

Uygun olmayan hisseler fırsat ekranına çıkarılmaz.


## v3.6 veri mimarisi

Tarama motoru artık TradingView günlük OHLCV verisini TradingView WebSocket üzerinden birincil kaynak olarak kullanır. Veri bulunamazsa İş Yatırım tarihsel günlük verisine düşer. TradingView verileri varsayılan olarak yaklaşık 15 dakika gecikmeli olabilir; gerçek zamanlı BIST veri erişimi TradingView hesap/veri paketi koşullarına bağlıdır. TradingView WebSocket kişisel/eğitim amaçlı kullanım için yayımlanmıştır; bu proje kişisel kullanım içindir.


## v4.0 Release
- BIST mum grafik
- EMA20/50/200
- Hacim
- RSI14 ve MACD
- Giriş/Stop/H1/H2 seviyeleri
- TradingView yalnız harici ayrıntılı grafik için

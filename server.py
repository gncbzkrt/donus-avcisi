from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import subprocess,sys,threading,json,urllib.parse
ROOT=Path(__file__).resolve().parent
SCANNING=False
class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*a,**kw): super().__init__(*a,directory=str(ROOT),**kw)
    def do_GET(self):
        parsed=urllib.parse.urlparse(self.path)
        if parsed.path.rstrip('/')=='/api/chart':
            q=urllib.parse.parse_qs(parsed.query)
            symbol=(q.get('symbol',[''])[0] or '').upper().strip()
            if not symbol or not symbol.replace('.','').isalnum() or len(symbol)>20:
                self.send_response(400); self.end_headers(); self.wfile.write(b'{\"ok\":false,\"error\":\"Gecersiz sembol\"}'); return
            try:
                from engine.providers import FallbackProvider
                provider=FallbackProvider(timeout=15,delay=0.2)
                result=provider.history(symbol,period='1y')
                df=result[0] if isinstance(result,tuple) else result
                if df is None or df.empty:
                    raise RuntimeError('Grafik verisi bulunamadi')
                cols={c.lower():c for c in df.columns}
                datecol=cols.get('date') or cols.get('datetime') or cols.get('timestamp')
                if datecol is None:
                    df=df.reset_index(); cols={c.lower():c for c in df.columns}; datecol=cols.get('date') or cols.get('datetime') or cols.get('timestamp') or df.columns[0]
                rows=[]
                for _,r in df.tail(180).iterrows():
                    def num(k):
                        c=cols.get(k);
                        return None if c is None else (float(r[c]) if r[c]==r[c] else None)
                    d=r[datecol]
                    try: ds=d.isoformat()
                    except Exception: ds=str(d)
                    rows.append({'date':ds[:10],'open':num('open'),'high':num('high'),'low':num('low'),'close':num('close'),'volume':num('volume')})
                payload={'ok':True,'symbol':symbol,'source':result[1] if isinstance(result,tuple) and len(result)>1 else 'BIST','rows':rows}
                body=json.dumps(payload,ensure_ascii=False).encode('utf-8')
                self.send_response(200); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Cache-Control','no-store'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body); return
            except Exception as e:
                body=json.dumps({'ok':False,'error':str(e)},ensure_ascii=False).encode('utf-8')
                self.send_response(502); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body); return
        return super().do_GET()

    def do_POST(self):
        global SCANNING
        if self.path.rstrip('/')=='/api/scan':
            if SCANNING:
                self.send_response(409); self.end_headers(); self.wfile.write(b'{"ok":false,"message":"Tarama zaten calisiyor"}'); return
            SCANNING=True
            def job():
                global SCANNING
                try: subprocess.run([sys.executable,'-m','engine.run_scan'],cwd=ROOT,check=False)
                finally: SCANNING=False
            threading.Thread(target=job,daemon=True).start()
            body=b'{"ok":true,"message":"Tarama baslatildi"}'
            self.send_response(202); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body); return
        self.send_response(404); self.end_headers()
    def log_message(self,fmt,*args):
        if not self.path.endswith(('.json','.png','.css','.js')): super().log_message(fmt,*args)
if __name__=='__main__':
    print('DÖNÜŞ AVCISI v3.8: http://127.0.0.1:8080/app/')
    ThreadingHTTPServer(('0.0.0.0',8080),Handler).serve_forever()

const VERSION='v4.2';
let DATA=null, PERF=null, mode='all';
const favKey='donus_avcisi_favoriler_v26';
const obsKey='donus_avcisi_gozlemler_v26';
const oldFavKey='donus_avcisi_favoriler_v25';
const oldObsKey='donus_avcisi_gozlemler_v25';
const $=s=>document.querySelector(s);
const themeKey='donus_avcisi_tema_v26';
function applyTheme(t){const theme=t==='light'?'light':'dark';document.documentElement.dataset.theme=theme;localStorage.setItem(themeKey,theme);document.querySelectorAll('[data-theme-choice]').forEach(b=>b.classList.toggle('active',b.dataset.themeChoice===theme));const m=document.querySelector('meta[name=theme-color]');if(m)m.content=theme==='light'?'#f4f6f8':'#080b10';}
function initTheme(){applyTheme(localStorage.getItem(themeKey)||'dark')}

function readJson(k,fallback){try{return JSON.parse(localStorage.getItem(k)||JSON.stringify(fallback))}catch{return fallback}}
function getFavs(){let x=readJson(favKey,null);if(x===null){x=readJson(oldFavKey,null);if(x===null)x=readJson('donus_avcisi_favoriler_v24',{});if(Object.keys(x||{}).length)localStorage.setItem(favKey,JSON.stringify(x||{}))}return x||{}}
function saveFavs(x){localStorage.setItem(favKey,JSON.stringify(x))}
function getObs(){let x=readJson(obsKey,null);if(x===null){x=readJson(oldObsKey,null);if(x===null)x=readJson('donus_avcisi_gozlemler_v24',{});if(Object.keys(x||{}).length)localStorage.setItem(obsKey,JSON.stringify(x||{}))}return x||{}}
function saveObs(x){localStorage.setItem(obsKey,JSON.stringify(x))}
const money=x=>x==null||Number.isNaN(Number(x))?'—':Number(x).toLocaleString('tr-TR',{maximumFractionDigits:2,minimumFractionDigits:0});
const pct=x=>(x==null||Number.isNaN(Number(x))?'—':`${Number(x)>=0?'+':''}${Number(x).toFixed(2)}%`);
function toast(t){const e=$('#toast');e.textContent=t;e.classList.add('show');clearTimeout(window.__toast);window.__toast=setTimeout(()=>e.classList.remove('show'),1900)}
function stateLabel(x){return ({CONFIRMED_REVERSAL:'DÖNÜŞ TEYİTLİ',EARLY_REVERSAL:'ERKEN DÖNÜŞ',BASE_FORMING:'DİP OLUŞUYOR',STRATEGY_SETUP:'STRATEJİ FIRSATI',NO_SETUP:'İZLE'})[x]||'İZLE'}
function strategyLabel(x){return ({daily:'Günlük',swing:'Swing',trend:'Trend',mid_term:'Orta Vade',reversal:'Dipten Dönüş'})[x]||x}
function score(x){return mode==='all'?Number(x.confidence||0):Number(x.strategies?.[mode]||0)}
function isFav(s){return !!getFavs()[s]}
function observeFavorites(){
  if(!DATA)return;
  const f=getFavs(),o=getObs(),ts=DATA.generated_at||new Date().toISOString(),day=String(ts).slice(0,10);
  for(const symbol of Object.keys(f)){
    const x=DATA.rows.find(a=>a.symbol===symbol); if(!x||x.price==null)continue;
    o[symbol]=o[symbol]||[]; const last=o[symbol][o[symbol].length-1];
    if(!last||String(last.ts).slice(0,10)!==day)o[symbol].push({ts,price:Number(x.price),confidence:Number(x.confidence||0),state:x.state});
  }
  saveObs(o);
}
function toggleFav(x){
  const f=getFavs();
  if(f[x.symbol]){delete f[x.symbol];toast(`${x.symbol} favorilerden çıkarıldı`)}
  else{
    f[x.symbol]={symbol:x.symbol,addedAt:new Date().toISOString(),entryPrice:Number(x.price),entryScore:Number(x.confidence||0),entryState:x.state,entryStop:Number(x.stop||0),entryTarget1:Number(x.target1||0),entryTarget2:Number(x.target2||0),entryStrategies:x.strategies||{}};
    toast(`${x.symbol} favorilere eklendi`)
  }
  saveFavs(f);renderAll();
}
function starButton(symbol){const fav=isFav(symbol);return `<button class="star ${fav?'on':''}" data-fav="${symbol}" aria-label="${fav?'Favoriden çıkar':'Favoriye ekle'}" title="${fav?'Favoriden çıkar':'Favoriye ekle'}">${fav?'★':'☆'}</button>`}
function liveLink(symbol){const tv=`https://www.tradingview.com/symbols/BIST-${encodeURIComponent(symbol)}/`;return `<a class="live-link" href="${tv}" target="_blank" rel="noopener noreferrer" aria-label="${symbol} canlı grafik">📈 Canlı Hisse</a>`}
function card(x,rank,withFav=true){
  const fav=isFav(x.symbol),f=getFavs()[x.symbol];
  const gain=f&&f.entryPrice?((Number(x.price)/f.entryPrice-1)*100):null;
  const status=f?favStatus(f,x):null;
  return `<article class="card stock-card ${fav?'is-fav':''}" data-stock="${x.symbol}"><div class="rank">${String(rank).padStart(2,'0')}</div><div class="main"><div class="top"><div><b>${x.symbol}</b><span class="state">${stateLabel(x.state)}</span></div>${withFav?starButton(x.symbol):''}</div><div class="scores">${[['SKOR',score(x)],['DİP',x.dip_score],['DÖNÜŞ',x.turn_score],['GÜVEN',x.confidence]].map(z=>`<div><small>${z[0]}</small><strong>${Number(z[1]||0).toFixed(0)}</strong></div>`).join('')}</div><div class="reason"><b>En uygun: ${strategyLabel(x.best_strategy||mode)}</b> · ${(x.reasons||[]).join(' · ')||'Strateji kriterleri karşılanıyor.'}</div><div class="plan"><span>Fiyat <b>${money(x.price)}</b></span><span>Stop <b>${money(x.stop)}</b></span><span>H1 <b>${money(x.target1)}</b></span><span>H2 <b>${money(x.target2)}</b></span><span>R/R <b>${x.risk_reward_1||'—'}</b></span></div><div class="card-actions">${liveLink(x.symbol)}${withFav?starButton(x.symbol):''}</div>${f?`<div class="favline">Favori sonrası <b class="${gain>=0?'up':'down'}">${pct(gain)}</b> · ${status}</div>`:''}</div></article>`
}
function bindStars(){document.querySelectorAll('[data-fav]').forEach(b=>b.onclick=e=>{e.stopPropagation();const x=DATA?.rows?.find(a=>a.symbol===b.dataset.fav);if(x)toggleFav(x)});document.querySelectorAll('.live-link').forEach(a=>a.onclick=e=>e.stopPropagation());bindCards()}
function fmtTech(v){return v==null||Number.isNaN(Number(v))?'—':Number(v).toLocaleString('tr-TR',{maximumFractionDigits:2})}
function renderLocalChart(symbol){
  const svg=$('#stockChart'); if(!svg)return;
  fetch(`./data/charts/${encodeURIComponent(symbol)}.json?ts=${Date.now()}`,{cache:'no-store'})
    .then(r=>{
      if(!r.ok) throw Error('Static chart yok');
      return r.json();
    })
    .catch(()=>{
      return fetch(`../api/chart?symbol=${encodeURIComponent(symbol)}&ts=${Date.now()}`,{cache:'no-store'}).then(r=>r.json());
    })
    .then(d=>{
    if(!d.ok||!d.rows?.length)throw Error(d.error||'Grafik verisi yok');
    const rows=d.rows.filter(r=>[r.open,r.high,r.low,r.close].every(v=>Number.isFinite(Number(v))));
    if(rows.length<2)throw Error('Yeterli grafik verisi yok');
    const nums=rows.map(r=>({o:+r.open,h:+r.high,l:+r.low,c:+r.close,v:Number(r.volume)||0}));
    const ema=(period)=>{const a=[],k=2/(period+1);let prev=nums[0].c;a.push(prev);for(let i=1;i<nums.length;i++){prev=nums[i].c*k+prev*(1-k);a.push(prev)}return a};
    const ema12=ema(12),ema26=ema(26),ema20=ema(20),ema50=ema(50),ema200=ema(200);
    const macd=ema12.map((v,i)=>v-ema26[i]);
    const signal=[]; const k9=2/10; let sp=macd[0]; signal.push(sp); for(let i=1;i<macd.length;i++){sp=macd[i]*k9+sp*(1-k9);signal.push(sp)}
    const hist=macd.map((v,i)=>v-signal[i]);
    const gains=[],losses=[]; for(let i=1;i<nums.length;i++){const ch=nums[i].c-nums[i-1].c;gains.push(Math.max(ch,0));losses.push(Math.max(-ch,0))}
    const rsi=new Array(nums.length).fill(null); const rp=14;
    if(nums.length>rp){let ag=gains.slice(0,rp).reduce((a,b)=>a+b,0)/rp, al=losses.slice(0,rp).reduce((a,b)=>a+b,0)/rp; rsi[rp]=al===0?100:100-(100/(1+ag/al)); for(let i=rp+1;i<nums.length;i++){ag=(ag*(rp-1)+gains[i-1])/rp;al=(al*(rp-1)+losses[i-1])/rp;rsi[i]=al===0?100:100-(100/(1+ag/al));}}
    const W=980,H=650,pad={l:58,r:18,t:24,b:30}, priceH=360,volH=82,oscH=120,gap=12;
    const pTop=pad.t,pBot=pTop+priceH,vTop=pBot+gap,vBot=vTop+volH,oTop=vBot+gap,oBot=oTop+oscH;
    const highs=nums.map(r=>r.h),lows=nums.map(r=>r.l),closes=nums.map(r=>r.c); let lo=Math.min(...lows),hi=Math.max(...highs);
    [ema20,ema50,ema200].forEach(a=>a.forEach(v=>{if(Number.isFinite(v)){lo=Math.min(lo,v);hi=Math.max(hi,v)}}));
    const levels=[['Giriş',Number(DATA?.rows?.find(x=>x.symbol===symbol)?.price)],['Stop',Number(DATA?.rows?.find(x=>x.symbol===symbol)?.stop)],['H1',Number(DATA?.rows?.find(x=>x.symbol===symbol)?.target1)],['H2',Number(DATA?.rows?.find(x=>x.symbol===symbol)?.target2)]];
    levels.forEach(([_,v])=>{if(Number.isFinite(v)&&v>0){lo=Math.min(lo,v);hi=Math.max(hi,v)}});
    const span=hi-lo||1;lo-=span*.06;hi+=span*.06;
    const x=i=>pad.l+i*(W-pad.l-pad.r)/(rows.length-1), y=v=>pTop+(hi-v)*(priceH)/(hi-lo);
    const vmax=Math.max(...nums.map(r=>r.v),1), vy=v=>vBot-(v/vmax)*volH;
    const rsy=v=>oTop+(100-v)*oscH/100;
    const macdVals=macd.concat(signal,hist),mhi=Math.max(...macdVals.map(Math.abs),0.0001), my=v=>oTop+oscH/2-(v/mhi)*(oscH*.44);
    const grid=[]; for(let i=0;i<5;i++){const v=lo+(hi-lo)*i/4,yy=y(v);grid.push(`<line x1="${pad.l}" x2="${W-pad.r}" y1="${yy}" y2="${yy}" class="chart-grid"/><text x="${pad.l-8}" y="${yy+4}" text-anchor="end" class="chart-label">${money(v)}</text>`)}
    [30,50,70].forEach(v=>grid.push(`<line x1="${pad.l}" x2="${W-pad.r}" y1="${rsy(v)}" y2="${rsy(v)}" class="chart-grid"/><text x="${pad.l-8}" y="${rsy(v)+4}" text-anchor="end" class="chart-label">RSI ${v}</text>`));
    const step=Math.max(1,Math.floor(rows.length/6)); for(let i=0;i<rows.length;i+=step)grid.push(`<text x="${x(i)}" y="${H-8}" text-anchor="middle" class="chart-label">${rows[i].date?.slice(5)||''}</text>`);
    const candleStep=(W-pad.l-pad.r)/Math.max(1,rows.length-1),bodyW=Math.max(2,Math.min(10,candleStep*.58));
    const candles=nums.map((r,i)=>{const xx=x(i),yo=y(r.o),yc=y(r.c),yh=y(r.h),yl=y(r.l),up=r.c>=r.o,top=Math.min(yo,yc),body=Math.max(1,Math.abs(yc-yo));return `<g class="candle ${up?'bull':'bear'}"><line x1="${xx.toFixed(1)}" x2="${xx.toFixed(1)}" y1="${yh.toFixed(1)}" y2="${yl.toFixed(1)}" class="candle-wick"/><rect x="${(xx-bodyW/2).toFixed(1)}" y="${top.toFixed(1)}" width="${bodyW.toFixed(1)}" height="${body.toFixed(1)}" class="candle-body"/></g>`}).join('');
    const poly=(arr,fn,cls)=>`<polyline points="${arr.map((v,i)=>Number.isFinite(v)?`${x(i).toFixed(1)},${fn(v).toFixed(1)}`:'').filter(Boolean).join(' ')}" class="${cls}"/>`;
    const vol=nums.map((r,i)=>{const xx=x(i),bw=Math.max(1,bodyW*.7),yy=vy(r.v);return `<rect x="${(xx-bw/2).toFixed(1)}" y="${yy.toFixed(1)}" width="${bw.toFixed(1)}" height="${Math.max(1,vBot-yy).toFixed(1)}" class="vol-bar ${r.c>=r.o?'up':'down'}"/>`}).join('');
    const histBars=hist.map((v,i)=>{const xx=x(i),bw=Math.max(1,bodyW*.7),zero=my(0),yy=my(v);return `<rect x="${(xx-bw/2).toFixed(1)}" y="${Math.min(zero,yy).toFixed(1)}" width="${bw.toFixed(1)}" height="${Math.max(1,Math.abs(yy-zero)).toFixed(1)}" class="macd-hist ${v>=0?'up':'down'}"/>`}).join('');
    const levelSvg=levels.filter(([_,v])=>Number.isFinite(v)&&v>0).map(([name,v],i)=>{const yy=y(v);return `<line x1="${pad.l}" x2="${W-pad.r}" y1="${yy}" y2="${yy}" class="level l${i}"/><text x="${W-pad.r-4}" y="${yy-4}" text-anchor="end" class="level-label">${name} ${money(v)}</text>`}).join('');
    const last=nums[nums.length-1], lastRsi=rsi[rsi.length-1];
    svg.setAttribute('viewBox',`0 0 ${W} ${H}`);
    svg.innerHTML=`<rect x="0" y="0" width="${W}" height="${H}" class="chart-bg"/>${grid.join('')}<text x="${pad.l}" y="16" class="panel-title">Fiyat · Mum + EMA20/50/200</text>${candles}${poly(ema20,y,'ema20')}${poly(ema50,y,'ema50')}${poly(ema200,y,'ema200')}${levelSvg}<line x1="${pad.l}" x2="${W-pad.r}" y1="${vTop-6}" y2="${vTop-6}" class="panel-sep"/><text x="${pad.l}" y="${vTop+10}" class="panel-title">Hacim</text>${vol}<line x1="${pad.l}" x2="${W-pad.r}" y1="${oTop-6}" y2="${oTop-6}" class="panel-sep"/><text x="${pad.l}" y="${oTop+10}" class="panel-title">RSI 14 · MACD</text><line x1="${pad.l}" x2="${W-pad.r}" y1="${rsy(50)}" y2="${rsy(50)}" class="chart-grid"/>${rsi.map((v,i)=>v==null?'':`<circle cx="${x(i)}" cy="${rsy(v)}" r="1.6" class="rsi-dot"/>`).join('')}${histBars}${poly(macd,my,'macd-line')}${poly(signal,my,'signal-line')}<text x="${W-pad.r-4}" y="${oTop+24}" text-anchor="end" class="indicator-label">RSI ${lastRsi==null?'—':lastRsi.toFixed(1)} · MACD ${macd[macd.length-1].toFixed(3)}</text><g class="legend"><text x="${pad.l+120}" y="16" class="ema20-t">EMA20</text><text x="${pad.l+180}" y="16" class="ema50-t">EMA50</text><text x="${pad.l+240}" y="16" class="ema200-t">EMA200</text></g>`;
    $('#chartLoading').textContent=`Son veri: ${rows[rows.length-1].date} · ${money(last.c)} · ${d.source} · RSI ${lastRsi==null?'—':lastRsi.toFixed(1)}`;
  }).catch(e=>{const el=$('#chartLoading');if(el)el.textContent='Grafik yüklenemedi: '+e.message});
}

function detailPage(x){
  const t=x.technicals||{}, fav=isFav(x.symbol);
  const tv=`https://www.tradingview.com/symbols/BIST-${encodeURIComponent(x.symbol)}/`;
  $('#detailTitle').textContent=x.symbol;
  $('#detailState').textContent=stateLabel(x.state);
  $('#detailPrice').textContent=money(x.price);
  $('#detailScore').textContent=Number(x.confidence||0).toFixed(0);
  $('#detailReason').textContent=(x.reasons||[]).join(' · ')||'Yeterli teyit oluşmadı.';
  $('#detailPlan').innerHTML=[['Giriş',x.price],['Stop',x.stop],['H1',x.target1],['H2',x.target2],['R/R',x.risk_reward_1?`1:${x.risk_reward_1}`:'—']].map(z=>`<div><small>${z[0]}</small><b>${typeof z[1]==='number'?money(z[1]):z[1]}</b></div>`).join('');
  $('#detailScores').innerHTML=[['Dip',x.dip_score],['Dönüş',x.turn_score],['Güven',x.confidence],['Satıcı tükenmesi',x.seller_exhaustion],['Alıcı uyanışı',x.buyer_awakening],['Asimetri',x.asymmetry]].map(z=>`<div><small>${z[0]}</small><b>${fmtTech(z[1])}</b></div>`).join('');
  $('#detailTechnicals').innerHTML=[['RSI 14',t.rsi14],['MACD',t.macd],['MACD Signal',t.macd_signal],['MACD Hist.',t.macd_hist],['EMA 20',t.ema20],['EMA 50',t.ema50],['EMA 200',t.ema200],['ATR 14',t.atr14],['Hacim / Hacim20',t.volume_ratio20?`${fmtTech(t.volume_ratio20)}x`:'—']].map(z=>`<div><small>${z[0]}</small><b>${z[1]==null?'—':z[1]}</b></div>`).join('');
  $('#detailLive').innerHTML=`<div class="tv-symbol-bar"><b>BIST:${x.symbol}</b><span>Günlük grafik · Dönüş Avcısı verisi</span></div><div class="local-chart"><div id="chartLoading" class="chart-loading">Grafik verisi yükleniyor…</div><svg id="stockChart" viewBox="0 0 900 420" preserveAspectRatio="none" aria-label="BIST:${x.symbol} fiyat grafiği"></svg></div>`;
  renderLocalChart(x.symbol);
  $('#detailActions').innerHTML=`<button class="wide" id="detailBack">← Fırsatlara dön</button><a class="live-link wide-link" href="${tv}" target="_blank" rel="noopener noreferrer">↗ TradingView'de aç</a>${starButton(x.symbol)}`;
  $('#detailActions [data-fav]').onclick=()=>toggleFav(x);
  $('#detailBack').onclick=()=>showPage('opportunities');
  showPage('stock-detail');
  $('#detailTopBack').onclick=()=>showPage('opportunities');
  window.scrollTo({top:0,behavior:'smooth'});
}
function bindCards(){document.querySelectorAll('[data-stock]').forEach(b=>b.onclick=()=>{const x=DATA?.rows?.find(a=>a.symbol===b.dataset.stock);if(x)detailPage(x)})}
function updateMeta(){if(!DATA)return;const u=$('#universeCount');if(u)u.textContent=DATA.universe_count??'—';const sc=$('#scanCount');if(sc)sc.textContent=DATA.data_found_count??DATA.scanned_count??'—';const op=$('#opportunityCount');if(op)op.textContent=DATA.opportunity_count??'—';const fav=$('#favoriteCount');if(fav)fav.textContent=Object.keys(getFavs()).length;const note=$('#scanNote');if(note)note.textContent=`${DATA.universe_count??'—'} evren · ${DATA.data_found_count??DATA.scanned_count??'—'} veri · ${DATA.data_unavailable_count??0} veri yok · ${DATA.provider_error_count??0} hata`;const un=$('#universeInfo');if(un)un.textContent=`${DATA.universe_count??'—'} şirket · kaynak: KAP · veri: İş Yatırım`;const dn=$('#dataNote');if(dn)dn.textContent=DATA.data_source||'İş Yatırım günlük tarihsel veri';}
function renderHome(){const arr=[...DATA.rows].filter(x=>!x.error&&Number(x.best_score||0)>=65).sort((a,b)=>Number(b.best_score||0)-Number(a.best_score||0)).slice(0,6);$('#homeCards').innerHTML=arr.length?arr.map((x,i)=>card(x,i+1)).join(''):'<div class="empty">Uygun fırsat bulunamadı.</div>';bindStars()}
function renderOpportunities(){const arr=[...DATA.rows].filter(x=>!x.error&&Number(score(x))>=65).sort((a,b)=>score(b)-score(a)).slice(0,80);$('#cards').innerHTML=arr.length?arr.map((x,i)=>card(x,i+1)).join(''):'<div class="empty">Uygun fırsat bulunamadı.</div>';bindStars()}
function favStatus(f,x){const p=Number(x.price),s=Number(f.entryStop||0),t1=Number(f.entryTarget1||0),t2=Number(f.entryTarget2||0);if(s&&p<=s)return 'STOP SEVİYESİNE GELDİ';if(t2&&p>=t2)return 'H2 HEDEFİNE ULAŞTI';if(t1&&p>=t1)return 'H1 HEDEFİNE ULAŞTI';return 'TAKİPTE'}
function renderFavorites(){
  const f=getFavs(),o=getObs(),arr=Object.values(f),stats=$('#favStats');
  if(!arr.length){stats.innerHTML='';$('#favoriteCards').innerHTML='<div class="empty">Henüz favori eklemedin. Radar kartlarındaki ☆ işaretine dokun.</div>';return}
  const map=Object.fromEntries(DATA.rows.map(x=>[x.symbol,x]));let wins=0,returns=[];
  const html=arr.sort((a,b)=>new Date(b.addedAt)-new Date(a.addedAt)).map((v,i)=>{
    const x=map[v.symbol];if(!x)return `<article class="card"><div class="main"><b>${v.symbol}</b><p>Bu taramada veri bulunamadı.</p></div></article>`;
    const gain=(Number(x.price)/v.entryPrice-1)*100;if(gain>0)wins++;returns.push(gain);
    const days=Math.max(0,Math.floor((Date.now()-new Date(v.addedAt))/86400000));
    const observations=o[v.symbol]||[],prices=observations.map(a=>Number(a.price)).filter(Number.isFinite).concat([v.entryPrice,Number(x.price)]);
    const max=(Math.max(...prices)/v.entryPrice-1)*100,min=(Math.min(...prices)/v.entryPrice-1)*100,status=favStatus(v,x);
    return `<article class="card favcard is-fav"><div class="rank">★</div><div class="main"><div class="top"><div><b>${x.symbol}</b><span class="state">${status}</span></div>${starButton(x.symbol)}</div><div class="favsummary"><div><small>Giriş</small><b>${money(v.entryPrice)}</b></div><div><small>Güncel</small><b>${money(x.price)}</b></div><div><small>Süre</small><b>${days} gün</b></div><div><small>Getiri</small><b class="${gain>=0?'up':'down'}">${pct(gain)}</b></div></div><div class="favsummary"><div><small>En yüksek gözlem</small><b class="up">${pct(max)}</b></div><div><small>En düşük gözlem</small><b class="down">${pct(min)}</b></div><div><small>Giriş skoru</small><b>${Number(v.entryScore||0).toFixed(0)}</b></div><div><small>Güncel güven</small><b>${Number(x.confidence||0).toFixed(0)}</b></div></div><div class="reason">Giriş: ${new Date(v.addedAt).toLocaleString('tr-TR')} · Stop ${money(v.entryStop)} · H1 ${money(v.entryTarget1)} · H2 ${money(v.entryTarget2)}<br>${(x.reasons||[]).join(' · ')}</div></div></article>`
  }).join('');
  const avg=returns.reduce((a,b)=>a+b,0)/(returns.length||1);
  stats.innerHTML=`<div><small>Favori sayısı</small><b>${arr.length}</b></div><div><small>Pozitif</small><b>${wins}/${arr.length}</b></div><div><small>Ort. getiri</small><b class="${avg>=0?'up':'down'}">${pct(avg)}</b></div>`;
  $('#favoriteCards').innerHTML=html;bindStars();
}
function statBox(title,s){return `<div class="stat"><b>${title}</b><span>${s?.adet||0} ölçüm</span><strong>${s?.basari==null?'—':s.basari+'%'}</strong><small>Ortalama ${s?.ortalama==null?'—':pct(s.ortalama)}</small><small>Medyan ${s?.medyan==null?'—':pct(s.medyan)}</small><small>En iyi ${s?.en_iyi==null?'—':pct(s.en_iyi)} · En kötü ${s?.en_kotu==null?'—':pct(s.en_kotu)}</small></div>`}
function renderPerformance(){
  if(!PERF){$('#horizonStats').innerHTML='<div class="empty">Henüz yeterli geçmiş tarama oluşmadı.</div>';$('#strategyStats').innerHTML='';return}
  $('#horizonStats').innerHTML=Object.entries(PERF.ufuklar||{}).map(([k,v])=>statBox(k,v)).join('')||'<div class="empty">Henüz ölçüm yok.</div>';
  $('#strategyStats').innerHTML=Object.entries(PERF.stratejiler||{}).map(([k,v])=>statBox(strategyLabel(k),v)).join('')||'<div class="empty">Henüz ölçüm yok.</div>';
  const sig=(PERF.sinyaller||[]).slice(0,20);$('#signalHistory').innerHTML=sig.length?sig.map(x=>`<div class="signal"><b>${x.symbol}</b><span>${x.tarih||'—'} · ${stateLabel(x.state)}</span><span>Giriş ${money(x.price)} · Skor ${Number(x.confidence||0).toFixed(0)}</span><span>${x.sonuclar?.['1G']==null?'1G —':`1G ${pct(x.sonuclar['1G'])}`} · ${x.sonuclar?.['5G']==null?'5G —':`5G ${pct(x.sonuclar['5G'])}`}</span></div>`).join(''):'<div class="empty">Henüz tamamlanmış sinyal ölçümü yok. Tarama geçmişi biriktikçe burada sonuçlar oluşacak.</div>';
}
function renderAll(){updateMeta();
  if(!DATA)return;observeFavorites();
  $('#version').textContent=VERSION;$('#marketScore').textContent=Number(DATA.market?.score||0).toFixed(1);$('#regime').textContent=DATA.market?.regime||'—';$('#updated').textContent=DATA.generated_at?new Date(DATA.generated_at).toLocaleString('tr-TR'):'—';$('#scanCount').textContent=DATA.scanned_count||0;$('#opportunityCount').textContent=DATA.opportunity_count??DATA.rows.filter(x=>Number(x.best_score||0)>=65).length;$('#favoriteCount').textContent=Object.keys(getFavs()).length;$('#universeInfo').textContent=`${DATA.universe_count||0} BIST şirketi hedef evrende · ${DATA.attempted_count||DATA.universe_count||0} denendi · ${DATA.scanned_count||0} veri bulundu · ${DATA.short_history_count||0} kısa geçmiş · ${DATA.data_unavailable_count||0} veri yok · ${DATA.provider_error_count||0} hata`;$('#dataNote').textContent=DATA.data_note||'Günlük veri';renderHome();renderOpportunities();renderFavorites();renderPerformance();
}
async function load(showToast=false){
  const btn=$('#refresh');btn.disabled=true;btn.classList.add('spin');
  try{const [a,b]=await Promise.all([fetch('./data/latest.json?ts='+Date.now(),{cache:'no-store'}),fetch('./data/performance.json?ts='+Date.now(),{cache:'no-store'})]);if(!a.ok)throw Error('Veri yok');DATA=await a.json();PERF=b.ok?await b.json():null;renderAll();if(showToast)toast('Veriler yenilendi')}catch(e){console.error(e);if(!DATA)$('#homeCards').innerHTML='<div class="empty">Veri bulunamadı. Önce taramayı çalıştır.</div>';if(showToast)toast('Veriler alınamadı')}finally{btn.disabled=false;btn.classList.remove('spin')}}
function showPage(id){document.querySelectorAll('.page').forEach(p=>p.classList.toggle('active',p.id===id));document.querySelectorAll('.bottom button').forEach(b=>b.classList.toggle('active',b.dataset.page===id));if(id==='favorites')renderFavorites();if(id==='performance')renderPerformance()}
document.querySelectorAll('.bottom button').forEach(b=>b.onclick=()=>showPage(b.dataset.page));document.querySelectorAll('[data-go]').forEach(b=>b.onclick=()=>showPage(b.dataset.go));document.querySelectorAll('.tabs button').forEach(b=>b.onclick=()=>{document.querySelectorAll('.tabs button').forEach(x=>x.classList.remove('active'));b.classList.add('active');mode=b.dataset.mode;renderOpportunities()});$('#refresh').onclick=async()=>{try{const r=await fetch('../api/scan',{method:'POST'});if(r.ok){toast('Yeni tarama başlatıldı…');setTimeout(()=>load(true),900);return}}catch(e){} load(true)};
$('#exportFav').onclick=()=>{const payload={version:VERSION,exportedAt:new Date().toISOString(),favoriler:getFavs(),gozlemler:getObs()};const blob=new Blob([JSON.stringify(payload,null,2)],{type:'application/json'}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='donus-avcisi-favoriler-yedek.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)};
document.querySelectorAll('[data-theme-choice]').forEach(b=>b.onclick=()=>applyTheme(b.dataset.themeChoice));
$('#importFav').onclick=()=>$('#fileInput').click();$('#fileInput').onchange=e=>{const file=e.target.files[0];if(!file)return;const r=new FileReader();r.onload=()=>{try{const z=JSON.parse(r.result);saveFavs(z.favoriler||z);if(z.gozlemler)saveObs(z.gozlemler);renderAll();toast('Favoriler geri yüklendi')}catch{toast('Yedek dosyası geçersiz')}};r.readAsText(file);e.target.value=''};
initTheme();
load();

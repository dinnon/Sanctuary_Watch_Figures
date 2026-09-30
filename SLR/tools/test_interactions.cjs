// Logic-level DOM/canvas harness, not a substitute for a real browser/layout test.
// Run: node tools/test_interactions.cjs (Node 18+; no packages required).
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..');
const snapshot=id=>JSON.parse(fs.readFileSync(path.join(root,'snapshots',id+'.json'),'utf8'));
async function load(file,id,{network='offline',width=900,storage={},mutate=null}={}){
 const elements={},listeners={},drawCalls=[];
 const ctx=new Proxy({measureText:s=>({width:String(s).length*5.5})},{get:(o,k)=>k in o?o[k]:(...args)=>{for(const a of args)if(typeof a==='number')assert(Number.isFinite(a),k+' nonfinite');drawCalls.push([k,...args])}});
 const element=id=>elements[id]||=( {style:{},textContent:'',value:'',clientWidth:width,clientHeight:400,offsetWidth:180,
  setAttribute(k,v){this[k]=v},getContext:()=>ctx,addEventListener(k,f){(listeners[id+':'+k]||=[]).push(f)},
  getBoundingClientRect:()=>({left:0,top:0,width,height:400}),setPointerCapture(){}} );
 const s={console:{warn(){}},URLSearchParams,AbortController,Date,Math,Set,Number,Error,JSON,
  devicePixelRatio:1,location:{search:'?station='+id},document:{getElementById:element},
  localStorage:{getItem:k=>storage[k]??null,setItem:(k,v)=>storage[k]=v},
  ResizeObserver:class{observe(){}},setTimeout:()=>1,clearTimeout(){},
  fetch:async url=>{
   if(network==='offline')throw Error('Simulated NOAA outage');
   const u=new URL(url),full=snapshot('9440910');
   let v;
   if(file==='embed_amount.html')v=u.searchParams.has('details')?full.observed.monthly:{SeaLvlTrendsObserved:[full.observed.summary]};
   else v=u.searchParams.has('details')?{stationID:id,stationName:full.name,datum:'MSL',units:'meters',trendType:'SINGLE',
    data:full.rows.map(r=>({year:r.y,month:r.m,msl:r.raw,mslDeseasonalized:r.obs,trendLine:r.trend,lowerConfidence:r.lo,upperConfidence:r.hi}))}:{SeaLvlTrends:[full.trend_summary]};
   v=structuredClone(v);if(mutate)mutate(v,u);
   return {ok:true,json:async()=>v};
  }};
 s.window=s.parent={};
 vm.createContext(s);
 const html=fs.readFileSync(path.join(root,file),'utf8'),script=html.match(/<script>([\s\S]*?)<\/script>/)[1];
 vm.runInContext(script.replace('new ResizeObserver(draw).observe(box);refresh();','new ResizeObserver(draw).observe(box);globalThis.ready=refresh();'),s);
 await s.ready;
 return {s,e:elements,storage,drawCalls,run:code=>vm.runInContext(code,s),event:(id,type,event={})=>{for(const f of listeners[id+':'+type]||[])f(event)}};
}
(async()=>{
 for(const id of ['9440910','9443090','9447130'])for(const width of [375,900]){
  const v=snapshot(id).observed,p=await load('embed_amount.html',id,{width});
  assert(p.run('dataKind').includes('Saved'));
  assert(p.drawCalls.some(c=>c[0]==='lineTo'));assert(!('status' in p.e));assert(!('summaryText' in p.e));
  for(const [mode,key]of [['ntde','changeNTDE'],['por','changePOR']]){
   p.event(mode,'click');assert.equal(p.run('summary().change'),v.summary.seaLvlChange[key]);
   const before=p.run('summary().change');
   p.e.from.value='2000';p.event('from','input');assert.equal(String(p.e.fromYear.value),'2000');
   assert.equal(p.run('summary().change'),before);p.event('reset','click');
  }
  p.event('plot','pointermove',{clientX:width/2});assert.equal(p.e.tip.style.display,'block');
  p.event('plot','pointerdown',{clientX:100,pointerId:1});p.event('plot','pointerup',{clientX:width-30,pointerId:1});
  assert(p.run('limits[0]>0'));p.event('reset','click');assert.equal(p.run('limits[0]'),0);
  const t=await load('embed.html',id,{width});
  assert.equal(t.run('data.trend_summary.trendType'),'SINGLE');
  assert.equal(t.run('data.trend_start'),snapshot(id).trend_start);
 }
 const live=await load('embed_amount.html','9440910',{network:'live'});
 assert.equal(live.run('dataKind'),'Live');
 assert(live.storage['noaa-observed-sl-v2-9440910']);
 const cached=await load('embed_amount.html','9440910',{storage:live.storage});
 assert(cached.run('dataKind').includes('Saved'));
 const nullCase=await load('embed_amount.html','9440910',{network:'live',mutate:v=>{if(v.SeaLvlTrendsObserved)v.SeaLvlTrendsObserved[0].seaLvlChange.changeNTDE=null}});
 assert.equal(nullCase.run('summary().available'),false);assert.equal(nullCase.run('NOAAAmountData.levels(data,baselineMode)'),null);
 assert.equal(nullCase.run('baselineMode'),'ntde');nullCase.event('por','click');
 assert.equal(nullCase.run('summary().change'),.059);
 const malformed=await load('embed_amount.html','9440910',{network:'live',mutate:v=>{if(v.data)v.units='feet'}});
 assert(malformed.run('dataKind').includes('Saved'));
 assert(!malformed.storage['noaa-observed-sl-v2-9440910']);
 const unknown=await load('embed_amount.html','1234567');assert(unknown.e.error.textContent.includes('unavailable'));
 const invalid=await load('embed_amount.html','bad');assert(invalid.e.error.textContent.includes('seven-digit'));
 const rate=await load('embed.html','9440910',{network:'live'});assert(rate.storage['noaa-sealvltrends-single-v2-9440910']);
 console.log('PASS: DOM/canvas logic at two widths, three stations, both baselines, zoom/reset/hover, live response handling, cached/offline fallbacks, null NTDE, invalid units, invalid IDs, and separate trend cache. No real-browser rendering asserted.');
})().catch(e=>{console.error(e);process.exit(1)});

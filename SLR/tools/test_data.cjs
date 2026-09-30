// Run: node tools/test_data.cjs (Node 18+; no packages required).
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
const context = vm.createContext({});
vm.runInContext(fs.readFileSync(path.join(__dirname, 'amount-data.js'), 'utf8')+'\nglobalThis.adapter=NOAAAmountData;',context);
const A=context.adapter;
let count=0;
for(const file of fs.readdirSync(path.join(root,'snapshots')).filter(f=>f.endsWith('.json'))){
  const full=JSON.parse(fs.readFileSync(path.join(root,'snapshots',file),'utf8')),v=full.observed;
  assert(A.valid(v,full.station));
  assert.equal(full.trend_summary.trendType,'SINGLE');
  assert.equal(full.trend_mm_year,full.trend_summary.trend*2.54);
  assert(full.trend_start&&full.trend_end);
  for(const [mode,key]of [['ntde','changeNTDE'],['por','changePOR']]){
    const c=A.comparison(v,mode);
    assert.equal(c.change,v.summary.seaLvlChange[key]);
    assert.equal(c.available,v.summary.seaLvlChange[key]!==null);
    if(c.available)assert(Math.abs(c.change*A.FT-c.change/0.3048)<1e-12);
    const levels=A.levels(v,mode);
    assert(levels);
    assert(Math.abs((levels.recent-levels.base)-c.change)<1e-12);
    assert.equal(levels.recentStop-levels.recentStart,5);
    assert.equal(levels.stop-levels.start,mode==='ntde'?19:5);
  }
  const rebuilt=A.make(v.station,{SeaLvlTrendsObserved:[v.summary]},v.monthly,v.retrieved_utc);
  assert.equal(JSON.stringify(rebuilt.monthly),JSON.stringify(v.monthly));
  assert.equal(JSON.stringify(rebuilt.summary),JSON.stringify(v.summary));
  for(const mutate of [
    x=>x.monthly.units='feet',x=>x.summary.metadata.changeUnits='feet',
    x=>x.monthly.stationID='0000000',x=>x.summary.stationId='0000000',
    x=>x.summary.seaLvlChange.changeNTDE='0.1',x=>delete x.summary.seaLvlChange.changePOR,
    x=>x.monthly.data[0].msl=NaN,x=>x.monthly.data[1]=x.monthly.data[0],
    x=>x.summary.seaLvlChange.ntdeEndMidpoint='02/31/2023',x=>x.schema_version=1
  ]){const bad=structuredClone(v);mutate(bad);assert(!A.valid(bad,v.station));}
  const absent=structuredClone(v);absent.summary.seaLvlChange.changeNTDE=null;
  assert(A.valid(absent,v.station));assert.equal(A.comparison(absent,'ntde').available,false);
  assert.equal(A.comparison(absent,'ntde').change,null); // Never substitute POR.
  assert.equal(A.levels(absent,'ntde'),null);assert.equal(A.levels(absent,'por'),null);
  const shifted=structuredClone(v);shifted.summary.seaLvlChange.changeNTDEoffset=.12;
  assert.equal(A.levels(shifted,'ntde').base,.12);
  assert.equal(A.levels(shifted,'ntde').recent,v.summary.seaLvlChange.changeNTDE+.12);
  const zero=structuredClone(v);zero.summary.seaLvlChange.changeNTDE=0;
  assert(A.valid(zero,v.station));assert.equal(A.comparison(zero,'ntde').available,true);
  assert.equal(A.comparison(zero,'ntde').change,0);
  const revised=structuredClone(v);revised.retrieved_utc='2099-01-01T00:00:00Z';
  assert(A.newer(revised,v));assert(!A.newer(v,revised));
  assert(!A.valid({station:v.station,rows:full.rows},v.station)); // Reject old inferred cache.
  count++;
}
for(const file of ['embed.html','embed_amount.html','index.html']){
 const html=fs.readFileSync(path.join(root,file),'utf8');
 assert(!/__BUNDLED_SNAPSHOTS__|__AMOUNT_DATA_JS__|__STATIONS__/.test(html));
 for(const match of html.matchAll(/<script>([\s\S]*?)<\/script>/g))new vm.Script(match[1]);
 assert(!/<script[^>]+src=/.test(html));
 if(file!=='index.html')assert(!/id="(?:description|status|summaryText|source|provenance)"/.test(html));
}
console.log(`PASS: ${count} station snapshots; exact official values, units, nulls, cache isolation, generated JS syntax, and standalone HTML.`);

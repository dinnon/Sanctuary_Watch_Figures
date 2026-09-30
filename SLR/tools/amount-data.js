/* Source-preserving adapter: no averaging, refitting, interpolation, or datum shifts. */
const NOAAAmountData = (() => {
  const api = 'https://api.tidesandcurrents.noaa.gov/dpapi/prod/webapi/product/observedSL.json';
  const FT = 1 / 0.3048;
  const numberOrNull = v => v === null || (typeof v === 'number' && Number.isFinite(v));
  function date(v) {
    if (typeof v !== 'string' || !/^\d{2}\/\d{2}\/\d{4}$/.test(v)) return null;
    const [m,d,y] = v.split('/').map(Number), t = Date.UTC(y,m-1,d), c = new Date(t);
    return c.getUTCFullYear() === y && c.getUTCMonth() === m-1 && c.getUTCDate() === d ? t : null;
  }
  const monthKey = r => `${r.year}-${String(r.month).padStart(2,'0')}`;
  function valid(v, station) {
    if (!v || v.schema_version !== 2 || v.product !== 'observedSL' || v.station !== station) return false;
    const s=v.summary, m=v.monthly, c=s?.seaLvlChange;
    if (s?.stationId !== station || s.metadata?.changeUnits !== 'meters' || !c ||
        m?.stationID !== station || m.units !== 'meters' || m.datum !== 'MSL' || m.trendType !== 'NTDE' ||
        !Array.isArray(m.data) || !m.data.length || !Number.isFinite(Date.parse(v.retrieved_utc))) return false;
    if (!['changePOR','changeNTDE','changeNTDEoffset'].every(k => numberOrNull(c[k]))) return false;
    for (const k of ['porStartMidpoint','porEndMidpoint','ntdeStartMidpoint','ntdeEndMidpoint'])
      if (c[k] !== null && date(c[k]) === null) return false;
    let previous=-Infinity;
    for (const r of m.data) {
      const index=r.year*12+r.month;
      if (!Number.isInteger(r.year) || !Number.isInteger(r.month) || r.month<1 || r.month>12 ||
          index<=previous || !numberOrNull(r.msl)) return false;
      previous=index;
    }
    return m.data.some(r=>r.msl!==null) && v.latest_month===monthKey(m.data.at(-1));
  }
  function urls(station) { return {summary:`${api}?station=${station}&units=metric`,monthly:`${api}?station=${station}&details=monthlymeans&units=metric&trendType=NTDE`}; }
  function make(station,response,monthly,retrieved=new Date().toISOString()) {
    const summary=response.SeaLvlTrendsObserved?.find(s=>s.stationId===station), source=urls(station);
    const v={schema_version:2,product:'observedSL',station,name:summary?.metadata?.stationName||monthly.stationName||station,
      retrieved_utc:retrieved,latest_month:monthly.data?.length?monthKey(monthly.data.at(-1)):'',
      source_summary:source.summary,source_monthly:source.monthly,summary,monthly};
    if (!valid(v,station)) throw Error('Unexpected NOAA observedSL data, units, or station');
    return v;
  }
  function comparison(v,mode) {
    if (!['ntde','por'].includes(mode)) throw Error('Unknown baseline');
    const c=v.summary.seaLvlChange, epoch=mode==='ntde', change=c[epoch?'changeNTDE':'changePOR'];
    return {available:change!==null,change,start:date(c[epoch?'ntdeStartMidpoint':'porStartMidpoint']),
      end:date(c[epoch?'ntdeEndMidpoint':'porEndMidpoint']),label:epoch?'NTDE baseline (1983–2001)':'first five-year average'};
  }
  const newer=(a,b)=>a.latest_month>b.latest_month||(a.latest_month===b.latest_month&&Date.parse(a.retrieved_utc)>=Date.parse(b.retrieved_utc));
  function levels(v,mode) {
    const c=v.summary.seaLvlChange, q=comparison(v,mode);
    if(!q.available || c.changeNTDE===null || c.changeNTDEoffset===null || q.start===null || q.end===null) return null;
    // Reconstruct elevations only from published differences and datum offset.
    // POR and NTDE must refer to the same recent averaging period.
    if(mode==='por' && c.porEndMidpoint!==c.ntdeEndMidpoint) return null;
    const recent=c.changeNTDE+c.changeNTDEoffset;
    const base=mode==='ntde'?c.changeNTDEoffset:recent-c.changePOR;
    const monthYear=t=>{const d=new Date(t);return d.getUTCFullYear()+d.getUTCMonth()/12};
    return {base,recent,start:mode==='ntde'?1983:monthYear(q.start)-2.5,
      stop:mode==='ntde'?2002:monthYear(q.start)+2.5,
      recentStart:monthYear(q.end)-2.5,recentStop:monthYear(q.end)+2.5};
  }
  return {api,FT,date,valid,urls,make,comparison,newer,levels};
})();

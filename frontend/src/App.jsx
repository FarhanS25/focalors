import React,{useEffect,useRef,useState}from'react';
import cytoscape from'cytoscape';
import{Activity,Droplets,Network,Play,RefreshCw,AlertTriangle}from'lucide-react';
const API=import.meta.env.VITE_API_BASE||'http://localhost:8000';
export default function App(){
 const mapRef=useRef(null),cyRef=useRef(null);
 const[network,setNetwork]=useState(null),[result,setResult]=useState(null),[loading,setLoading]=useState(true),[running,setRunning]=useState(false),[error,setError]=useState('');
 const[leakPipe,setLeakPipe]=useState('329'),[scope,setScope]=useState('15');
 async function load(){setLoading(true);setError('');try{const r=await fetch(`${API}/api/network`);if(!r.ok)throw Error(`HTTP ${r.status}`);setNetwork(await r.json())}catch(e){setError(`Backend unavailable (${API}). Start FastAPI. ${e.message}`)}finally{setLoading(false)}}
 useEffect(()=>{load()},[]);
 useEffect(()=>{if(!network||!mapRef.current)return;cyRef.current?.destroy();
  const cy=cytoscape({container:mapRef.current,elements:network.elements,layout:{name:'preset',fit:true,padding:25},style:[
   {selector:'node',style:{label:'data(label)','font-size':8,color:'#a9c0ce','background-color':'#66869c',width:7,height:7,'text-valign':'top','text-margin-y':4}},
   {selector:'node[kind="reservoir"]',style:{shape:'diamond','background-color':'#60e0c6',width:12,height:12}},
   {selector:'edge',style:{width:2,'line-color':'#29465b','curve-style':'bezier'}},
   {selector:'.candidate',style:{'line-color':'#edc56a',width:4}},
   {selector:'.ground-truth',style:{'line-color':'#ff6875',width:6}},
   {selector:'.sensor',style:{'background-color':'#61e0bf',width:12,height:12,'border-width':2,'border-color':'#e5fff8'}}
  ]});
  const ps=network.elements.filter(e=>e.position).map(e=>e.position);
  if(!ps.length||ps.every(p=>p.x===0&&p.y===0))cy.layout({name:'cose',animate:false}).run();else cy.fit(undefined,25);
  cyRef.current=cy;return()=>cy.destroy();
 },[network]);
 useEffect(()=>{if(!cyRef.current||!result)return;const cy=cyRef.current;cy.edges().removeClass('candidate ground-truth');cy.nodes().removeClass('sensor');
  result.candidates.forEach((c,i)=>{const el=cy.getElementById(String(c.pipe_id));if(el.length)el.addClass(c.is_ground_truth?'ground-truth':i<5?'candidate':'')});
  result.sensors.forEach(s=>{const n=cy.getElementById(String(s.junction));if(n.length)n.addClass('sensor')});
 },[result]);
 async function simulate(){setRunning(true);setError('');try{const r=await fetch(`${API}/api/simulate`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({leak_pipe:leakPipe||null,leak_area_m2:.0001,sensor_count:5,candidate_limit:scope==='all'?null:Number(scope),sample_time_s:7200})});const d=await r.json();if(!r.ok)throw Error(d.detail||`HTTP ${r.status}`);setResult(d)}catch(e){setError(e.message)}finally{setRunning(false)}}
 const top=result?.candidates?.[0];
 return <main className="shell">
  <header><div className="brand"><span className="logo"><Droplets/></span><div><b>FOCALORS <small>/ FIELD INTELLIGENCE</small></b><p>Hydraulic leak investigation prototype</p></div></div><span className="pill">● SIMULATION MODE</span></header>
  <section className="hero"><div><label>WATER NETWORK INTELLIGENCE</label><h1>Find the leak.<br/><em>Know what to check next.</em></h1><p>Simulate a pipe leak, compare pressure signatures, and inspect candidate pipes in the Net3 benchmark network.</p></div><div className="stats"><strong>{network?.junction_count??'—'}</strong><span>Junctions</span><strong>{network?.pipe_count??'—'}</strong><span>Pipes</span></div></section>
  {error&&<div className="error"><AlertTriangle size={18}/>{error}</div>}
  <section className="controls"><div><b>01 / Investigation setup</b><p>Configure a simulated scenario</p></div><label>Leak pipe ID<input value={leakPipe} onChange={e=>setLeakPipe(e.target.value)} /></label><label>Candidate scope<select value={scope} onChange={e=>setScope(e.target.value)}><option value="15">Quick · 15 + target</option><option value="40">Medium · 40 + target</option><option value="all">All pipes · slower</option></select></label><button onClick={simulate} disabled={running||loading}><Play size={16}/>{running?'Running hydraulics…':'Run simulation'}</button></section>
  <section className="grid"><div className="panel"><div className="panelhead"><h2><Network size={17}/> Network map</h2><button className="refresh" onClick={load}><RefreshCw size={15}/></button></div><p className="muted">Net3 model coordinates · not GPS</p><div className="map" ref={mapRef}>{loading&&<span className="overlay">Loading network…</span>}</div><div className="legend"><span>🟢 Sensors</span><span>🟡 Top candidates</span><span>🔴 Simulated leak</span></div></div>
   <div className="side"><div className="panel"><div className="panelhead"><h2><Activity size={17}/> Investigation summary</h2></div>{!result?<div className="empty">Run a scenario to show pressure readings and pipe rankings.</div>:<div className="summary"><div><small>Simulated leak</small><b>Pipe {result.leak_pipe}</b></div><div><small>Candidates evaluated</small><b>{result.candidate_count}</b></div><div><small>Ground-truth rank</small><b>{result.actual_pipe_rank?`#${result.actual_pipe_rank}`:'Not evaluated'}</b></div><div className="accent"><small>Best match</small><b>{top?`Pipe ${top.pipe_id}`:'—'}</b><small>{top?`Error ${top.matching_error.toExponential(3)} · not a probability`:''}</small></div>{result.notes.map(n=><p className="note" key={n}>{n}</p>)}</div>}</div>
   <div className="panel"><div className="panelhead"><h2><Activity size={17}/> Pressure signature</h2></div>{!result?<div className="empty small">Pressure readings appear after a run.</div>:<div className="sensors">{result.sensors.map(s=><div className="sensor" key={s.id}><span><b>{s.id}</b> Junction {s.junction}</span><strong className={s.delta_pressure<0?'neg':'pos'}>{s.delta_pressure.toFixed(6)}</strong></div>)}</div>}</div></div></section>
  <section className="panel ranking"><div className="panelhead"><div><h2><Activity size={17}/> Candidate pipe ranking</h2><p className="muted">Lower matching error means a closer signature match.</p></div>{result&&<span className="badge">{result.candidates.length} shown / {result.candidate_count} evaluated</span>}</div>{!result?<div className="empty small">Ranked candidates will appear here.</div>:<div className="tablewrap"><table><thead><tr><th>Rank</th><th>Pipe</th><th>Matching error</th><th>Ground truth</th></tr></thead><tbody>{result.candidates.map(c=><tr key={c.pipe_id}><td>#{c.rank}</td><td><b>{c.pipe_id}</b></td><td>{c.matching_error.toExponential(5)}</td><td>{c.is_ground_truth?<span className="tag red">Yes — simulated leak</span>:c.rank<=5?<span className="tag yellow">Top candidate</span>:'—'}</td></tr>)}</tbody></table></div>}</section>
  <footer><span>FOCALORS · Zero Chill</span><span>Simulated results only · Not field validation</span></footer>
 </main>
}

import { useEffect, useRef, useState } from 'react'
import cytoscape from 'cytoscape'
import { Activity, AlertTriangle, Droplets, Network, Play, RefreshCw } from 'lucide-react'

const API = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'

const MAP_STYLE = [
  {
    selector: 'node',
    style: {
      'background-color': '#66869c',
      width: 14,
      height: 14,
      label: '',
      color: '#e5fff8',
      'font-size': 10,
      'text-outline-width': 2,
      'text-outline-color': '#071018',
      'text-valign': 'top',
      'text-margin-y': -2,
    },
  },
  {
    selector: 'node[kind="reservoir"]',
    style: { shape: 'diamond', 'background-color': '#60e0c6', width: 22, height: 22 },
  },
  {
    selector: 'node[kind="tank"]',
    style: { shape: 'rectangle', 'background-color': '#8eb4ff', width: 18, height: 18 },
  },
  {
    selector: 'node.hover, node.sensor',
    style: { label: 'data(label)' },
  },
  {
    selector: 'node.sensor',
    style: {
      'background-color': '#61e0bf',
      width: 26,
      height: 26,
      'border-width': 3,
      'border-color': '#e5fff8',
    },
  },
  {
    selector: 'edge',
    style: { width: 3, 'line-color': '#7fa8c2', 'curve-style': 'straight', label: '' },
  },
  {
    selector: 'edge[kind="pump"]',
    style: { 'line-style': 'dashed', 'line-color': '#60e0c6', width: 2.4 },
  },
  {
    selector: 'edge[kind="valve"]',
    style: { 'line-style': 'dotted', 'line-color': '#edc56a', width: 2.4 },
  },
  {
    selector: 'edge.hover',
    style: { label: 'data(name)', color: '#edc56a', 'font-size': 11, 'text-outline-width': 2, 'text-outline-color': '#071018' },
  },
  { selector: 'edge.candidate', style: { 'line-color': '#edc56a', width: 7 } },
  { selector: 'edge.ground-truth', style: { 'line-color': '#ff6875', width: 8 } },
  { selector: 'edge.focus', style: { width: 10, 'line-color': '#ffffff' } },
]

function toElements(elements) {
  const nodes = elements.filter((element) => element.position)
  if (!nodes.length) return elements
  const xs = nodes.map((element) => element.position.x)
  const ys = nodes.map((element) => element.position.y)
  const minX = Math.min(...xs)
  const maxX = Math.max(...xs)
  const minY = Math.min(...ys)
  const maxY = Math.max(...ys)
  const span = Math.max(maxX - minX, maxY - minY, 1)
  // Net3 coordinates span only a few dozen model units. Scale them so node
  // sizes stay readable at zoom 1, and flip Y so north is up.
  const scale = 1000 / span
  return elements.map((element) => {
    if (!element.position) return element
    return {
      ...element,
      position: {
        x: (element.position.x - minX) * scale,
        y: (maxY - element.position.y) * scale,
      },
    }
  })
}

function messageFrom(payload, status) {
  const detail = payload?.detail
  if (typeof detail === 'string' && detail.trim()) return detail
  if (Array.isArray(detail)) {
    return detail.map((item) => item?.msg || JSON.stringify(item)).join('; ')
  }
  return `Request failed (HTTP ${status})`
}

function formatPressure(value) {
  if (!Number.isFinite(value)) return '—'
  const absolute = Math.abs(value)
  if (absolute !== 0 && absolute < 0.001) return `${value.toExponential(2)} m`
  return `${value.toFixed(3)} m`
}

function formatError(value) {
  if (!Number.isFinite(value)) return '—'
  if (value === 0) return '0 m'
  if (value < 0.001) return `${value.toExponential(3)} m`
  return `${value.toFixed(4)} m`
}

function edgesNamed(cy, name) {
  return cy.edges().filter((edge) => String(edge.data('name')) === String(name))
}

export default function App() {
  const mapRef = useRef(null)
  const cyRef = useRef(null)
  const [network, setNetwork] = useState(null)
  const [result, setResult] = useState(null)
  const [runs, setRuns] = useState([])
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)
  const [online, setOnline] = useState(null)
  const [error, setError] = useState('')
  const [leakPipe, setLeakPipe] = useState('329')
  const [leakArea, setLeakArea] = useState('0.0001')
  const [scope, setScope] = useState('all')
  const [focusPipe, setFocusPipe] = useState(null)

  async function loadRuns() {
    try {
      const response = await fetch(`${API}/api/runs?limit=6`)
      if (!response.ok) return
      const payload = await response.json()
      setRuns(payload.runs || [])
    } catch {
      /* Recent runs are secondary to the live investigation. */
    }
  }

  async function loadNetwork() {
    setLoading(true)
    setError('')
    try {
      const healthResponse = await fetch(`${API}/api/health`)
      const health = await healthResponse.json().catch(() => ({}))
      if (!healthResponse.ok || !health.status) {
        throw new Error(messageFrom(health, healthResponse.status))
      }
      setOnline(true)
      if (health.database && health.database.status !== 'ok') {
        setError(health.database.detail || 'MongoDB is unavailable, so runs cannot be saved.')
      }
    } catch (err) {
      setOnline(false)
      setError(`Backend unavailable (${API}). Start FastAPI, then reload. ${err.message || ''}`.trim())
      setLoading(false)
      return
    }
    try {
      const response = await fetch(`${API}/api/network`)
      const payload = await response.json().catch(() => ({}))
      if (!response.ok) throw new Error(messageFrom(payload, response.status))
      setNetwork(payload)
      await loadRuns()
    } catch (err) {
      setError(err.message || 'Could not load the network.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadNetwork()
  }, [])

  useEffect(() => {
    if (!network || !mapRef.current) return undefined
    const elements = toElements(network.elements)
    const cy = cytoscape({
      container: mapRef.current,
      elements,
      layout: { name: 'preset', fit: true, padding: 28 },
      style: MAP_STYLE,
      wheelSensitivity: 0.22,
      minZoom: 0.15,
      maxZoom: 4,
      boxSelectionEnabled: false,
      autoungrabify: true,
    })
    const positions = elements.filter((element) => element.position).map((element) => element.position)
    if (!positions.length || positions.every((position) => position.x === 0 && position.y === 0)) {
      cy.layout({ name: 'cose', animate: false }).run()
    }
    cy.fit(undefined, 28)
    const hover = (event) => event.target.addClass('hover')
    const clear = (event) => event.target.removeClass('hover')
    cy.on('mouseover', 'node, edge', hover)
    cy.on('mouseout', 'node, edge', clear)
    cyRef.current = cy
    const observer = new ResizeObserver(() => cy.resize())
    observer.observe(mapRef.current)
    return () => {
      observer.disconnect()
      cy.destroy()
      if (cyRef.current === cy) cyRef.current = null
    }
  }, [network])

  useEffect(() => {
    const cy = cyRef.current
    if (!cy) return
    if (!result) {
      cy.elements().removeClass('candidate ground-truth sensor focus')
      return
    }
    cy.batch(() => {
      cy.elements().removeClass('candidate ground-truth sensor focus')
      for (const sensor of result.sensors || []) {
        cy.nodes()
          .filter((node) => String(node.data('name')) === String(sensor.junction))
          .addClass('sensor')
      }
      for (const candidate of result.candidates || []) {
        if (candidate.rank <= 5 && !candidate.is_ground_truth) {
          edgesNamed(cy, candidate.pipe_id).addClass('candidate')
        }
      }
      if (result.leak_pipe) edgesNamed(cy, result.leak_pipe).addClass('ground-truth')
      if (focusPipe) edgesNamed(cy, focusPipe).addClass('focus')
    })
  }, [result, network, focusPipe])

  function fitMap() {
    cyRef.current?.fit(undefined, 28)
  }

  function showPipe(pipeId) {
    setFocusPipe(pipeId)
    const cy = cyRef.current
    if (!cy) return
    const edge = edgesNamed(cy, pipeId)
    if (edge.length) {
      cy.animate({ fit: { eles: edge.union(edge.connectedNodes()), padding: 80 }, duration: 350 })
    }
  }

  async function simulate(event) {
    event.preventDefault()
    setRunning(true)
    setError('')
    setResult(null)
    setFocusPipe(null)
    const scopeText = scope === 'all' ? `all ${network?.pipe_count ?? ''} pipes`.replace('  ', ' ') : `${scope} sampled pipes`
    try {
      const response = await fetch(`${API}/api/simulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          leak_pipe: leakPipe.trim() || null,
          leak_area_m2: Number(leakArea),
          sensor_count: 5,
          candidate_limit: scope === 'all' ? null : Number(scope),
          sample_time_s: 7200,
        }),
      })
      const payload = await response.json().catch(() => ({}))
      if (!response.ok) throw new Error(messageFrom(payload, response.status))
      setResult(payload)
      await loadRuns()
    } catch (err) {
      setError(err.message || `Simulation failed while evaluating ${scopeText}.`)
    } finally {
      setRunning(false)
    }
  }

  const top = result?.candidates?.[0]
  const maxAbs = Math.max(...(result?.sensors || []).map((sensor) => Math.abs(sensor.delta_pressure)), 0)
  const worstError = result?.candidates?.length
    ? result.candidates[result.candidates.length - 1].matching_error
    : 0
  const scopeText = scope === 'all'
    ? `all ${network?.pipe_count ?? 'Net3'} pipes`
    : `${scope} spatially sampled pipes`

  return (
    <main className="shell">
      <header>
        <div className="brand">
          <span className="logo"><Droplets /></span>
          <div>
            <b>FOCALORS <small>/ FIELD INTELLIGENCE</small></b>
            <p>Hydraulic leak investigation prototype</p>
          </div>
        </div>
        <span className={online === false ? 'pill offline' : 'pill'}>
          {online === false ? '○ BACKEND OFFLINE' : online ? '● SIMULATION MODE' : '○ CHECKING BACKEND'}
        </span>
      </header>

      <section className="hero">
        <div>
          <label>WATER NETWORK INTELLIGENCE</label>
          <h1>Find the leak.<br /><em>Know what to check next.</em></h1>
          <p>
            Simulate a pipe leak on the Net3 benchmark, compare pressure signatures from WNTR,
            and inspect the pipes whose signatures are closest. Scores are matching errors from
            a controlled simulation, not field-detection accuracy.
          </p>
        </div>
        <div className="stats">
          <strong>{network?.junction_count ?? '—'}</strong>
          <span>Junctions</span>
          <strong>{network?.pipe_count ?? '—'}</strong>
          <span>Pipes</span>
        </div>
      </section>

      {error && (
        <div className="error" role="alert">
          <AlertTriangle size={18} />
          <span>{error}</span>
        </div>
      )}

      <form className="controls" onSubmit={simulate}>
        <div>
          <b>01 / Investigation setup</b>
          <p>The leak ID builds the scenario. The ranker does not receive it.</p>
        </div>
        <label className="field">
          Leak pipe ID
          <input value={leakPipe} onChange={(event) => setLeakPipe(event.target.value)} placeholder="329" />
        </label>
        <label className="field">
          Orifice area (m²)
          <input
            type="number"
            min="0.00001"
            max="0.01"
            step="0.0001"
            value={leakArea}
            onChange={(event) => setLeakArea(event.target.value)}
          />
        </label>
        <label className="field">
          Candidate scope
          <select value={scope} onChange={(event) => setScope(event.target.value)}>
            <option value="15">Spatial sample · 15 pipes</option>
            <option value="40">Spatial sample · 40 pipes</option>
            <option value="all">Full network · every pipe</option>
          </select>
        </label>
        <button type="submit" disabled={running || loading || !network}>
          <Play size={16} />
          {running ? 'Solving hydraulics…' : 'Run simulation'}
        </button>
      </form>

      <section className="grid">
        <div className="panel">
          <div className="panelhead">
            <h2><Network size={17} /> Network map</h2>
            <div className="actions">
              <button type="button" className="refresh" onClick={fitMap}>Fit</button>
              <button type="button" className="refresh" onClick={loadNetwork} disabled={loading} aria-label="Reload network">
                <RefreshCw size={15} />
              </button>
            </div>
          </div>
          <p className="muted">
            {result
              ? 'Red is the scenario leak you configured. Gold pipes are the five lowest-RMSE candidates. Teal nodes are virtual sensors.'
              : 'Net3 model coordinates, drawn with north up. Not a GPS map.'}
          </p>
          <div className="mapwrap">
            <div className="map" ref={mapRef} />
            {loading && <div className="overlay">Loading network…</div>}
            {!loading && !network && <div className="overlay">Network not loaded</div>}
            {running && <div className="overlay">Solving {scopeText}. Each candidate is a real WNTR run.</div>}
          </div>
          <div className="legend">
            <span><i className="swatch sensor" /> Virtual sensors</span>
            <span><i className="swatch candidate" /> Lowest RMSE</span>
            <span><i className="swatch leak" /> Scenario leak</span>
          </div>
        </div>

        <div className="side">
          <div className="panel">
            <div className="panelhead">
              <h2><Activity size={17} /> Investigation summary</h2>
            </div>
            {running && <div className="empty">Solving the baseline, the scenario leak, and each candidate pipe.</div>}
            {!running && !result && <div className="empty">Run a scenario to show pressure readings and pipe rankings.</div>}
            {result && (
              <div className="summary">
                <div className="success" role="status">
                  Simulation finished in {result.elapsed_seconds}s. Controlled WNTR demonstration, not field validation.
                </div>
                <div>
                  <small>Scenario leak</small>
                  <b>Pipe {result.leak_pipe}</b>
                  <small>Hidden from the ranker</small>
                </div>
                <div>
                  <small>Candidates ranked</small>
                  <b>{result.candidate_count}</b>
                  <small>{result.candidate_selection === 'all_pipes' ? 'Every Net3 pipe' : 'Spatial sample'}</small>
                </div>
                <div>
                  <small>Post-hoc scenario rank</small>
                  <b>{result.actual_pipe_rank ? `#${result.actual_pipe_rank}` : 'Not ranked'}</b>
                  <small>
                    {result.true_pipe_in_candidate_set
                      ? 'Scored after sorting'
                      : 'Not inserted into the candidate set'}
                  </small>
                </div>
                <div className="accent">
                  <small>Lowest RMSE</small>
                  <b>{top ? `Pipe ${top.pipe_id}` : '—'}</b>
                  <small>{top ? `${formatError(top.matching_error)} · not a probability` : 'No candidate succeeded'}</small>
                </div>
                <p className="note">
                  Largest sensor change {formatPressure(result.observed_signal_max_abs_m)}. Pressure unit: meters of head.
                </p>
              </div>
            )}
          </div>

          <div className="panel">
            <div className="panelhead">
              <h2><Activity size={17} /> Pressure signature</h2>
            </div>
            {running && <div className="empty small">Pressure readings appear when the solves finish.</div>}
            {!running && !result && <div className="empty small">Sensor readings appear after a run.</div>}
            {result && (
              <div className="sensors">
                {(result.sensors || []).map((sensor) => {
                  const width = maxAbs > 0 ? (Math.abs(sensor.delta_pressure) / maxAbs) * 100 : 0
                  return (
                    <div className="sig" key={sensor.id}>
                      <div className="sigrow">
                        <span><b>{sensor.id}</b> Junction {sensor.junction}</span>
                        <strong className={sensor.delta_pressure < 0 ? 'neg' : 'pos'}>
                          {formatPressure(sensor.delta_pressure)}
                        </strong>
                      </div>
                      <div className="track" aria-hidden="true">
                        <div className={`bar ${sensor.delta_pressure < 0 ? 'neg' : 'pos'}`} style={{ width: `${width}%` }} />
                      </div>
                      <p className="muted">
                        {formatPressure(sensor.baseline_pressure)} baseline → {formatPressure(sensor.leak_pressure)} with leak
                      </p>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </div>
      </section>

      <section className="panel ranking">
        <div className="panelhead">
          <div>
            <h2><Activity size={17} /> Candidate pipe ranking</h2>
            <p className="muted">RMSE of the sensor pressure-change vector. Lower means a closer hydraulic match.</p>
          </div>
          {result && (
            <span className="badge">{result.candidates.length} shown / {result.candidate_count} ranked</span>
          )}
        </div>
        {running && <div className="empty small">Ranked candidates will appear here.</div>}
        {!running && !result && <div className="empty small">Ranked candidates will appear here.</div>}
        {result && result.candidates.length === 0 && (
          <div className="empty small">No candidate simulation succeeded, so there is nothing to rank.</div>
        )}
        {result && result.candidates.length > 0 && (
          <div className="tablewrap">
            <table>
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Pipe</th>
                  <th>RMSE</th>
                  <th>Match</th>
                  <th>Scenario leak</th>
                </tr>
              </thead>
              <tbody>
                {result.candidates.map((candidate) => {
                  const width = worstError > 0 ? (candidate.matching_error / worstError) * 100 : 0
                  return (
                    <tr
                      key={candidate.pipe_id}
                      data-pipe={candidate.pipe_id}
                      className={candidate.is_ground_truth ? 'scenario' : candidate.rank <= 5 ? 'top' : ''}
                      onClick={() => showPipe(candidate.pipe_id)}
                      onKeyDown={(event) => {
                        if (event.key === 'Enter' || event.key === ' ') {
                          event.preventDefault()
                          showPipe(candidate.pipe_id)
                        }
                      }}
                      tabIndex={0}
                    >
                      <td>#{candidate.rank}</td>
                      <td><b>{candidate.pipe_id}</b></td>
                      <td>{formatError(candidate.matching_error)}</td>
                      <td>
                        <div className="track slim" aria-hidden="true">
                          <div className="bar gold" style={{ width: `${width}%` }} />
                        </div>
                      </td>
                      <td>
                        {candidate.is_ground_truth
                          ? <span className="tag red">Simulated leak</span>
                          : candidate.rank <= 5
                            ? <span className="tag yellow">Closest signature</span>
                            : '—'}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
        {result?.failures?.length > 0 && (
          <p className="note">{result.failures.length} candidate simulations failed and were left unranked.</p>
        )}
        {result?.notes?.length > 0 && (
          <details>
            <summary>What this score does and does not mean</summary>
            {result.notes.map((note) => <p className="note" key={note}>{note}</p>)}
          </details>
        )}
      </section>

      <section className="panel">
        <div className="panelhead">
          <h2><Activity size={17} /> Saved runs</h2>
        </div>
        {runs.length === 0 && <div className="empty small">Completed simulations are stored in MongoDB and listed here.</div>}
        {runs.length > 0 && (
          <div className="runs">
            {runs.map((run) => (
              <div className="run" key={run.id}>
                <b>#{run.id} · Pipe {run.leak_pipe}</b>
                <span>{run.candidate_count} ranked</span>
                <span>{run.actual_pipe_rank ? `scenario rank #${run.actual_pipe_rank}` : 'scenario not ranked'}</span>
                <span className="muted">{run.created_at} UTC</span>
              </div>
            ))}
          </div>
        )}
      </section>

      <footer>
        <span>FOCALORS · Zero Chill</span>
        <span>Simulated results only · Not field validation</span>
      </footer>
    </main>
  )
}

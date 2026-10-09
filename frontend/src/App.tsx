import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { BrowserRouter, Link, Navigate, Route, Routes } from 'react-router-dom'
import './App.css'

const API_BASE = 'http://localhost:8000/api'

type User = {
  id: number
  username: string
  email: string
}

type Summary = {
  total_logs: number
  error_count: number
  warning_count: number
  incidents_total: number
  open_incidents: number
  critical_incidents: number
  pipeline_runs: number
}

async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    credentials: 'include',
    ...options,
    headers: {
      ...(options.headers || {}),
      ...(options.body && !(options.body instanceof FormData) ? { 'Content-Type': 'application/json' } : {}),
    },
  })

  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    throw new Error((data as { detail?: string; error?: string }).detail || (data as { detail?: string; error?: string }).error || 'Request failed')
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}

function App() {
  const [user, setUser] = useState<User | null>(null)
  const [loadingUser, setLoadingUser] = useState(true)

  useEffect(() => {
    const loadUser = async () => {
      try {
        const data = await api<User>('/auth/me/')
        setUser(data)
      } catch {
        setUser(null)
      } finally {
        setLoadingUser(false)
      }
    }
    loadUser()
  }, [])

  if (loadingUser) {
    return <div className="app-shell loading-shell">Loading workspace…</div>
  }

  return (
    <BrowserRouter>
      {user ? (
        <ProtectedApp user={user} onLogout={() => setUser(null)} />
      ) : (
        <AuthScreen onLogin={(nextUser) => setUser(nextUser)} />
      )}
    </BrowserRouter>
  )
}

function ProtectedApp({ user, onLogout }: { user: User; onLogout: () => void }) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-block">
          <div className="brand-mark">SFI</div>
          <div>
            <div className="brand-name">Software Failure Intelligence</div>
            <div className="brand-subtitle">Observability workspace</div>
          </div>
        </div>
        <nav className="nav-links">
          <Link to="/">Dashboard</Link>
          <Link to="/logs">Logs</Link>
          <Link to="/incidents">Incidents</Link>
          <Link to="/ai">AI investigations</Link>
          <Link to="/knowledge">Knowledge base</Link>
          <Link to="/pipeline">Pipeline</Link>
        </nav>
      </aside>
      <main className="main-panel">
        <header className="topbar">
          <div>
            <div className="eyebrow">Platform</div>
            <h1>Incident intelligence</h1>
          </div>
          <div className="topbar-user">
            <span>{user.username}</span>
            <button onClick={async () => { await api('/auth/logout/', { method: 'POST' }); onLogout() }}>Logout</button>
          </div>
        </header>
        <Routes>
          <Route path="/" element={<DashboardView />} />
          <Route path="/logs" element={<LogsView />} />
          <Route path="/incidents" element={<IncidentsView />} />
          <Route path="/ai" element={<AiView />} />
          <Route path="/knowledge" element={<KnowledgeView />} />
          <Route path="/pipeline" element={<PipelineView />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  )
}

function AuthScreen({ onLogin }: { onLogin: (user: User) => void }) {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [error, setError] = useState('')
  const [form, setForm] = useState({ username: 'demo', email: 'demo@example.com', password: 'demo1234' })

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError('')
    try {
      const endpoint = mode === 'login' ? '/auth/login/' : '/auth/register/'
      const payload = mode === 'login'
        ? { username: form.username, password: form.password }
        : { username: form.username, email: form.email, password: form.password }
      const result = await api<User>(endpoint, { method: 'POST', body: JSON.stringify(payload) })
      onLogin(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed')
    }
  }

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="auth-title">AI Software Failure Intelligence</div>
        <div className="auth-toggle">
          <button className={mode === 'login' ? 'active' : ''} onClick={() => setMode('login')}>Login</button>
          <button className={mode === 'register' ? 'active' : ''} onClick={() => setMode('register')}>Register</button>
        </div>
        <form onSubmit={handleSubmit} className="auth-form">
          <label>
            Username
            <input value={form.username} onChange={(event) => setForm((current) => ({ ...current, username: event.target.value }))} />
          </label>
          {mode === 'register' && (
            <label>
              Email
              <input type="email" value={form.email} onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))} />
            </label>
          )}
          <label>
            Password
            <input type="password" value={form.password} onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))} />
          </label>
          {error && <div className="error-box">{error}</div>}
          <button type="submit" className="primary-btn">{mode === 'login' ? 'Sign in' : 'Create account'}</button>
        </form>
      </div>
    </div>
  )
}

function DashboardView() {
  const [summary, setSummary] = useState<Summary | null>(null)
  const [trend, setTrend] = useState<Array<{ date: string; count: number }>>([])
  const [services, setServices] = useState<Array<{ service_name: string; total: number; errors: number }>>([])
  const [incidents, setIncidents] = useState<Array<{ id: number; title: string; severity: string; status: string; service_name: string; error_count: number }>>([])

  useEffect(() => {
    const load = async () => {
      const [summaryData, trendData, serviceData, incidentData] = await Promise.all([
        api<Summary>('/analytics/summary/'),
        api<{ results: Array<{ date: string; count: number }> }>('/analytics/errors-over-time/'),
        api<{ results: Array<{ service_name: string; total: number; errors: number }> }>('/analytics/services/'),
        api<{ results: Array<{ id: number; title: string; severity: string; status: string; service_name: string; error_count: number }> }>('/incidents/'),
      ])
      setSummary(summaryData)
      setTrend(trendData.results)
      setServices(serviceData.results)
      setIncidents(incidentData.results)
    }
    load().catch((error) => console.error(error))
  }, [])

  const maxTrend = useMemo(() => Math.max(...trend.map((item) => item.count), 1), [trend])

  return (
    <div className="content-stack">
      <section className="card-grid compact-grid">
        <StatCard label="Total logs" value={summary?.total_logs ?? 0} tone="blue" />
        <StatCard label="Error count" value={summary?.error_count ?? 0} tone="red" />
        <StatCard label="Warnings" value={summary?.warning_count ?? 0} tone="amber" />
        <StatCard label="Open incidents" value={summary?.open_incidents ?? 0} tone="green" />
      </section>

      <section className="panel-grid">
        <div className="panel">
          <div className="panel-header">
            <h2>Error trend</h2>
          </div>
          <div className="bar-chart">
            {trend.map((point) => (
              <div key={point.date} className="bar-col">
                <div className="bar-value" style={{ height: `${Math.max((point.count / maxTrend) * 100, 8)}%` }} />
                <span>{new Date(point.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="panel">
          <div className="panel-header"><h2>Top services</h2></div>
          <div className="list-rows">
            {services.map((service) => (
              <div key={service.service_name} className="list-row compact-row">
                <span>{service.service_name}</span>
                <strong>{service.errors} errors</strong>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header"><h2>Recent incidents</h2></div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Service</th><th>Severity</th><th>Status</th><th>Errors</th></tr>
            </thead>
            <tbody>
              {incidents.slice(0, 6).map((incident) => (
                <tr key={incident.id}>
                  <td>{incident.service_name}</td>
                  <td><span className={`badge ${incident.severity}`}>{incident.severity}</span></td>
                  <td>{incident.status}</td>
                  <td>{incident.error_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}

function LogsView() {
  const [logs, setLogs] = useState<Array<{ id: number; service_name: string; level: string; message: string; timestamp: string; exception_type: string }>>([])
  const [file, setFile] = useState<File | null>(null)
  const [message, setMessage] = useState('')

  const loadLogs = async () => {
    const data = await api<{ results: Array<{ id: number; service_name: string; level: string; message: string; timestamp: string; exception_type: string }> }>('/logs/')
    setLogs(data.results)
  }

  useEffect(() => { loadLogs().catch((error) => console.error(error)) }, [])

  const handleUpload = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!file) return
    const formData = new FormData()
    formData.append('file', file)
    const result = await api<{ summary: { accepted: number; rejected: number; duplicate: number } }>('/logs/upload/', {
      method: 'POST',
      body: formData,
    })
    setMessage(`Uploaded ${result.summary.accepted} accepted records.`)
    setFile(null)
    loadLogs()
  }

  return (
    <div className="content-stack">
      <div className="panel">
        <div className="panel-header"><h2>Log ingestion</h2></div>
        <form onSubmit={handleUpload} className="upload-form">
          <input type="file" accept=".csv,.json" onChange={(event) => setFile(event.target.files?.[0] || null)} />
          <button type="submit" className="primary-btn">Upload logs</button>
        </form>
        {message && <div className="success-box">{message}</div>}
      </div>
      <div className="panel">
        <div className="panel-header"><h2>Recent log entries</h2></div>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Service</th><th>Level</th><th>Message</th><th>Time</th></tr></thead>
            <tbody>
              {logs.map((entry) => (
                <tr key={entry.id}>
                  <td>{entry.service_name}</td>
                  <td><span className={`badge ${entry.level.toLowerCase()}`}>{entry.level}</span></td>
                  <td>{entry.message}</td>
                  <td>{new Date(entry.timestamp).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

function IncidentsView() {
  const [incidents, setIncidents] = useState<Array<{ id: number; title: string; severity: string; status: string; service_name: string; error_count: number; error_signature: string }>>([])

  const load = async () => {
    const data = await api<{ results: Array<{ id: number; title: string; severity: string; status: string; service_name: string; error_count: number; error_signature: string }> }>('/incidents/')
    setIncidents(data.results)
  }

  useEffect(() => { load().catch((error) => console.error(error)) }, [])

  const updateStatus = async (incidentId: number, status: string) => {
    await api(`/incidents/${incidentId}/update/`, { method: 'PATCH', body: JSON.stringify({ status }) })
    load()
  }

  return (
    <div className="content-stack">
      <div className="panel">
        <div className="panel-header"><h2>Incident feed</h2></div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Title</th><th>Service</th><th>Severity</th><th>Status</th><th>Errors</th><th>Action</th></tr>
            </thead>
            <tbody>
              {incidents.map((incident) => (
                <tr key={incident.id}>
                  <td>{incident.title}</td>
                  <td>{incident.service_name}</td>
                  <td><span className={`badge ${incident.severity}`}>{incident.severity}</span></td>
                  <td>{incident.status}</td>
                  <td>{incident.error_count}</td>
                  <td>
                    <button onClick={() => updateStatus(incident.id, 'investigating')}>Investigate</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

function AiView() {
  const [investigations, setInvestigations] = useState<Array<{ id: number; summary: string; status: string; incident_id: number }>>([])

  useEffect(() => {
    const load = async () => {
      const data = await api<{ results: Array<{ id: number; summary: string; status: string; incident_id: number }> }>('/investigations/')
      setInvestigations(data.results)
    }
    load().catch((error) => console.error(error))
  }, [])

  return (
    <div className="content-stack">
      <div className="panel">
        <div className="panel-header"><h2>AI investigation history</h2></div>
        <div className="list-rows">
          {investigations.map((item) => (
            <div key={item.id} className="list-row">
              <span>Incident #{item.incident_id}</span>
              <strong>{item.status}</strong>
              <small>{item.summary || 'Investigation available'}</small>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function KnowledgeView() {
  const [documents, setDocuments] = useState<Array<{ id: number; title: string; status: string }>>([])
  const [query, setQuery] = useState('database timeout')
  const [results, setResults] = useState<Array<{ document: string; content: string; score: number }>>([])
  const [file, setFile] = useState<File | null>(null)

  const load = async () => {
    const data = await api<{ results: Array<{ id: number; title: string; status: string }> }>('/knowledge/documents/list/')
    setDocuments(data.results)
  }

  useEffect(() => { load().catch((error) => console.error(error)) }, [])

  const handleUpload = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!file) return
    const formData = new FormData()
    formData.append('file', file)
    formData.append('title', file.name)
    await api('/knowledge/documents/', { method: 'POST', body: formData })
    load()
  }

  const handleSearch = async () => {
    const data = await api<{ results: Array<{ document: string; content: string; score: number }> }>('/knowledge/search/', {
      method: 'POST',
      body: JSON.stringify({ query }),
    })
    setResults(data.results)
  }

  return (
    <div className="content-stack">
      <div className="panel">
        <div className="panel-header"><h2>Upload runbook</h2></div>
        <form onSubmit={handleUpload} className="upload-form">
          <input type="file" accept=".md,.txt" onChange={(event) => setFile(event.target.files?.[0] || null)} />
          <button type="submit" className="primary-btn">Index runbook</button>
        </form>
      </div>
      <div className="panel">
        <div className="panel-header"><h2>Runbook search</h2></div>
        <div className="search-row">
          <input value={query} onChange={(event) => setQuery(event.target.value)} />
          <button onClick={handleSearch}>Search</button>
        </div>
        <div className="list-rows">
          {results.map((result, index) => (
            <div key={`${result.document}-${index}`} className="list-row">
              <strong>{result.document}</strong>
              <small>{result.score}</small>
              <p>{result.content}</p>
            </div>
          ))}
        </div>
      </div>
      <div className="panel">
        <div className="panel-header"><h2>Indexed documents</h2></div>
        <div className="list-rows">
          {documents.map((doc) => (
            <div key={doc.id} className="list-row">
              <span>{doc.title}</span>
              <strong>{doc.status}</strong>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function PipelineView() {
  const [runs, setRuns] = useState<Array<{ id: number; source_name: string; status: string; total_records: number; accepted_records: number; rejected_records: number }>>([])

  useEffect(() => {
    const load = async () => {
      const data = await api<{ results: Array<{ id: number; source_name: string; status: string; total_records: number; accepted_records: number; rejected_records: number }> }>('/logs/pipeline-runs/')
      setRuns(data.results)
    }
    load().catch((error) => console.error(error))
  }, [])

  return (
    <div className="content-stack">
      <div className="panel">
        <div className="panel-header"><h2>Pipeline runs</h2></div>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Source</th><th>Status</th><th>Total</th><th>Accepted</th><th>Rejected</th></tr></thead>
            <tbody>
              {runs.map((run) => (
                <tr key={run.id}>
                  <td>{run.source_name}</td>
                  <td><span className={`badge ${run.status}`}>{run.status}</span></td>
                  <td>{run.total_records}</td>
                  <td>{run.accepted_records}</td>
                  <td>{run.rejected_records}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

function StatCard({ label, value, tone }: { label: string; value: number; tone: 'blue' | 'red' | 'amber' | 'green' }) {
  return (
    <div className={`stat-card ${tone}`}>
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
    </div>
  )
}

export default App

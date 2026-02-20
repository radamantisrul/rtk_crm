import { useEffect, useMemo, useState } from 'react'
import { Navigate, NavLink, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import { request } from './api'

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/empresas', label: 'Empresas' },
  { to: '/clientes', label: 'Clientes' },
  { to: '/integraciones', label: 'Integraciones' },
  { to: '/monitoreo', label: 'Monitoreo' },
  { to: '/comunicaciones', label: 'Comunicaciones' },
  { to: '/configuracion', label: 'Configuración' },
]

function Badge({ children, tone = 'neutral' }) {
  return <span className={`badge badge-${tone}`}>{children}</span>
}

function KpiCard({ title, value, hint }) {
  return (
    <article className="kpi-card">
      <p className="kpi-title">{title}</p>
      <h3>{value}</h3>
      <small>{hint}</small>
    </article>
  )
}

function DataTable({ title, columns, rows, searchBy = [], filters = [] }) {
  const [query, setQuery] = useState('')
  const [activeFilter, setActiveFilter] = useState('all')

  const filteredRows = useMemo(() => {
    const q = query.trim().toLowerCase()
    return rows.filter((row) => {
      const passText = !q || searchBy.some((key) => String(row[key] ?? '').toLowerCase().includes(q))
      const passFilter = activeFilter === 'all' || row.status === activeFilter
      return passText && passFilter
    })
  }, [query, rows, searchBy, activeFilter])

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>{title}</h2>
        <div className="actions-inline">
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Buscar..." />
          {filters.length > 0 && (
            <select value={activeFilter} onChange={(e) => setActiveFilter(e.target.value)}>
              <option value="all">Todos</option>
              {filters.map((filter) => (
                <option key={filter} value={filter}>
                  {filter}
                </option>
              ))}
            </select>
          )}
        </div>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              {columns.map((col) => (
                <th key={col.key}>{col.label}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filteredRows.map((row) => (
              <tr key={row.id}>
                {columns.map((col) => (
                  <td key={col.key}>{col.render ? col.render(row[col.key], row) : row[col.key]}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        {filteredRows.length === 0 && <p className="empty">Sin resultados.</p>}
      </div>
    </section>
  )
}

function DashboardPage({ apiStatus, companiesCount }) {
  return (
    <div className="page-grid">
      <section className="panel">
        <h2>Resumen Operativo</h2>
        <div className="kpi-grid">
          <KpiCard title="Estado API" value={apiStatus === 'ok' ? 'Online' : 'Offline'} hint="/health" />
          <KpiCard title="Empresas" value={companiesCount} hint="Tenants registrados" />
          <KpiCard title="Eventos" value="24" hint="Últimas 24h" />
          <KpiCard title="Automatizaciones" value="7" hint="Activas" />
        </div>
      </section>
    </div>
  )
}

function EmpresasPage({ companies, onCreateCompany }) {
  const [form, setForm] = useState({ name: '', network_name: '', parent_company_id: '' })

  async function onSubmit(event) {
    event.preventDefault()
    await onCreateCompany({ ...form, parent_company_id: form.parent_company_id || null })
    setForm({ name: '', network_name: '', parent_company_id: '' })
  }

  const rows = companies.map((item) => ({
    ...item,
    status: item.parent_company_id ? 'reseller' : 'core',
  }))

  return (
    <div className="page-grid">
      <section className="panel">
        <h2>Nueva Empresa</h2>
        <form className="form-grid" onSubmit={onSubmit}>
          <input required placeholder="Nombre" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <input required placeholder="Red lógica" value={form.network_name} onChange={(e) => setForm({ ...form, network_name: e.target.value })} />
          <input placeholder="Parent Company ID (opcional)" value={form.parent_company_id} onChange={(e) => setForm({ ...form, parent_company_id: e.target.value })} />
          <button type="submit">Crear empresa</button>
        </form>
      </section>

      <DataTable
        title="Empresas"
        rows={rows}
        searchBy={['name', 'id', 'network_name']}
        filters={['core', 'reseller']}
        columns={[
          { key: 'name', label: 'Nombre' },
          { key: 'id', label: 'ID' },
          { key: 'network_name', label: 'Red' },
          {
            key: 'status',
            label: 'Tipo',
            render: (value) => <Badge tone={value === 'core' ? 'success' : 'warning'}>{value}</Badge>,
          },
        ]}
      />
    </div>
  )
}

function ClientesPage({ companies, onCreateCustomer }) {
  const [form, setForm] = useState({ company_id: '', name: '', email: '', plan_name: '' })

  async function onSubmit(event) {
    event.preventDefault()
    await onCreateCustomer(form)
    setForm({ company_id: '', name: '', email: '', plan_name: '' })
  }

  return (
    <div className="page-grid">
      <section className="panel">
        <h2>Alta de Cliente</h2>
        <form className="form-grid" onSubmit={onSubmit}>
          <select required value={form.company_id} onChange={(e) => setForm({ ...form, company_id: e.target.value })}>
            <option value="">Seleccionar empresa</option>
            {companies.map((company) => (
              <option key={company.id} value={company.id}>
                {company.name}
              </option>
            ))}
          </select>
          <input required placeholder="Nombre cliente" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <input required type="email" placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          <input required placeholder="Plan (ej: 100Mbps)" value={form.plan_name} onChange={(e) => setForm({ ...form, plan_name: e.target.value })} />
          <button type="submit">Crear cliente</button>
        </form>
      </section>

      <section className="panel muted">
        <h2>Tip UISP</h2>
        <p>Después del alta, puedes usar el endpoint de cambio de estado para activar/suspender y disparar automatizaciones n8n.</p>
      </section>
    </div>
  )
}

function PlaceholderPage({ title, description, status = 'planned' }) {
  return (
    <section className="panel">
      <div className="panel-header">
        <h2>{title}</h2>
        <Badge tone={status === 'active' ? 'success' : 'neutral'}>{status}</Badge>
      </div>
      <p>{description}</p>
    </section>
  )
}

function LoginPage({ onLogin }) {
  return (
    <div className="login-screen">
      <section className="login-card">
        <h1>RTK CRM</h1>
        <p>Sesión simulada (mock) para rutas protegidas.</p>
        <button onClick={onLogin}>Entrar</button>
      </section>
    </div>
  )
}

function ProtectedLayout({ session, onLogout, apiStatus, children }) {
  const location = useLocation()

  if (!session.loggedIn) {
    return <Navigate to="/login" replace />
  }

  return (
    <div className="layout">
      <aside className="sidebar">
        <div>
          <h1>RTK CRM</h1>
          <p>Network Operations</p>
        </div>
        <nav>
          {NAV_ITEMS.map((item) => (
            <NavLink key={item.to} to={item.to} className={({ isActive }) => (isActive ? 'active' : '')}>
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <section className="main">
        <header className="topbar">
          <div>
            <strong>{NAV_ITEMS.find((item) => location.pathname.startsWith(item.to))?.label || 'Panel'}</strong>
          </div>
          <div className="actions-inline">
            <Badge tone={apiStatus === 'ok' ? 'success' : 'danger'}>{apiStatus === 'ok' ? 'API Online' : 'API Offline'}</Badge>
            <button className="ghost" onClick={onLogout}>Salir</button>
          </div>
        </header>

        <main className="content">{children}</main>
      </section>
    </div>
  )
}

export default function App() {
  const navigate = useNavigate()
  const [session, setSession] = useState({ loggedIn: false, user: 'ops@rtk.local' })
  const [apiStatus, setApiStatus] = useState('loading')
  const [companies, setCompanies] = useState([])
  const [isLoadingCompanies, setIsLoadingCompanies] = useState(true)
  const [error, setError] = useState('')

  async function loadHealth() {
    try {
      const data = await request('/health')
      setApiStatus(data.status)
    } catch {
      setApiStatus('down')
    }
  }

  async function loadCompanies() {
    setIsLoadingCompanies(true)
    setError('')
    try {
      const data = await request('/companies')
      setCompanies(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setIsLoadingCompanies(false)
    }
  }

  useEffect(() => {
    loadHealth()
  }, [])

  useEffect(() => {
    if (session.loggedIn) {
      loadCompanies()
    }
  }, [session.loggedIn])

  async function createCompany(payload) {
    setError('')
    try {
      await request('/companies', { method: 'POST', body: JSON.stringify(payload) })
      await loadCompanies()
    } catch (err) {
      setError(err.message)
    }
  }

  async function createCustomer(payload) {
    setError('')
    try {
      await request(`/companies/${payload.company_id}/customers`, {
        method: 'POST',
        body: JSON.stringify({ name: payload.name, email: payload.email, plan_name: payload.plan_name }),
      })
    } catch (err) {
      setError(err.message)
    }
  }

  function login() {
    setSession((prev) => ({ ...prev, loggedIn: true }))
    navigate('/dashboard')
  }

  function logout() {
    setSession((prev) => ({ ...prev, loggedIn: false }))
    navigate('/login')
  }

  return (
    <>
      {error && <div className="global-error">{error}</div>}
      <Routes>
        <Route path="/login" element={<LoginPage onLogin={login} />} />

        <Route
          path="/*"
          element={(
            <ProtectedLayout session={session} onLogout={logout} apiStatus={apiStatus}>
              {isLoadingCompanies && <p className="loading">Cargando datos...</p>}
              <Routes>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<DashboardPage apiStatus={apiStatus} companiesCount={companies.length} />} />
                <Route path="/empresas" element={<EmpresasPage companies={companies} onCreateCompany={createCompany} />} />
                <Route path="/clientes" element={<ClientesPage companies={companies} onCreateCustomer={createCustomer} />} />
                <Route
                  path="/integraciones"
                  element={<PlaceholderPage title="Integraciones" description="Conexiones por empresa: UISP, OpenAI, n8n y Google." status="active" />}
                />
                <Route
                  path="/monitoreo"
                  element={<PlaceholderPage title="Monitoreo" description="Vista para salud operativa, métricas de red y alertas de clientes." />}
                />
                <Route
                  path="/comunicaciones"
                  element={<PlaceholderPage title="Comunicaciones" description="Consola tipo inbox para flujos omnicanal y campañas automáticas." />}
                />
                <Route
                  path="/configuracion"
                  element={<PlaceholderPage title="Configuración" description="Parámetros globales por tenant, claves API y reglas de automatización." />}
                />
              </Routes>
            </ProtectedLayout>
          )}
        />
      </Routes>
    </>
  )
}

import { useEffect, useMemo, useState } from 'react'
import { Navigate, NavLink, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import {
  clearToken,
  createCustomerForTenant,
  createTenant,
  getMe,
  getToken,
  getUispCustomerServices,
  listCustomersByTenant,
  listIntegrations,
  listTenants,
  login,
  request,
  saveIntegration,
  searchUispCustomers,
  testIntegration,
  testUisp,
} from './api'

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/empresas', label: 'Empresas' },
  { to: '/clientes', label: 'Clientes' },
  { to: '/integraciones', label: 'Integraciones' },
  { to: '/uisp', label: 'UISP' },
  { to: '/monitoreo', label: 'Monitoreo' },
  { to: '/comunicaciones', label: 'Comunicaciones' },
  { to: '/configuracion', label: 'Configuración' },
]

function Badge({ children, tone = 'neutral' }) {
  return <span className={`badge badge-${tone}`}>{children}</span>
}

function DataTable({ title, columns, rows, searchBy = [] }) {
  const [query, setQuery] = useState('')
  const filteredRows = useMemo(() => {
    const q = query.trim().toLowerCase()
    return rows.filter((row) => !q || searchBy.some((key) => String(row[key] ?? '').toLowerCase().includes(q)))
  }, [query, rows, searchBy])

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>{title}</h2>
        <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Buscar..." />
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>{columns.map((col) => <th key={col.key}>{col.label}</th>)}</tr>
          </thead>
          <tbody>
            {filteredRows.map((row) => (
              <tr key={row.id}>{columns.map((col) => <td key={col.key}>{col.render ? col.render(row[col.key], row) : row[col.key]}</td>)}</tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

function DashboardPage({ apiStatus, tenantCount, customerCount, integrationCount }) {
  const cards = [
    { title: 'Estado API', value: apiStatus === 'ok' ? 'Online' : 'Offline' },
    { title: 'Tenants', value: tenantCount },
    { title: 'Clientes (tenant activo)', value: customerCount },
    { title: 'Integraciones', value: integrationCount },
  ]

  return (
    <section className="panel">
      <h2>Resumen</h2>
      <div className="kpi-grid">
        {cards.map((item) => (
          <article className="kpi-card" key={item.title}>
            <p className="kpi-title">{item.title}</p>
            <h3>{item.value}</h3>
          </article>
        ))}
      </div>
    </section>
  )
}

function TenantsPage({ tenants, onCreateTenant }) {
  const [form, setForm] = useState({ name: '', network_name: '' })

  return (
    <div className="page-grid">
      <section className="panel">
        <h2>Crear tenant</h2>
        <form
          className="form-grid"
          onSubmit={async (e) => {
            e.preventDefault()
            await onCreateTenant(form)
            setForm({ name: '', network_name: '' })
          }}
        >
          <input required placeholder="Nombre" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <input required placeholder="Red lógica" value={form.network_name} onChange={(e) => setForm({ ...form, network_name: e.target.value })} />
          <button type="submit">Crear</button>
        </form>
      </section>

      <DataTable
        title="Tenants"
        rows={tenants}
        searchBy={['id', 'name', 'network_name']}
        columns={[{ key: 'name', label: 'Nombre' }, { key: 'network_name', label: 'Red' }, { key: 'id', label: 'ID' }]}
      />
    </div>
  )
}

function CustomersPage({ tenants, selectedTenantId, onTenantChange, customers, onCreateCustomer }) {
  const [form, setForm] = useState({ name: '', email: '', plan_name: '', status: 'active' })

  return (
    <div className="page-grid">
      <section className="panel">
        <h2>Clientes por tenant</h2>
        <select value={selectedTenantId} onChange={(e) => onTenantChange(e.target.value)}>
          <option value="">Selecciona tenant</option>
          {tenants.map((tenant) => <option key={tenant.id} value={tenant.id}>{tenant.name}</option>)}
        </select>
        <form
          className="form-grid"
          onSubmit={async (e) => {
            e.preventDefault()
            await onCreateCustomer(form)
            setForm({ name: '', email: '', plan_name: '', status: 'active' })
          }}
        >
          <input required placeholder="Nombre" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <input required type="email" placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          <input required placeholder="Plan" value={form.plan_name} onChange={(e) => setForm({ ...form, plan_name: e.target.value })} />
          <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
            <option value="active">active</option>
            <option value="suspended">suspended</option>
          </select>
          <button type="submit" disabled={!selectedTenantId}>Crear cliente</button>
        </form>
      </section>

      <DataTable
        title="Listado de clientes"
        rows={customers}
        searchBy={['name', 'email', 'plan_name', 'status']}
        columns={[
          { key: 'name', label: 'Nombre' },
          { key: 'email', label: 'Email' },
          { key: 'plan_name', label: 'Plan' },
          { key: 'status', label: 'Estado', render: (v) => <Badge tone={v === 'active' ? 'success' : 'warning'}>{v}</Badge> },
        ]}
      />
    </div>
  )
}

function IntegrationsPage({ selectedTenantId, integrations, onSaveIntegration, onTestIntegration, onTestUisp }) {
  const [forms, setForms] = useState({
    uisp: { base_url: '', app_key: '', token: '' },
    chatwoot: { base_url: '', api_key: '' },
    n8n: { base_url: '', api_key: '' },
  })
  const [results, setResults] = useState({})

  async function handleSave(provider) {
    await onSaveIntegration(provider, forms[provider])
  }

  async function handleTest(provider) {
    if (provider === 'uisp') {
      const result = await onTestUisp()
      setResults((prev) => ({ ...prev, [provider]: result.ok ? '✅ Conexión OK' : `❌ ${result.detail}` }))
      return
    }

    const existing = integrations.find((item) => item.provider === provider)
    if (!existing) {
      setResults((prev) => ({ ...prev, [provider]: 'Guarda la integración primero' }))
      return
    }
    const result = await onTestIntegration(existing.id)
    setResults((prev) => ({ ...prev, [provider]: result.ok ? '✅ Conexión OK' : `❌ ${result.detail}` }))
  }

  return (
    <div className="page-grid provider-grid">
      {['uisp', 'chatwoot', 'n8n'].map((provider) => (
        <section className="panel" key={provider}>
          <div className="panel-header">
            <h2>{provider.toUpperCase()}</h2>
            <Badge tone={integrations.some((item) => item.provider === provider) ? 'success' : 'neutral'}>
              {integrations.some((item) => item.provider === provider) ? 'Configurado' : 'Pendiente'}
            </Badge>
          </div>
          <div className="form-grid">
            <input placeholder="Base URL" value={forms[provider].base_url} onChange={(e) => setForms((prev) => ({ ...prev, [provider]: { ...prev[provider], base_url: e.target.value } }))} />
            {provider === 'uisp' ? (
              <>
                <input placeholder="App Key" value={forms.uisp.app_key} onChange={(e) => setForms((prev) => ({ ...prev, uisp: { ...prev.uisp, app_key: e.target.value } }))} />
                <input placeholder="Token" value={forms.uisp.token} onChange={(e) => setForms((prev) => ({ ...prev, uisp: { ...prev.uisp, token: e.target.value } }))} />
              </>
            ) : (
              <input placeholder="API Key (opcional)" value={forms[provider].api_key} onChange={(e) => setForms((prev) => ({ ...prev, [provider]: { ...prev[provider], api_key: e.target.value } }))} />
            )}
            <button onClick={() => handleSave(provider)} disabled={!selectedTenantId}>Guardar</button>
            <button className="ghost" onClick={() => handleTest(provider)} disabled={!selectedTenantId}>Probar conexión</button>
            {results[provider] && <small>{results[provider]}</small>}
          </div>
        </section>
      ))}
    </div>
  )
}

function UispSearchPage({ selectedTenantId }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [services, setServices] = useState({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function runSearch() {
    if (!selectedTenantId || !query.trim()) return
    setLoading(true)
    setError('')
    try {
      const data = await searchUispCustomers(selectedTenantId, query)
      setResults(data.results || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function loadServices(customerId) {
    setError('')
    try {
      const data = await getUispCustomerServices(selectedTenantId, customerId)
      setServices((prev) => ({ ...prev, [customerId]: data.services || [] }))
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <section className="panel">
      <h2>UISP · Buscar cliente</h2>
      <div className="actions-inline">
        <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Nombre, email o id" />
        <button onClick={runSearch} disabled={!selectedTenantId || loading}>{loading ? 'Buscando...' : 'Buscar'}</button>
      </div>
      {error && <p className="inline-error">{error}</p>}
      <div className="table-wrap">
        <table>
          <thead>
            <tr><th>ID</th><th>Nombre</th><th>Email</th><th>Estado</th><th>Servicios</th></tr>
          </thead>
          <tbody>
            {results.map((row) => (
              <tr key={row.id || row.name}>
                <td>{row.id}</td>
                <td>{row.name}</td>
                <td>{row.email}</td>
                <td><Badge tone={row.status === 'active' ? 'success' : 'warning'}>{row.status}</Badge></td>
                <td>
                  <button className="ghost" onClick={() => loadServices(row.id)}>Ver servicios</button>
                  {services[row.id] && <div><small>{services[row.id].length} servicios</small></div>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

function LoginPage({ onSubmit, loading, error }) {
  const [credentials, setCredentials] = useState({ username: '', password: '' })
  return (
    <div className="login-screen">
      <section className="login-card">
        <h1>RTK CRM</h1>
        <form className="form-grid" onSubmit={(e) => { e.preventDefault(); onSubmit(credentials) }}>
          <input placeholder="Usuario" required value={credentials.username} onChange={(e) => setCredentials({ ...credentials, username: e.target.value })} />
          <input placeholder="Contraseña" type="password" required value={credentials.password} onChange={(e) => setCredentials({ ...credentials, password: e.target.value })} />
          <button type="submit" disabled={loading}>{loading ? 'Ingresando...' : 'Entrar'}</button>
        </form>
        {error && <p className="inline-error">{error}</p>}
      </section>
    </div>
  )
}

function PlaceholderPage({ title }) {
  return <section className="panel"><h2>{title}</h2><p>Módulo en construcción.</p></section>
}

function ProtectedLayout({ isAuthenticated, apiStatus, onLogout, tenants, selectedTenantId, onTenantChange, children }) {
  const location = useLocation()
  if (!isAuthenticated) return <Navigate to="/login" replace />

  return (
    <div className="layout">
      <aside className="sidebar">
        <div><h1>RTK CRM</h1><p>Multi-tenant basic</p></div>
        <nav>{NAV_ITEMS.map((item) => <NavLink key={item.to} to={item.to} className={({ isActive }) => (isActive ? 'active' : '')}>{item.label}</NavLink>)}</nav>
      </aside>
      <section className="main">
        <header className="topbar">
          <strong>{NAV_ITEMS.find((item) => location.pathname.startsWith(item.to))?.label || 'Panel'}</strong>
          <div className="actions-inline">
            <select value={selectedTenantId} onChange={(e) => onTenantChange(e.target.value)}><option value="">Tenant</option>{tenants.map((tenant) => <option key={tenant.id} value={tenant.id}>{tenant.name}</option>)}</select>
            <Badge tone={apiStatus === 'ok' ? 'success' : 'danger'}>{apiStatus}</Badge>
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
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [authLoading, setAuthLoading] = useState(false)
  const [authError, setAuthError] = useState('')
  const [error, setError] = useState('')
  const [apiStatus, setApiStatus] = useState('loading')
  const [tenants, setTenants] = useState([])
  const [selectedTenantId, setSelectedTenantId] = useState(localStorage.getItem('rtk_tenant_id') || '')
  const [customers, setCustomers] = useState([])
  const [integrations, setIntegrations] = useState([])

  async function loadHealth() {
    try {
      const data = await request('/health')
      setApiStatus(data.status)
    } catch {
      setApiStatus('down')
    }
  }

  async function loadTenants() {
    const data = await listTenants()
    setTenants(data)
    if (!selectedTenantId && data.length > 0) {
      setSelectedTenantId(data[0].id)
      localStorage.setItem('rtk_tenant_id', data[0].id)
    }
  }

  async function loadCustomers(tenantId) {
    if (!tenantId) {
      setCustomers([])
      return
    }
    setCustomers(await listCustomersByTenant(tenantId))
  }

  async function loadIntegrations(tenantId) {
    if (!tenantId) {
      setIntegrations([])
      return
    }
    setIntegrations(await listIntegrations(tenantId))
  }

  useEffect(() => { loadHealth() }, [])

  useEffect(() => {
    const run = async () => {
      const token = getToken()
      if (!token) return
      try {
        await getMe()
        setIsAuthenticated(true)
        await loadTenants()
      } catch {
        clearToken()
      }
    }
    run()
  }, [])

  useEffect(() => {
    if (isAuthenticated) {
      loadCustomers(selectedTenantId)
      loadIntegrations(selectedTenantId)
    }
  }, [selectedTenantId, isAuthenticated])

  async function handleLogin(credentials) {
    setAuthLoading(true)
    setAuthError('')
    try {
      await login(credentials.username, credentials.password)
      await getMe()
      setIsAuthenticated(true)
      await loadTenants()
      navigate('/dashboard')
    } catch (err) {
      setAuthError(err.message)
    } finally {
      setAuthLoading(false)
    }
  }

  async function handleCreateTenant(payload) {
    try {
      setError('')
      await createTenant(payload)
      await loadTenants()
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleCreateCustomer(payload) {
    try {
      setError('')
      await createCustomerForTenant(selectedTenantId, payload)
      await loadCustomers(selectedTenantId)
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleSaveIntegration(provider, config) {
    try {
      setError('')
      await saveIntegration(selectedTenantId, provider, config)
      await loadIntegrations(selectedTenantId)
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleTestIntegration(integrationId) {
    try {
      setError('')
      return await testIntegration(selectedTenantId, integrationId)
    } catch (err) {
      setError(err.message)
      return { ok: false, detail: err.message }
    }
  }

  async function handleTestUisp() {
    try {
      setError('')
      return await testUisp(selectedTenantId)
    } catch (err) {
      setError(err.message)
      return { ok: false, detail: err.message }
    }
  }

  function handleTenantChange(tenantId) {
    setSelectedTenantId(tenantId)
    localStorage.setItem('rtk_tenant_id', tenantId)
  }

  function logout() {
    clearToken()
    setIsAuthenticated(false)
    navigate('/login')
  }

  return (
    <>
      {error && <div className="global-error">{error}</div>}
      <Routes>
        <Route path="/login" element={<LoginPage onSubmit={handleLogin} loading={authLoading} error={authError} />} />
        <Route
          path="/*"
          element={
            <ProtectedLayout isAuthenticated={isAuthenticated} apiStatus={apiStatus} onLogout={logout} tenants={tenants} selectedTenantId={selectedTenantId} onTenantChange={handleTenantChange}>
              <Routes>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<DashboardPage apiStatus={apiStatus} tenantCount={tenants.length} customerCount={customers.length} integrationCount={integrations.length} />} />
                <Route path="/empresas" element={<TenantsPage tenants={tenants} onCreateTenant={handleCreateTenant} />} />
                <Route path="/clientes" element={<CustomersPage tenants={tenants} selectedTenantId={selectedTenantId} onTenantChange={handleTenantChange} customers={customers} onCreateCustomer={handleCreateCustomer} />} />
                <Route path="/integraciones" element={<IntegrationsPage selectedTenantId={selectedTenantId} integrations={integrations} onSaveIntegration={handleSaveIntegration} onTestIntegration={handleTestIntegration} onTestUisp={handleTestUisp} />} />
                <Route path="/uisp" element={<UispSearchPage selectedTenantId={selectedTenantId} />} />
                <Route path="/monitoreo" element={<PlaceholderPage title="Monitoreo" />} />
                <Route path="/comunicaciones" element={<PlaceholderPage title="Comunicaciones" />} />
                <Route path="/configuracion" element={<PlaceholderPage title="Configuración" />} />
              </Routes>
            </ProtectedLayout>
          }
        />
      </Routes>
    </>
  )
}

import { useEffect, useState } from 'react'
import { request } from './api'

function Card({ title, children }) {
  return (
    <section className="card">
      <h2>{title}</h2>
      {children}
    </section>
  )
}

export default function App() {
  const [health, setHealth] = useState('loading')
  const [companies, setCompanies] = useState([])
  const [loadingCompanies, setLoadingCompanies] = useState(false)
  const [error, setError] = useState('')

  const [companyForm, setCompanyForm] = useState({ name: '', network_name: '', parent_company_id: '' })
  const [customerForm, setCustomerForm] = useState({ company_id: '', name: '', email: '', plan_name: '' })

  async function loadHealth() {
    try {
      const data = await request('/health')
      setHealth(data.status)
    } catch {
      setHealth('down')
    }
  }

  async function loadCompanies() {
    setLoadingCompanies(true)
    setError('')
    try {
      const data = await request('/companies')
      setCompanies(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoadingCompanies(false)
    }
  }

  useEffect(() => {
    loadHealth()
    loadCompanies()
  }, [])

  async function submitCompany(event) {
    event.preventDefault()
    setError('')
    try {
      await request('/companies', {
        method: 'POST',
        body: JSON.stringify({
          ...companyForm,
          parent_company_id: companyForm.parent_company_id || null,
        }),
      })
      setCompanyForm({ name: '', network_name: '', parent_company_id: '' })
      await loadCompanies()
    } catch (err) {
      setError(err.message)
    }
  }

  async function submitCustomer(event) {
    event.preventDefault()
    setError('')
    try {
      await request(`/companies/${customerForm.company_id}/customers`, {
        method: 'POST',
        body: JSON.stringify({
          name: customerForm.name,
          email: customerForm.email,
          plan_name: customerForm.plan_name,
        }),
      })
      setCustomerForm({ company_id: '', name: '', email: '', plan_name: '' })
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <main className="layout">
      <header className="hero">
        <h1>RTK CRM Frontend (React + Vite)</h1>
        <p>Estado API: <strong className={health === 'ok' ? 'ok' : 'bad'}>{health}</strong></p>
      </header>

      {error && <div className="error">{error}</div>}

      <div className="grid">
        <Card title="Companies">
          <form onSubmit={submitCompany} className="form">
            <input placeholder="Nombre" value={companyForm.name} onChange={(e) => setCompanyForm({ ...companyForm, name: e.target.value })} required />
            <input placeholder="Red lógica" value={companyForm.network_name} onChange={(e) => setCompanyForm({ ...companyForm, network_name: e.target.value })} required />
            <input placeholder="Parent company id (opcional)" value={companyForm.parent_company_id} onChange={(e) => setCompanyForm({ ...companyForm, parent_company_id: e.target.value })} />
            <button type="submit">Crear compañía</button>
          </form>
          <button onClick={loadCompanies} className="secondary">Refrescar</button>
          {loadingCompanies ? <p>Cargando...</p> : (
            <ul>
              {companies.map((company) => (
                <li key={company.id}>
                  <strong>{company.name}</strong><br />
                  {company.id}<br />
                  red: {company.network_name}
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card title="Customers">
          <form onSubmit={submitCustomer} className="form">
            <input placeholder="Company ID" value={customerForm.company_id} onChange={(e) => setCustomerForm({ ...customerForm, company_id: e.target.value })} required />
            <input placeholder="Nombre cliente" value={customerForm.name} onChange={(e) => setCustomerForm({ ...customerForm, name: e.target.value })} required />
            <input placeholder="Email" type="email" value={customerForm.email} onChange={(e) => setCustomerForm({ ...customerForm, email: e.target.value })} required />
            <input placeholder="Plan" value={customerForm.plan_name} onChange={(e) => setCustomerForm({ ...customerForm, plan_name: e.target.value })} required />
            <button type="submit">Crear customer</button>
          </form>
        </Card>
      </div>
    </main>
  )
}

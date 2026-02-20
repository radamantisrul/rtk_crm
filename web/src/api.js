const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const API_KEY = import.meta.env.VITE_API_KEY || ''
const TOKEN_KEY = 'rtk_auth_token'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY) || ''
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}

function currentTenantHeader() {
  return localStorage.getItem('rtk_tenant_id') || 'bootstrap'
}

export async function request(path, options = {}) {
  const token = getToken()
  const headers = {
    'Content-Type': 'application/json',
    ...(API_KEY ? { 'x-api-key': API_KEY } : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  })

  const contentType = response.headers.get('content-type') || ''
  const data = contentType.includes('application/json') ? await response.json() : await response.text()

  if (!response.ok) {
    const message = typeof data === 'object' && data?.detail ? data.detail : 'Error inesperado'
    throw new Error(message)
  }

  return data
}

export async function login(username, password) {
  const data = await request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  })
  setToken(data.access_token)
  return data
}

export async function getMe() {
  return request('/auth/me')
}

export async function listTenants() {
  return request('/tenants', { headers: { 'X-Tenant-Id': currentTenantHeader() } })
}

export async function createTenant(payload) {
  return request('/tenants', { method: 'POST', headers: { 'X-Tenant-Id': currentTenantHeader() }, body: JSON.stringify(payload) })
}

export async function listCustomersByTenant(tenantId) {
  return request('/customers', { headers: { 'X-Tenant-Id': tenantId } })
}

export async function createCustomerForTenant(tenantId, payload) {
  return request('/customers', {
    method: 'POST',
    headers: { 'X-Tenant-Id': tenantId },
    body: JSON.stringify(payload),
  })
}

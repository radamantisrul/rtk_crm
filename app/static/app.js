const logs = document.getElementById('logs');
const companiesList = document.getElementById('companies');
const dashboardOutput = document.getElementById('dashboard-output');

function log(title, data) {
  logs.textContent = `[${new Date().toLocaleTimeString()}] ${title}\n${JSON.stringify(data, null, 2)}\n\n` + logs.textContent;
}

async function api(url, options = {}) {
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Error inesperado');
  }
  return data;
}

async function refreshCompanies() {
  const companies = await api('/companies');
  companiesList.innerHTML = '';

  if (!companies.length) {
    companiesList.innerHTML = '<li>No hay compañías aún.</li>';
    return;
  }

  companies.forEach((company) => {
    const li = document.createElement('li');
    li.innerHTML = `<strong>${company.name}</strong><br>ID: ${company.id}<br>Red: ${company.network_name}${company.parent_company_id ? `<br>Padre: ${company.parent_company_id}` : ''}`;
    companiesList.appendChild(li);
  });
}

document.getElementById('company-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const form = new FormData(event.target);
  try {
    const payload = {
      name: form.get('name'),
      network_name: form.get('network_name'),
      parent_company_id: form.get('parent_company_id') || null,
    };
    const company = await api('/companies', { method: 'POST', body: JSON.stringify(payload) });
    log('Compañía creada', company);
    event.target.reset();
    await refreshCompanies();
  } catch (error) {
    log('Error creando compañía', { message: error.message });
  }
});

document.getElementById('refresh-companies').addEventListener('click', async () => {
  try {
    await refreshCompanies();
  } catch (error) {
    log('Error listando compañías', { message: error.message });
  }
});

document.getElementById('customer-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const form = new FormData(event.target);
  const companyId = form.get('company_id');
  try {
    const payload = {
      name: form.get('name'),
      email: form.get('email'),
      plan_name: form.get('plan_name'),
    };
    const customer = await api(`/companies/${companyId}/customers`, { method: 'POST', body: JSON.stringify(payload) });
    log('Cliente creado', customer);
    event.target.reset();
  } catch (error) {
    log('Error creando cliente', { message: error.message });
  }
});

document.getElementById('status-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const form = new FormData(event.target);
  const companyId = form.get('company_id');
  const customerId = form.get('customer_id');

  try {
    const payload = {
      status: form.get('status'),
      reason: form.get('reason') || null,
    };
    const result = await api(`/companies/${companyId}/customers/${customerId}/status`, { method: 'POST', body: JSON.stringify(payload) });
    log('Estado actualizado (UISP + n8n)', result);
  } catch (error) {
    log('Error actualizando estado', { message: error.message });
  }
});

document.getElementById('dashboard-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const form = new FormData(event.target);
  const companyId = form.get('company_id');

  try {
    const dashboard = await api(`/companies/${companyId}/dashboard`);
    dashboardOutput.textContent = JSON.stringify(dashboard, null, 2);
    log('Dashboard cargado', dashboard);
  } catch (error) {
    log('Error cargando dashboard', { message: error.message });
  }
});

refreshCompanies().catch((error) => log('Error inicial', { message: error.message }));

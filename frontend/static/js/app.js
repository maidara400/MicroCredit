const API = '/api';

// ===== UTILS TOKEN =====
function getToken() { return localStorage.getItem('access_token'); }
function getRefresh() { return localStorage.getItem('refresh_token'); }
function getUser() { return JSON.parse(localStorage.getItem('user') || 'null'); }

function setSession(data) {
  localStorage.setItem('access_token', data.access);
  localStorage.setItem('refresh_token', data.refresh);
  localStorage.setItem('user', JSON.stringify(data.user));
}

function clearSession() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
}

async function apiFetch(url, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  const token = getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;

  let res = await fetch(API + url, { ...options, headers });

  // Token expiré → refresh automatique
  if (res.status === 401 && getRefresh()) {
    const rRes = await fetch(API + '/auth/token/refresh/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: getRefresh() })
    });
    if (rRes.ok) {
      const rData = await rRes.json();
      localStorage.setItem('access_token', rData.access);
      headers['Authorization'] = `Bearer ${rData.access}`;
      res = await fetch(API + url, { ...options, headers });
    } else {
      clearSession();
      showPage('auth');
      return null;
    }
  }
  return res;
}

// ===== PAGES / NAVIGATION =====
function showPage(page) {
  document.getElementById('page-auth').classList.add('hidden');
  document.getElementById('page-dashboard').classList.add('hidden');
  document.getElementById('navbar').classList.add('hidden');
  if (page === 'auth') {
    document.getElementById('page-auth').classList.remove('hidden');
  } else {
    document.getElementById('navbar').classList.remove('hidden');
    document.getElementById('page-dashboard').classList.remove('hidden');
  }
}

function showTab(tab) {
  document.getElementById('form-login').classList.toggle('hidden', tab !== 'login');
  document.getElementById('form-register').classList.toggle('hidden', tab !== 'register');
  document.querySelectorAll('.tab').forEach((t, i) => {
    t.classList.toggle('active', (i === 0 && tab === 'login') || (i === 1 && tab === 'register'));
  });
}

function showModal(id) { document.getElementById(id).classList.remove('hidden'); }
function hideModal(id) { document.getElementById(id).classList.add('hidden'); }

function showError(id, msg) {
  const el = document.getElementById(id);
  el.textContent = msg;
  el.classList.remove('hidden');
}
function hideError(id) { document.getElementById(id).classList.add('hidden'); }

function fillDemo(email, pass) {
  document.getElementById('login-email').value = email;
  document.getElementById('login-password').value = pass;
}

// ===== AUTH =====
async function login(e) {
  e.preventDefault();
  hideError('login-error');
  const email = document.getElementById('login-email').value;
  const password = document.getElementById('login-password').value;

  const res = await fetch(API + '/auth/login/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  const data = await res.json();

  if (!res.ok) {
    showError('login-error', data.detail || 'Email ou mot de passe incorrect.');
    return;
  }

  // Récupérer le profil
  const meRes = await fetch(API + '/auth/me/', {
    headers: { 'Authorization': `Bearer ${data.access}` }
  });
  const user = await meRes.json();

  setSession({ access: data.access, refresh: data.refresh, user });
  loadDashboard();
}

async function register(e) {
  e.preventDefault();
  hideError('register-error');
  const body = {
    first_name: document.getElementById('reg-firstname').value,
    last_name: document.getElementById('reg-lastname').value,
    username: document.getElementById('reg-username').value,
    email: document.getElementById('reg-email').value,
    telephone: document.getElementById('reg-phone').value,
    password: document.getElementById('reg-password').value,
    password2: document.getElementById('reg-password2').value,
  };
  const res = await fetch(API + '/auth/register/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  const data = await res.json();
  if (!res.ok) {
    const msg = Object.values(data).flat().join(' ');
    showError('register-error', msg);
    return;
  }
  setSession(data);
  loadDashboard();
}

function logout() {
  clearSession();
  showPage('auth');
}

// ===== DASHBOARD =====
function loadDashboard() {
  showPage('dashboard');
  const user = getUser();
  document.getElementById('nav-user').textContent = `${user.first_name} ${user.last_name} (${user.role})`;

  ['dash-client', 'dash-agent', 'dash-admin'].forEach(id => document.getElementById(id).classList.add('hidden'));

  if (user.role === 'client') loadClientDash();
  else if (user.role === 'agent') loadAgentDash();
  else loadAdminDash();
}

// ===== CLIENT =====
async function loadClientDash() {
  document.getElementById('dash-client').classList.remove('hidden');
  const [demRes, pretRes] = await Promise.all([
    apiFetch('/demandes/'),
    apiFetch('/prets/')
  ]);
  const demandes = await demRes.json();
  const prets = await pretRes.json();
  const pretActif = prets.find(p => p.statut === 'actif');

  // Stats
  document.getElementById('client-stats').innerHTML = `
    <div class="stat-card"><div class="stat-value">${demandes.length}</div><div class="stat-label">Demandes</div></div>
    <div class="stat-card"><div class="stat-value">${prets.filter(p=>p.statut==='actif').length}</div><div class="stat-label">Prêt actif</div></div>
    <div class="stat-card"><div class="stat-value">${prets.filter(p=>p.statut==='solde').length}</div><div class="stat-label">Prêts soldés</div></div>
    ${pretActif ? `<div class="stat-card"><div class="stat-value">${pretActif.echeances_restantes}</div><div class="stat-label">Échéances restantes</div></div>` : ''}
  `;

  // Demandes
  if (demandes.length === 0) {
    document.getElementById('client-demandes').innerHTML = '<div class="empty"><p>Aucune demande. Cliquez sur "+ Nouvelle demande" pour commencer.</p></div>';
  } else {
    document.getElementById('client-demandes').innerHTML = `
      <div class="table-wrap"><table>
        <tr><th>#</th><th>Montant</th><th>Durée</th><th>Mensualité</th><th>Statut</th><th>Date</th><th>Motif refus</th></tr>
        ${demandes.map(d => `
          <tr>
            <td>${d.id}</td>
            <td>${Number(d.montant).toLocaleString()} FCFA</td>
            <td>${d.duree_mois} mois</td>
            <td>${d.mensualite_estimee?.toLocaleString()} FCFA</td>
            <td>${badge(d.statut)}</td>
            <td>${new Date(d.date_soumission).toLocaleDateString('fr-FR')}</td>
            <td>${d.motif_refus || '—'}</td>
          </tr>`).join('')}
      </table></div>`;
  }

  // Prêt actif
  if (pretActif) {
    document.getElementById('client-pret').innerHTML = `
      <div class="cards-row">
        <div class="stat-card"><div class="stat-value">${Number(pretActif.montant_total).toLocaleString()}</div><div class="stat-label">Montant total (FCFA)</div></div>
        <div class="stat-card"><div class="stat-value">${Number(pretActif.mensualite).toLocaleString()}</div><div class="stat-label">Mensualité (FCFA)</div></div>
        <div class="stat-card"><div class="stat-value">${Number(pretActif.montant_rembourse).toLocaleString()}</div><div class="stat-label">Remboursé (FCFA)</div></div>
        <div class="stat-card"><div class="stat-value">${Number(pretActif.montant_restant).toLocaleString()}</div><div class="stat-label">Restant (FCFA)</div></div>
      </div>`;
    loadEcheances(pretActif.id);
  } else {
    document.getElementById('client-pret').innerHTML = '<div class="empty"><p>Aucun prêt actif.</p></div>';
    document.getElementById('client-echeances').innerHTML = '';
  }
}

async function loadEcheances(pretId) {
  const res = await apiFetch(`/prets/${pretId}/echeances/`);
  const echeances = await res.json();
  document.getElementById('client-echeances').innerHTML = `
    <div class="table-wrap"><table>
      <tr><th>#</th><th>Montant dû</th><th>Date échéance</th><th>Statut</th><th>Date paiement</th><th>Action</th></tr>
      ${echeances.map(e => `
        <tr>
          <td>${e.numero}</td>
          <td>${Number(e.montant_du).toLocaleString()} FCFA</td>
          <td>${new Date(e.date_echeance).toLocaleDateString('fr-FR')}</td>
          <td>${badge(e.statut)}</td>
          <td>${e.date_paiement ? new Date(e.date_paiement).toLocaleDateString('fr-FR') : '—'}</td>
          <td>${e.statut !== 'paye' ? `<button class="btn btn-sm btn-success" onclick="payerEcheance(${e.id})">Payer</button>` : ''}</td>
        </tr>`).join('')}
    </table></div>`;
}

async function submitDemande(e) {
  e.preventDefault();
  hideError('dem-error');
  const montant = document.getElementById('dem-montant').value;
  const duree = document.getElementById('dem-duree').value;
  const motif = document.getElementById('dem-motif').value;

  const res = await apiFetch('/demandes/', { method: 'POST', body: JSON.stringify({ montant, duree_mois: duree, motif }) });
  const data = await res.json();
  if (!res.ok) {
    showError('dem-error', Object.values(data).flat().join(' '));
    return;
  }
  hideModal('modal-demande');
  loadClientDash();
}

async function payerEcheance(id) {
  if (!confirm('Confirmer le paiement de cette échéance ?')) return;
  const res = await apiFetch(`/prets/echeances/${id}/payer/`, { method: 'POST' });
  const data = await res.json();
  alert(data.detail);
  loadClientDash();
}

// ===== AGENT =====
async function loadAgentDash() {
  document.getElementById('dash-agent').classList.remove('hidden');
  const res = await apiFetch('/demandes/');
  const demandes = await res.json();

  const attente = demandes.filter(d => d.statut === 'en_attente');
  renderAgentDemandes('agent-demandes-attente', attente, true);
  renderAgentDemandes('agent-demandes-all', demandes, false);

  const retardRes = await apiFetch('/prets/echeances/en-retard/');
  const retards = await retardRes.json();
  document.getElementById('agent-retards').innerHTML = retards.length === 0
    ? '<div class="empty"><p>Aucune échéance en retard.</p></div>'
    : `<div class="table-wrap"><table>
        <tr><th>Prêt #</th><th>Échéance #</th><th>Montant</th><th>Date prévue</th></tr>
        ${retards.map(e => `<tr><td>${e.pret}</td><td>${e.numero}</td><td>${Number(e.montant_du).toLocaleString()} FCFA</td><td>${new Date(e.date_echeance).toLocaleDateString('fr-FR')}</td></tr>`).join('')}
      </table></div>`;
}

function renderAgentDemandes(containerId, demandes, showActions) {
  if (demandes.length === 0) {
    document.getElementById(containerId).innerHTML = '<div class="empty"><p>Aucun dossier.</p></div>';
    return;
  }
  document.getElementById(containerId).innerHTML = `
    <div class="table-wrap"><table>
      <tr><th>#</th><th>Client</th><th>Montant</th><th>Durée</th><th>Motif</th><th>Statut</th><th>Date</th>${showActions ? '<th>Actions</th>' : ''}</tr>
      ${demandes.map(d => `
        <tr>
          <td>${d.id}</td>
          <td>${d.client_detail?.first_name} ${d.client_detail?.last_name}</td>
          <td>${Number(d.montant).toLocaleString()} FCFA</td>
          <td>${d.duree_mois} mois</td>
          <td>${d.motif.substring(0, 40)}...</td>
          <td>${badge(d.statut)}</td>
          <td>${new Date(d.date_soumission).toLocaleDateString('fr-FR')}</td>
          ${showActions ? `<td style="display:flex;gap:6px">
            <button class="btn btn-sm btn-success" onclick="approuver(${d.id})">Approuver</button>
            <button class="btn btn-sm btn-danger" onclick="openRefus(${d.id})">Refuser</button>
          </td>` : ''}
        </tr>`).join('')}
    </table></div>`;
}

async function approuver(id) {
  if (!confirm('Approuver cette demande et générer le prêt ?')) return;
  const res = await apiFetch(`/demandes/${id}/approuver/`, { method: 'POST' });
  const data = await res.json();
  alert(data.detail);
  loadAgentDash();
}

function openRefus(id) {
  document.getElementById('refus-demande-id').value = id;
  document.getElementById('refus-motif').value = '';
  hideError('refus-error');
  showModal('modal-refus');
}

async function submitRefus(e) {
  e.preventDefault();
  hideError('refus-error');
  const id = document.getElementById('refus-demande-id').value;
  const motif_refus = document.getElementById('refus-motif').value;
  const res = await apiFetch(`/demandes/${id}/refuser/`, { method: 'POST', body: JSON.stringify({ motif_refus }) });
  const data = await res.json();
  if (!res.ok) { showError('refus-error', Object.values(data).flat().join(' ')); return; }
  hideModal('modal-refus');
  loadAgentDash();
}

// ===== ADMIN =====
async function loadAdminDash() {
  document.getElementById('dash-admin').classList.remove('hidden');
  const [statsRes, usersRes] = await Promise.all([
    apiFetch('/auth/admin/stats/'),
    apiFetch('/auth/admin/users/')
  ]);
  const stats = await statsRes.json();
  const users = await usersRes.json();

  document.getElementById('admin-stats').innerHTML = `
    <div class="stat-card"><div class="stat-value">${stats.utilisateurs.total}</div><div class="stat-label">Utilisateurs</div></div>
    <div class="stat-card"><div class="stat-value">${stats.demandes.en_attente}</div><div class="stat-label">Dossiers en attente</div></div>
    <div class="stat-card"><div class="stat-value">${stats.prets.actifs}</div><div class="stat-label">Prêts actifs</div></div>
    <div class="stat-card"><div class="stat-value">${Number(stats.prets.montant_total_prete).toLocaleString()}</div><div class="stat-label">Total prêté (FCFA)</div></div>
    <div class="stat-card"><div class="stat-value">${stats.remboursements.echeances_en_retard}</div><div class="stat-label">Échéances en retard</div></div>
  `;

  document.getElementById('admin-users').innerHTML = `
    <div class="table-wrap"><table>
      <tr><th>#</th><th>Nom</th><th>Email</th><th>Rôle</th><th>Téléphone</th><th>Statut</th><th>Inscrit le</th></tr>
      ${users.map(u => `
        <tr>
          <td>${u.id}</td>
          <td>${u.first_name} ${u.last_name}</td>
          <td>${u.email}</td>
          <td>${badge(u.role)}</td>
          <td>${u.telephone || '—'}</td>
          <td>${u.is_active ? '<span class="badge badge-success">Actif</span>' : '<span class="badge badge-danger">Inactif</span>'}</td>
          <td>${new Date(u.date_joined).toLocaleDateString('fr-FR')}</td>
        </tr>`).join('')}
    </table></div>`;
}

async function createUser(e) {
  e.preventDefault();
  hideError('cu-error');
  const body = {
    first_name: document.getElementById('cu-firstname').value,
    last_name: document.getElementById('cu-lastname').value,
    username: document.getElementById('cu-username').value,
    email: document.getElementById('cu-email').value,
    role: document.getElementById('cu-role').value,
    password: document.getElementById('cu-password').value,
  };
  const res = await apiFetch('/auth/admin/users/', { method: 'POST', body: JSON.stringify(body) });
  const data = await res.json();
  if (!res.ok) { showError('cu-error', Object.values(data).flat().join(' ')); return; }
  hideModal('modal-create-user');
  loadAdminDash();
}

// ===== HELPERS =====
function badge(statut) {
  const map = {
    en_attente: ['badge-warning', 'En attente'],
    approuve:   ['badge-success', 'Approuvée'],
    refuse:     ['badge-danger', 'Refusée'],
    actif:      ['badge-info', 'Actif'],
    solde:      ['badge-success', 'Soldé'],
    paye:       ['badge-success', 'Payée'],
    en_retard:  ['badge-danger', 'En retard'],
    client:     ['badge-gray', 'Client'],
    agent:      ['badge-info', 'Agent'],
    admin:      ['badge-warning', 'Admin'],
  };
  const [cls, label] = map[statut] || ['badge-gray', statut];
  return `<span class="badge ${cls}">${label}</span>`;
}

// Calcul mensualité en temps réel
document.getElementById('dem-montant')?.addEventListener('input', calcMensualite);
document.getElementById('dem-duree')?.addEventListener('input', calcMensualite);
function calcMensualite() {
  const m = parseFloat(document.getElementById('dem-montant').value);
  const d = parseInt(document.getElementById('dem-duree').value);
  const box = document.getElementById('dem-mensualite');
  if (m > 0 && d > 0) {
    box.textContent = `Mensualité estimée : ${(m / d).toLocaleString('fr-FR', {maximumFractionDigits: 0})} FCFA / mois`;
    box.classList.remove('hidden');
  } else { box.classList.add('hidden'); }
}

// ===== INIT =====
if (getToken() && getUser()) {
  loadDashboard();
}

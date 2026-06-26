const API = '/api';
let allUsers = []; // cache pour le filtre admin

// ===== TOKEN & SESSION =====
const getToken   = () => localStorage.getItem('access_token');
const getRefresh = () => localStorage.getItem('refresh_token');
const getUser    = () => JSON.parse(localStorage.getItem('user') || 'null');

function setSession(data) {
  localStorage.setItem('access_token', data.access);
  localStorage.setItem('refresh_token', data.refresh);
  localStorage.setItem('user', JSON.stringify(data.user));
}
function clearSession() {
  ['access_token','refresh_token','user'].forEach(k => localStorage.removeItem(k));
}

async function apiFetch(url, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  const token = getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;

  let res = await fetch(API + url, { ...options, headers });

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

// ===== TOAST =====
function toast(msg, type = 'info') {
  const icons = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' };
  const el = document.createElement('div');
  el.className = `toast toast-${type}`;
  el.innerHTML = `<span class="toast-icon">${icons[type]}</span><span>${msg}</span>`;
  document.getElementById('toast-container').appendChild(el);
  setTimeout(() => {
    el.style.animation = 'fadeOut .4s ease forwards';
    setTimeout(() => el.remove(), 400);
  }, 3500);
}

// ===== PAGES =====
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
function hideError(id) { document.getElementById(id)?.classList.add('hidden'); }

function fillDemo(email, pass) {
  document.getElementById('login-email').value = email;
  document.getElementById('login-password').value = pass;
}

function togglePwd(id, btn) {
  const inp = document.getElementById(id);
  inp.type = inp.type === 'password' ? 'text' : 'password';
  btn.textContent = inp.type === 'password' ? '👁' : '🙈';
}

// ===== AUTH =====
async function login(e) {
  e.preventDefault();
  hideError('login-error');
  const btn = document.getElementById('btn-login');
  btn.disabled = true;
  btn.textContent = 'Connexion...';

  const res = await fetch(API + '/auth/login/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: document.getElementById('login-email').value,
      password: document.getElementById('login-password').value
    })
  });
  const data = await res.json();
  btn.disabled = false;
  btn.textContent = 'Se connecter';

  if (!res.ok) {
    showError('login-error', data.detail || 'Email ou mot de passe incorrect.');
    return;
  }

  const meRes = await fetch(API + '/auth/me/', {
    headers: { 'Authorization': `Bearer ${data.access}` }
  });
  const user = await meRes.json();
  setSession({ access: data.access, refresh: data.refresh, user });
  toast(`Bienvenue, ${user.first_name} !`, 'success');
  loadDashboard();
}

async function register(e) {
  e.preventDefault();
  hideError('register-error');
  const res = await fetch(API + '/auth/register/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      first_name: document.getElementById('reg-firstname').value,
      last_name: document.getElementById('reg-lastname').value,
      username: document.getElementById('reg-username').value,
      email: document.getElementById('reg-email').value,
      telephone: document.getElementById('reg-phone').value,
      password: document.getElementById('reg-password').value,
      password2: document.getElementById('reg-password2').value,
    })
  });
  const data = await res.json();
  if (!res.ok) {
    showError('register-error', Object.values(data).flat().join(' '));
    return;
  }
  setSession(data);
  toast('Compte créé avec succès !', 'success');
  loadDashboard();
}

function logout() {
  clearSession();
  toast('Déconnexion réussie.', 'info');
  showPage('auth');
}

// ===== DASHBOARD =====
function loadDashboard() {
  showPage('dashboard');
  const user = getUser();
  const roleLabel = { client: '👤 Client', agent: '🧑‍💼 Agent', admin: '👑 Admin' };
  document.getElementById('nav-user').textContent = `${user.first_name} ${user.last_name}`;
  document.getElementById('nav-badge').textContent = roleLabel[user.role] || user.role;

  ['dash-client', 'dash-agent', 'dash-admin'].forEach(id =>
    document.getElementById(id).classList.add('hidden')
  );

  if (user.role === 'client') loadClientDash();
  else if (user.role === 'agent') loadAgentDash();
  else loadAdminDash();
}

// ===== CLIENT =====
async function loadClientDash() {
  document.getElementById('dash-client').classList.remove('hidden');
  const user = getUser();
  const today = new Date().toLocaleDateString('fr-FR', { weekday:'long', year:'numeric', month:'long', day:'numeric' });

  document.getElementById('client-welcome').textContent = `Bonjour, ${user.first_name} 👋`;
  document.getElementById('client-date').textContent = today;

  const [dashRes, demRes] = await Promise.all([
    apiFetch('/prets/dashboard/'),
    apiFetch('/demandes/' + buildQuery({ statut: document.getElementById('filter-dem-statut')?.value }))
  ]);
  if (!dashRes || !demRes) return;

  const dash = await dashRes.json();
  const demandes = await demRes.json();

  // Stats cards
  document.getElementById('client-stats').innerHTML = `
    <div class="stat-card"><div class="stat-value">${dash.demandes.total}</div><div class="stat-label">Demandes totales</div></div>
    <div class="stat-card warning"><div class="stat-value">${dash.demandes.en_attente}</div><div class="stat-label">En attente</div></div>
    <div class="stat-card success"><div class="stat-value">${dash.prets.actifs}</div><div class="stat-label">Prêt actif</div></div>
    <div class="stat-card"><div class="stat-value">${dash.prets.soldes}</div><div class="stat-label">Prêts soldés</div></div>
  `;

  // Prêt actif avec barre de progression
  const pret = dash.pret_actif;
  const progSection = document.getElementById('client-pret-progress');
  if (pret) {
    progSection.classList.remove('hidden');
    document.getElementById('pret-statut-badge').innerHTML = badge('actif');
    document.getElementById('pret-info-grid').innerHTML = `
      <div class="pret-info-item"><div class="val">${fmt(pret.montant_total)}</div><div class="lbl">Montant total (FCFA)</div></div>
      <div class="pret-info-item"><div class="val">${fmt(pret.mensualite)}</div><div class="lbl">Mensualité (FCFA)</div></div>
      <div class="pret-info-item"><div class="val">${fmt(pret.montant_rembourse)}</div><div class="lbl">Remboursé (FCFA)</div></div>
      <div class="pret-info-item"><div class="val">${fmt(pret.montant_restant)}</div><div class="lbl">Restant (FCFA)</div></div>
      <div class="pret-info-item"><div class="val">${pret.echeances_payees}/${pret.duree_mois}</div><div class="lbl">Échéances payées</div></div>
      <div class="pret-info-item"><div class="val">${fmtDate(pret.date_fin_prevue)}</div><div class="lbl">Date de fin prévue</div></div>
    `;
    document.getElementById('progress-pct').textContent = `${pret.progression_pct}%`;
    document.getElementById('progress-bar').style.width = `${pret.progression_pct}%`;

    if (pret.prochaine_echeance) {
      const p = pret.prochaine_echeance;
      const isRetard = p.statut === 'en_retard';
      document.getElementById('prochaine-box').innerHTML = `
        <div>
          <div class="prochaine-label">Prochaine échéance (${isRetard ? '⚠️ EN RETARD' : '#' + p.numero})</div>
          <div style="font-size:0.8rem;color:#718096;margin-top:2px">Prévue le ${fmtDate(p.date_echeance)}</div>
        </div>
        <div style="display:flex;align-items:center;gap:10px">
          <div class="prochaine-amount">${fmt(p.montant_du)} FCFA</div>
          <button class="btn btn-sm btn-success" onclick="payerEcheance(${p.id})">Payer maintenant</button>
        </div>
      `;
      document.getElementById('prochaine-box').style.display = 'flex';
    }

    document.getElementById('section-echeances').style.display = '';
    loadEcheances(pret.id);
  } else {
    progSection.classList.add('hidden');
    document.getElementById('section-echeances').style.display = 'none';
    document.getElementById('client-echeances').innerHTML = '';
  }

  // Demandes
  if (demandes.length === 0) {
    document.getElementById('client-demandes').innerHTML = `
      <div class="empty">
        <div class="empty-icon">📋</div>
        <p>Aucune demande. Cliquez sur "+ Nouvelle demande" pour commencer.</p>
      </div>`;
  } else {
    document.getElementById('client-demandes').innerHTML = `
      <div class="table-wrap"><table>
        <tr><th>#</th><th>Montant</th><th>Durée</th><th>Mensualité</th><th>Statut</th><th>Soumis le</th><th>Motif refus</th></tr>
        ${demandes.map(d => `
          <tr>
            <td><strong>#${d.id}</strong></td>
            <td><strong>${fmt(d.montant)} FCFA</strong></td>
            <td>${d.duree_mois} mois</td>
            <td>${fmt(d.mensualite_estimee)} FCFA</td>
            <td>${badge(d.statut)}</td>
            <td>${fmtDate(d.date_soumission)}</td>
            <td style="max-width:200px;font-size:0.82rem;color:#e53e3e">${d.motif_refus || '—'}</td>
          </tr>`).join('')}
      </table></div>`;
  }

  // Historique prêts
  const pretsRes = await apiFetch('/prets/');
  const prets = await pretsRes.json();
  const soldes = prets.filter(p => p.statut === 'solde');
  document.getElementById('client-historique').innerHTML = soldes.length === 0
    ? '<div class="empty"><div class="empty-icon">📜</div><p>Aucun prêt soldé.</p></div>'
    : `<div class="table-wrap"><table>
        <tr><th>#</th><th>Montant</th><th>Durée</th><th>Date début</th><th>Date fin</th><th>Statut</th></tr>
        ${soldes.map(p => `
          <tr>
            <td>#${p.id}</td><td>${fmt(p.montant_total)} FCFA</td>
            <td>${p.duree_mois} mois</td>
            <td>${fmtDate(p.date_debut)}</td>
            <td>${fmtDate(p.date_fin_prevue)}</td>
            <td>${badge(p.statut)}</td>
          </tr>`).join('')}
      </table></div>`;
}

async function loadEcheances(pretId) {
  const res = await apiFetch(`/prets/${pretId}/echeances/`);
  const echeances = await res.json();
  const payees = echeances.filter(e => e.statut === 'paye').length;
  document.getElementById('client-echeances').innerHTML = `
    <div class="table-wrap"><table>
      <tr><th>#</th><th>Montant dû</th><th>Date prévue</th><th>Statut</th><th>Payé le</th><th>Action</th></tr>
      ${echeances.map(e => `
        <tr style="${e.statut==='en_retard'?'background:#fff5f5':''}">
          <td><strong>${e.numero}</strong></td>
          <td><strong>${fmt(e.montant_du)} FCFA</strong></td>
          <td>${fmtDate(e.date_echeance)}</td>
          <td>${badge(e.statut)}</td>
          <td>${e.date_paiement ? fmtDate(e.date_paiement) : '—'}</td>
          <td>${e.statut !== 'paye'
            ? `<button class="btn btn-sm btn-success" onclick="payerEcheance(${e.id})">💳 Payer</button>`
            : '<span style="color:#38a169;font-weight:700">✓ Payée</span>'
          }</td>
        </tr>`).join('')}
    </table></div>
    <div style="margin-top:12px;font-size:0.85rem;color:#718096;text-align:right">
      ${payees} / ${echeances.length} échéances payées
    </div>`;
}

async function submitDemande(e) {
  e.preventDefault();
  hideError('dem-error');
  const montant = document.getElementById('dem-montant').value;
  const duree = document.getElementById('dem-duree').value;
  const motif = document.getElementById('dem-motif').value;

  const res = await apiFetch('/demandes/', { method: 'POST', body: JSON.stringify({ montant, duree_mois: parseInt(duree), motif }) });
  const data = await res.json();
  if (!res.ok) {
    showError('dem-error', Object.values(data).flat().join(' '));
    return;
  }
  hideModal('modal-demande');
  toast('Demande soumise avec succès !', 'success');
  loadClientDash();
}

async function payerEcheance(id) {
  if (!confirm('Confirmer le paiement de cette échéance ?')) return;
  const res = await apiFetch(`/prets/echeances/${id}/payer/`, { method: 'POST' });
  const data = await res.json();
  if (!res.ok) { toast(data.detail || 'Erreur lors du paiement.', 'error'); return; }
  toast(data.detail, data.pret_solde ? 'success' : 'success');
  loadClientDash();
}

function printEcheances() {
  const content = document.getElementById('client-echeances').innerHTML;
  const user = getUser();
  document.getElementById('print-area').innerHTML = `
    <h2 style="margin-bottom:8px">MicroCredit — Plan de remboursement</h2>
    <p style="color:#718096;margin-bottom:20px">Client : ${user.first_name} ${user.last_name} — Imprimé le ${new Date().toLocaleDateString('fr-FR')}</p>
    ${content}`;
  document.getElementById('print-area').classList.remove('hidden');
  window.print();
  document.getElementById('print-area').classList.add('hidden');
}

// ===== AGENT =====
async function loadAgentDash() {
  document.getElementById('dash-agent').classList.remove('hidden');
  const user = getUser();
  document.getElementById('agent-welcome').textContent = `Bonjour, ${user.first_name} 👋`;

  const search = document.getElementById('agent-search')?.value || '';
  const statut = document.getElementById('agent-filter-statut')?.value || '';

  const [allDemRes, filteredDemRes, retardRes, pretsRes] = await Promise.all([
    apiFetch('/demandes/'),
    apiFetch('/demandes/' + buildQuery({ statut, search })),
    apiFetch('/prets/echeances/en-retard/'),
    apiFetch('/prets/?statut=actif'),
  ]);
  if (!allDemRes) return;

  const allDemandes = await allDemRes.json();
  const filteredDemandes = await filteredDemRes.json();
  const retards = await retardRes.json();
  const prets = await pretsRes.json();

  const attente = allDemandes.filter(d => d.statut === 'en_attente');

  // Stats
  document.getElementById('agent-stats').innerHTML = `
    <div class="stat-card warning"><div class="stat-value">${attente.length}</div><div class="stat-label">Dossiers en attente</div></div>
    <div class="stat-card success"><div class="stat-value">${allDemandes.filter(d=>d.statut==='approuve').length}</div><div class="stat-label">Approuvés</div></div>
    <div class="stat-card danger"><div class="stat-value">${allDemandes.filter(d=>d.statut==='refuse').length}</div><div class="stat-label">Refusés</div></div>
    <div class="stat-card danger"><div class="stat-value">${retards.length}</div><div class="stat-label">Retards</div></div>
    <div class="stat-card"><div class="stat-value">${prets.length}</div><div class="stat-label">Prêts actifs</div></div>
  `;

  // Dossiers en attente
  const attenteCount = document.getElementById('agent-attente-count');
  attenteCount.textContent = `${attente.length} dossier${attente.length > 1 ? 's' : ''}`;
  renderAgentDemandes('agent-demandes-attente', attente, true);

  // Tous les dossiers filtrés
  renderAgentDemandes('agent-demandes-all', filteredDemandes, false);

  // Retards
  const retardCount = document.getElementById('agent-retard-count');
  retardCount.textContent = `${retards.length} retard${retards.length > 1 ? 's' : ''}`;
  if (retards.length === 0) {
    document.getElementById('agent-retards').innerHTML = '<div class="empty"><div class="empty-icon">✅</div><p>Aucune échéance en retard.</p></div>';
  } else {
    document.getElementById('agent-retards').innerHTML = `
      <div class="table-wrap"><table>
        <tr><th>Prêt #</th><th>Client</th><th>Échéance #</th><th>Montant dû</th><th>Date prévue</th><th>Retard</th></tr>
        ${retards.map(e => {
          const jours = Math.floor((new Date() - new Date(e.date_echeance)) / 86400000);
          return `<tr style="background:#fff5f5">
            <td>#${e.pret}</td>
            <td>—</td>
            <td>${e.numero}</td>
            <td><strong>${fmt(e.montant_du)} FCFA</strong></td>
            <td>${fmtDate(e.date_echeance)}</td>
            <td><span class="badge badge-danger">${jours}j</span></td>
          </tr>`;
        }).join('')}
      </table></div>`;
  }

  // Prêts actifs
  if (prets.length === 0) {
    document.getElementById('agent-prets').innerHTML = '<div class="empty"><div class="empty-icon">💼</div><p>Aucun prêt actif.</p></div>';
  } else {
    document.getElementById('agent-prets').innerHTML = `
      <div class="table-wrap"><table>
        <tr><th>#</th><th>Client</th><th>Montant</th><th>Mensualité</th><th>Progression</th><th>Fin prévue</th></tr>
        ${prets.map(p => `
          <tr>
            <td>#${p.id}</td>
            <td>${p.client_detail?.first_name} ${p.client_detail?.last_name}</td>
            <td>${fmt(p.montant_total)} FCFA</td>
            <td>${fmt(p.mensualite)} FCFA</td>
            <td>
              <div style="display:flex;align-items:center;gap:8px">
                <div style="flex:1;background:#e2e8f0;border-radius:10px;height:8px;overflow:hidden">
                  <div style="width:${Math.round((p.echeances_payees/p.duree_mois)*100)}%;height:100%;background:#38a169;border-radius:10px"></div>
                </div>
                <span style="font-size:0.78rem;color:#718096;white-space:nowrap">${p.echeances_payees}/${p.duree_mois}</span>
              </div>
            </td>
            <td>${fmtDate(p.date_fin_prevue)}</td>
          </tr>`).join('')}
      </table></div>`;
  }
}

function renderAgentDemandes(containerId, demandes, showActions) {
  if (demandes.length === 0) {
    document.getElementById(containerId).innerHTML = '<div class="empty"><div class="empty-icon">📂</div><p>Aucun dossier.</p></div>';
    return;
  }
  document.getElementById(containerId).innerHTML = `
    <div class="table-wrap"><table>
      <tr><th>#</th><th>Client</th><th>Montant</th><th>Durée</th><th>Mensualité</th><th>Statut</th><th>Soumis le</th>${showActions ? '<th>Actions</th>' : ''}</tr>
      ${demandes.map(d => `
        <tr>
          <td><strong>#${d.id}</strong></td>
          <td>
            <div style="font-weight:600">${d.client_detail?.first_name} ${d.client_detail?.last_name}</div>
            <div style="font-size:0.78rem;color:#718096">${d.client_detail?.email}</div>
          </td>
          <td><strong>${fmt(d.montant)} FCFA</strong></td>
          <td>${d.duree_mois} mois</td>
          <td>${fmt(d.mensualite_estimee)} FCFA</td>
          <td>${badge(d.statut)}</td>
          <td>${fmtDate(d.date_soumission)}</td>
          ${showActions ? `
          <td>
            <div style="display:flex;gap:5px">
              <button class="btn btn-sm btn-outline" onclick="voirDemande(${d.id})">👁 Voir</button>
              <button class="btn btn-sm btn-success" onclick="approuver(${d.id})">✓ Approuver</button>
              <button class="btn btn-sm btn-danger" onclick="openRefus(${d.id}, '${d.client_detail?.first_name} ${d.client_detail?.last_name}', ${d.montant}, ${d.duree_mois})">✗ Refuser</button>
            </div>
          </td>` : ''}
        </tr>`).join('')}
    </table></div>`;
}

async function voirDemande(id) {
  const res = await apiFetch(`/demandes/${id}/`);
  const d = await res.json();
  document.getElementById('detail-demande-title').textContent = `Dossier #${d.id}`;
  document.getElementById('detail-demande-body').innerHTML = `
    <div class="detail-grid">
      <div class="detail-item"><div class="d-label">Client</div><div class="d-value">${d.client_detail?.first_name} ${d.client_detail?.last_name}</div></div>
      <div class="detail-item"><div class="d-label">Email</div><div class="d-value">${d.client_detail?.email}</div></div>
      <div class="detail-item"><div class="d-label">Téléphone</div><div class="d-value">${d.client_detail?.telephone || '—'}</div></div>
      <div class="detail-item"><div class="d-label">Montant demandé</div><div class="d-value">${fmt(d.montant)} FCFA</div></div>
      <div class="detail-item"><div class="d-label">Durée</div><div class="d-value">${d.duree_mois} mois</div></div>
      <div class="detail-item"><div class="d-label">Mensualité estimée</div><div class="d-value">${fmt(d.mensualite_estimee)} FCFA</div></div>
      <div class="detail-item"><div class="d-label">Date soumission</div><div class="d-value">${fmtDate(d.date_soumission)}</div></div>
      <div class="detail-item"><div class="d-label">Statut</div><div class="d-value">${badge(d.statut)}</div></div>
    </div>
    <div style="margin-top:16px">
      <div class="d-label" style="font-size:0.78rem;color:#718096;text-transform:uppercase;font-weight:700;margin-bottom:6px">Motif du prêt</div>
      <div style="background:#f7fafc;border-radius:8px;padding:12px;font-size:0.9rem">${d.motif}</div>
    </div>
    ${d.motif_refus ? `<div style="margin-top:12px;background:#fff5f5;border-radius:8px;padding:12px;font-size:0.9rem;color:#e53e3e"><strong>Motif de refus :</strong> ${d.motif_refus}</div>` : ''}
  `;
  const actionsDiv = document.getElementById('detail-demande-actions');
  if (d.statut === 'en_attente') {
    actionsDiv.innerHTML = `
      <button class="btn btn-outline" onclick="hideModal('modal-detail-demande')">Fermer</button>
      <button class="btn btn-success" onclick="hideModal('modal-detail-demande');approuver(${d.id})">✓ Approuver</button>
      <button class="btn btn-danger" onclick="hideModal('modal-detail-demande');openRefus(${d.id},'${d.client_detail?.first_name}',${d.montant},${d.duree_mois})">✗ Refuser</button>
    `;
  } else {
    actionsDiv.innerHTML = `<button class="btn btn-outline" onclick="hideModal('modal-detail-demande')">Fermer</button>`;
  }
  showModal('modal-detail-demande');
}

async function approuver(id) {
  if (!confirm('Approuver cette demande et générer le plan de remboursement ?')) return;
  const res = await apiFetch(`/demandes/${id}/approuver/`, { method: 'POST' });
  const data = await res.json();
  if (!res.ok) { toast(data.detail || 'Erreur.', 'error'); return; }
  toast(data.detail, 'success');
  loadAgentDash();
}

function openRefus(id, nom, montant, duree) {
  document.getElementById('refus-demande-id').value = id;
  document.getElementById('refus-motif').value = '';
  hideError('refus-error');
  document.getElementById('refus-demande-info').innerHTML = `
    <p><strong>Dossier #${id}</strong> — ${nom || ''}</p>
    ${montant ? `<p style="margin-top:4px;color:#718096">${fmt(montant)} FCFA sur ${duree} mois</p>` : ''}
  `;
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
  toast('Demande refusée.', 'warning');
  loadAgentDash();
}

// ===== ADMIN =====
async function loadAdminDash() {
  document.getElementById('dash-admin').classList.remove('hidden');
  const user = getUser();
  document.getElementById('admin-welcome').textContent = `Bonjour, ${user.first_name} 👋`;

  const [statsRes, usersRes, demandesRes] = await Promise.all([
    apiFetch('/auth/admin/stats/'),
    apiFetch('/auth/admin/users/'),
    apiFetch('/demandes/')
  ]);
  if (!statsRes) return;

  const stats = await statsRes.json();
  allUsers = await usersRes.json();
  const demandes = await demandesRes.json();

  // Stats cards
  document.getElementById('admin-stats').innerHTML = `
    <div class="stat-card"><div class="stat-value">${stats.utilisateurs.total}</div><div class="stat-label">Utilisateurs</div></div>
    <div class="stat-card warning"><div class="stat-value">${stats.demandes.en_attente}</div><div class="stat-label">Dossiers en attente</div></div>
    <div class="stat-card success"><div class="stat-value">${stats.prets.actifs}</div><div class="stat-label">Prêts actifs</div></div>
    <div class="stat-card"><div class="stat-value">${fmtK(stats.prets.montant_total_prete)}</div><div class="stat-label">Total prêté (FCFA)</div></div>
    <div class="stat-card danger"><div class="stat-value">${stats.remboursements.echeances_en_retard}</div><div class="stat-label">Retards</div></div>
    <div class="stat-card success"><div class="stat-value">${fmtK(stats.remboursements.montant_rembourse)}</div><div class="stat-label">Remboursé (FCFA)</div></div>
  `;

  // KPI
  const tauxRemb = stats.prets.montant_total_prete > 0
    ? Math.round((stats.remboursements.montant_rembourse / stats.prets.montant_total_prete) * 100)
    : 0;
  const tauxApprob = stats.demandes.total > 0
    ? Math.round((stats.demandes.approuvees / stats.demandes.total) * 100)
    : 0;
  document.getElementById('admin-kpi').innerHTML = `
    <div class="kpi-item"><div class="kpi-val">${tauxRemb}%</div><div class="kpi-lbl">Taux de remboursement</div></div>
    <div class="kpi-item"><div class="kpi-val">${tauxApprob}%</div><div class="kpi-lbl">Taux d'approbation</div></div>
    <div class="kpi-item"><div class="kpi-val">${stats.prets.soldes}</div><div class="kpi-lbl">Prêts soldés</div></div>
    <div class="kpi-item"><div class="kpi-val">${stats.utilisateurs.clients}</div><div class="kpi-lbl">Clients actifs</div></div>
    <div class="kpi-item"><div class="kpi-val">${stats.utilisateurs.agents}</div><div class="kpi-lbl">Agents de crédit</div></div>
    <div class="kpi-item"><div class="kpi-val">${stats.demandes.refusees}</div><div class="kpi-lbl">Demandes refusées</div></div>
  `;

  // Utilisateurs
  renderUsers(allUsers);

  // Tous les dossiers
  document.getElementById('admin-demandes').innerHTML = `
    <div class="table-wrap"><table>
      <tr><th>#</th><th>Client</th><th>Agent</th><th>Montant</th><th>Durée</th><th>Statut</th><th>Date</th></tr>
      ${demandes.map(d => `
        <tr>
          <td>#${d.id}</td>
          <td>${d.client_detail?.first_name} ${d.client_detail?.last_name}</td>
          <td>${d.agent_detail ? d.agent_detail.first_name + ' ' + d.agent_detail.last_name : '—'}</td>
          <td>${fmt(d.montant)} FCFA</td>
          <td>${d.duree_mois} mois</td>
          <td>${badge(d.statut)}</td>
          <td>${fmtDate(d.date_soumission)}</td>
        </tr>`).join('')}
    </table></div>`;
}

function renderUsers(users) {
  const search = document.getElementById('admin-search-user')?.value.toLowerCase() || '';
  const role = document.getElementById('admin-filter-role')?.value || '';
  const filtered = users.filter(u =>
    (!role || u.role === role) &&
    (!search || `${u.first_name} ${u.last_name} ${u.email}`.toLowerCase().includes(search))
  );
  document.getElementById('admin-users').innerHTML = filtered.length === 0
    ? '<div class="empty"><p>Aucun utilisateur trouvé.</p></div>'
    : `<div class="table-wrap"><table>
        <tr><th>#</th><th>Nom complet</th><th>Email</th><th>Rôle</th><th>Téléphone</th><th>Statut</th><th>Inscrit le</th><th>Action</th></tr>
        ${filtered.map(u => `
          <tr>
            <td>#${u.id}</td>
            <td><strong>${u.first_name} ${u.last_name}</strong></td>
            <td><a href="mailto:${u.email}" style="color:#1a56db">${u.email}</a></td>
            <td>${badge(u.role)}</td>
            <td>${u.telephone || '—'}</td>
            <td>${u.is_active ? '<span class="badge badge-success">Actif</span>' : '<span class="badge badge-danger">Inactif</span>'}</td>
            <td>${fmtDate(u.date_joined)}</td>
            <td><button class="btn btn-sm ${u.is_active ? 'btn-danger' : 'btn-success'}" onclick="toggleUser(${u.id}, ${!u.is_active})">${u.is_active ? 'Désactiver' : 'Activer'}</button></td>
          </tr>`).join('')}
      </table></div>`;
}

function filterUsers() { renderUsers(allUsers); }

async function toggleUser(id, activate) {
  if (!confirm(`${activate ? 'Activer' : 'Désactiver'} cet utilisateur ?`)) return;
  const res = await apiFetch(`/auth/admin/users/${id}/`, {
    method: 'PATCH',
    body: JSON.stringify({ is_active: activate })
  });
  if (!res.ok) { toast('Erreur lors de la modification.', 'error'); return; }
  toast(`Utilisateur ${activate ? 'activé' : 'désactivé'}.`, 'success');
  loadAdminDash();
}

async function createUser(e) {
  e.preventDefault();
  hideError('cu-error');
  const res = await apiFetch('/auth/admin/users/', {
    method: 'POST',
    body: JSON.stringify({
      first_name: document.getElementById('cu-firstname').value,
      last_name: document.getElementById('cu-lastname').value,
      username: document.getElementById('cu-username').value,
      email: document.getElementById('cu-email').value,
      telephone: document.getElementById('cu-phone').value,
      role: document.getElementById('cu-role').value,
      password: document.getElementById('cu-password').value,
    })
  });
  const data = await res.json();
  if (!res.ok) { showError('cu-error', Object.values(data).flat().join(' ')); return; }
  hideModal('modal-create-user');
  toast('Utilisateur créé avec succès !', 'success');
  loadAdminDash();
}

// ===== PROFIL =====
function openProfil() {
  const user = getUser();
  document.getElementById('profil-firstname').value = user.first_name;
  document.getElementById('profil-lastname').value = user.last_name;
  document.getElementById('profil-email').value = user.email;
  document.getElementById('profil-phone').value = user.telephone || '';
  document.getElementById('profil-adresse').value = user.adresse || '';
  const initiales = (user.first_name[0] + (user.last_name[0] || '')).toUpperCase();
  document.getElementById('profil-avatar').textContent = initiales;
  hideError('profil-error');
  showModal('modal-profil');
}

document.getElementById('modal-profil')?.addEventListener('click', function(e) {
  if (e.target === this) hideModal('modal-profil');
});

async function updateProfil(e) {
  e.preventDefault();
  hideError('profil-error');
  const res = await apiFetch('/auth/me/', {
    method: 'PATCH',
    body: JSON.stringify({
      first_name: document.getElementById('profil-firstname').value,
      last_name: document.getElementById('profil-lastname').value,
      telephone: document.getElementById('profil-phone').value,
      adresse: document.getElementById('profil-adresse').value,
    })
  });
  const data = await res.json();
  if (!res.ok) { showError('profil-error', Object.values(data).flat().join(' ')); return; }
  // Mettre à jour le user en session
  const user = getUser();
  const updated = { ...user, ...data };
  localStorage.setItem('user', JSON.stringify(updated));
  document.getElementById('nav-user').textContent = `${updated.first_name} ${updated.last_name}`;
  hideModal('modal-profil');
  toast('Profil mis à jour !', 'success');
}

// Remplacer les confirm() par le modal natif — fermer modal en cliquant outside
document.addEventListener('click', e => {
  if (e.target.classList.contains('modal')) hideModal(e.target.id);
});

// ===== HELPERS =====
function badge(statut) {
  const map = {
    en_attente: ['badge-warning', '⏳ En attente'],
    approuve:   ['badge-success', '✓ Approuvée'],
    refuse:     ['badge-danger',  '✗ Refusée'],
    actif:      ['badge-info',    '● Actif'],
    solde:      ['badge-success', '✓ Soldé'],
    paye:       ['badge-success', '✓ Payée'],
    en_retard:  ['badge-danger',  '⚠ Retard'],
    client:     ['badge-gray',    '👤 Client'],
    agent:      ['badge-info',    '🧑‍💼 Agent'],
    admin:      ['badge-warning', '👑 Admin'],
  };
  const [cls, label] = map[statut] || ['badge-gray', statut];
  return `<span class="badge ${cls}">${label}</span>`;
}

function fmt(n) {
  return Number(n).toLocaleString('fr-FR', { maximumFractionDigits: 0 });
}

function fmtK(n) {
  n = Number(n);
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
  if (n >= 1000) return (n / 1000).toFixed(0) + 'K';
  return fmt(n);
}

function fmtDate(d) {
  if (!d) return '—';
  return new Date(d).toLocaleDateString('fr-FR', { day:'2-digit', month:'short', year:'numeric' });
}

function buildQuery(params) {
  const q = Object.entries(params).filter(([,v]) => v).map(([k,v]) => `${k}=${encodeURIComponent(v)}`).join('&');
  return q ? '?' + q : '';
}

function syncDuree(val) {
  document.getElementById('dem-duree').value = val;
  document.getElementById('dem-duree-range').value = val;
  calcMensualite();
}

function calcMensualite() {
  const m = parseFloat(document.getElementById('dem-montant')?.value);
  const d = parseInt(document.getElementById('dem-duree')?.value);
  const box = document.getElementById('dem-mensualite');
  if (!box) return;
  if (m > 0 && d > 0) {
    box.textContent = `Mensualité estimée : ${fmt(m / d)} FCFA / mois — Total : ${fmt(m)} FCFA`;
    box.classList.remove('hidden');
  } else { box.classList.add('hidden'); }
}

document.getElementById('dem-montant')?.addEventListener('input', calcMensualite);
document.getElementById('dem-duree')?.addEventListener('input', calcMensualite);

// Bouton profil dans la navbar
document.querySelector('[onclick="showModal(\'modal-profil\')"]')
  ?.addEventListener('click', openProfil);

// ===== INIT =====
if (getToken() && getUser()) {
  loadDashboard();
}

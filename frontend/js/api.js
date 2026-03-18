/**
 * api.js
 * Utilitários de comunicação com a API BarberFlow.
 * Centraliza todas as chamadas HTTP para facilitar manutenção.
 */

// URL base da API - troque em produção
const API_BASE = window.API_URL || 'https://barberflow-api-0o7n.onrender.com';

// ─────────────────────────────────────────────
// AUTH: Salva e lê dados do usuário logado
// ─────────────────────────────────────────────

const Auth = {
    save(data) {
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('barbershop_id', data.barbershop_id);
        localStorage.setItem('barbershop_name', data.barbershop_name);
        localStorage.setItem('barbershop_slug', data.barbershop_slug);
        localStorage.setItem('user_name', data.user_name);
        localStorage.setItem('is_admin', data.is_admin ? '1' : '0');
        localStorage.setItem('must_change_password', data.must_change_password ? '1' : '0');
    },
    mustChangePassword() { return localStorage.getItem('must_change_password') === '1'; },
    getToken()         { return localStorage.getItem('token'); },
    getBarbershopName(){ return localStorage.getItem('barbershop_name'); },
    getUserName()      { return localStorage.getItem('user_name'); },
    getSlug()          { return localStorage.getItem('barbershop_slug'); },
    isLoggedIn()       { return !!localStorage.getItem('token'); },
    isAdmin()          { return localStorage.getItem('is_admin') === '1'; },
    logout() {
        localStorage.clear();
        window.location.href = '/index.html';
    }
};

// ─────────────────────────────────────────────
// HTTP: Função base para chamadas à API
// ─────────────────────────────────────────────

async function apiRequest(method, endpoint, body = null, requireAuth = true) {
    const headers = { 'Content-Type': 'application/json' };
    
    if (requireAuth) {
        const token = Auth.getToken();
        if (!token) { Auth.logout(); return; }
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    const config = { method, headers };
    if (body) config.body = JSON.stringify(body);
    
    try {
        const res = await fetch(`${API_BASE}${endpoint}`, config);
        
        if (res.status === 401) { Auth.logout(); return; }
        
        // 204 = sem conteúdo (delete/cancel)
        if (res.status === 204) return { ok: true };
        
        const data = await res.json();
        
        if (!res.ok) {
            throw new Error(data.detail || 'Erro desconhecido');
        }
        
        return data;
    } catch (err) {
        throw err;
    }
}

// ─────────────────────────────────────────────
// API ENDPOINTS
// ─────────────────────────────────────────────

const API = {
    // Auth
    login:    (body) => apiRequest('POST', '/auth/login', body, false),
    register: (body) => apiRequest('POST', '/auth/register', body, false),
    
    // Dashboard
    dashboard: (tzOffset) => apiRequest('GET', `/dashboard/${tzOffset !== undefined ? '?tz_offset='+tzOffset : ''}`),
    
    // Barbeiros
    getBarbers:    ()       => apiRequest('GET', '/barbers/'),
    createBarber:  (body)   => apiRequest('POST', '/barbers/', body),
    updateBarber:  (id, b)  => apiRequest('PUT', `/barbers/${id}`, b),
    deleteBarber:  (id)     => apiRequest('DELETE', `/barbers/${id}`),
    
    // Serviços
    getServices:   ()       => apiRequest('GET', '/services/'),
    createService: (body)   => apiRequest('POST', '/services/', body),
    updateService: (id, b)  => apiRequest('PUT', `/services/${id}`, b),
    deleteService: (id)     => apiRequest('DELETE', `/services/${id}`),
    
    // Clientes
    getClients:    (search) => apiRequest('GET', `/clients/${search ? '?search='+search : ''}`),
    createClient:  (body)   => apiRequest('POST', '/clients/', body),
    updateClient:  (id, b)  => apiRequest('PUT', `/clients/${id}`, b),
    deleteClient:  (id)     => apiRequest('DELETE', `/clients/${id}`),
    
    // Agendamentos
    getAppointments: (date, tzOffset) => apiRequest('GET', `/appointments/${date ? '?date_filter='+date+(tzOffset !== undefined ? '&tz_offset='+tzOffset : '') : ''}`),
    createAppointment:(body) => apiRequest('POST', '/appointments/', body),
    updateAppointment:(id,b) => apiRequest('PUT', `/appointments/${id}`, b),
    cancelAppointment:(id)  => apiRequest('DELETE', `/appointments/${id}`),
    togglePayment:    (id)  => apiRequest('PATCH',  `/appointments/${id}/payment`),
    
    // Agenda dos profissionais
    getSchedule:  (barberId)         => apiRequest('GET', `/schedules/${barberId}`),
    saveSchedule: (barberId, body)   => apiRequest('POST', `/schedules/${barberId}`, body),
    getSlots:     (params)           => apiRequest('GET', `/schedules/public/slots?${new URLSearchParams(params)}`, null, false),

    // Senha e Perfil
    getProfile:      ()       => apiRequest('GET',  '/password/profile'),
    updateProfile:   (body)   => apiRequest('PUT',  '/password/profile', body),
    changePassword:  (body)   => apiRequest('POST', '/password/change', body),
    resetPassword:   (body)   => apiRequest('POST', '/password/reset', body, false),
    generateCode:    (email)  => apiRequest('POST', `/password/reset-code/${email}`),
    adminReset:      (body)   => apiRequest('POST', '/password/admin-reset', body),

    // Público (sem auth)
    publicInfo: (slug)      => apiRequest('GET', `/appointments/public/${slug}/info`, null, false),
    publicBook: (slug, body) => apiRequest('POST', `/appointments/public/${slug}/book`, body, false),
};

// ─────────────────────────────────────────────
// UTILITÁRIOS DE UI
// ─────────────────────────────────────────────

function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    const colors = {
        success: 'bg-emerald-500',
        error:   'bg-red-500',
        info:    'bg-amber-500',
    };
    toast.className = `fixed top-5 right-5 z-50 px-5 py-3 rounded-lg text-white font-medium shadow-xl
                       ${colors[type]} transition-all duration-300 translate-y-0 opacity-100`;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => { toast.style.opacity = '0'; setTimeout(() => toast.remove(), 300); }, 3000);
}

function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
}

function formatDate(isoString) {
    return new Date(isoString).toLocaleDateString('pt-BR');
}

function formatDateTime(isoString) {
    return new Date(isoString).toLocaleString('pt-BR', {
        day: '2-digit', month: '2-digit', year: 'numeric',
        hour: '2-digit', minute: '2-digit'
    });
}

function todayISO() {
    return new Date().toISOString().split('T')[0];
}

// Redireciona para login se não estiver autenticado
function requireAuth() {
    if (!Auth.isLoggedIn()) {
        window.location.href = '/index.html';
    }
}

// Preenche o nome da barbearia no header
function fillBarbershopInfo() {
    const nameEl = document.getElementById('barbershop-name');
    const userEl = document.getElementById('user-name');
    if (nameEl) nameEl.textContent = Auth.getBarbershopName() || 'Minha Barbearia';
    if (userEl) userEl.textContent = Auth.getUserName() || '';
}

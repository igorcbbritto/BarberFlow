/**
 * layout.js
 * Sidebar responsiva com menu hambúrguer no mobile.
 */

function initLayout(activePage) {
  requireAuth();

  const nav = [
    { id: 'dashboard',     label: 'Dashboard',    href: 'dashboard.html',    icon: dashboardIcon() },
    { id: 'agendamentos',  label: 'Agenda',        href: 'agendamentos.html', icon: calendarIcon()  },
    { id: 'clientes',      label: 'Clientes',      href: 'clientes.html',     icon: usersIcon()     },
    { id: 'profissionais', label: 'Profissionais', href: 'profissionais.html',icon: personIcon()    },
    { id: 'servicos',      label: 'Serviços',      href: 'servicos.html',     icon: scissorsIcon()  },
  ];

  const navItems = nav.map(item => {
    const isActive = item.id === activePage;
    return `
      <a href="${item.href}" onclick="closeMobileMenu()"
         class="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all
                ${isActive ? 'bg-gold text-dark font-semibold shadow-md' : 'text-gray-400 hover:text-white hover:bg-dark-4'}">
        ${item.icon}
        <span>${item.label}</span>
      </a>`;
  }).join('');

  const slug = Auth.getSlug();
  const publicUrl = `../booking.html?slug=${slug}`;

  document.getElementById('app-layout').innerHTML = `
    <div class="app-container">

      <!-- ── OVERLAY MOBILE ── -->
      <div id="sidebar-overlay" class="sidebar-overlay" onclick="closeMobileMenu()"></div>

      <!-- ── SIDEBAR ── -->
      <aside id="sidebar" class="sidebar">
        <div class="flex items-center gap-3 px-6 py-6 border-b" style="border-color:#1e1e1e;">
          <svg width="28" height="28" viewBox="0 0 36 36" fill="none">
            <circle cx="18" cy="18" r="18" fill="#C9A84C" opacity="0.15"/>
            <path d="M10 10 L20 20 M26 10 L16 20 M14 22 a4 4 0 1 0 4 4 M22 22 a4 4 0 1 0 4 4"
                  stroke="#C9A84C" stroke-width="1.8" stroke-linecap="round"/>
          </svg>
          <span class="font-display text-2xl tracking-widest gold">BARBERFLOW</span>
        </div>

        <div class="px-6 py-4 border-b" style="border-color:#1e1e1e;">
          <p class="text-xs text-gray-500 uppercase tracking-widest mb-0.5">Barbearia</p>
          <p id="barbershop-name" class="text-sm font-semibold text-white truncate">—</p>
        </div>

        <nav class="flex-1 px-3 py-4 space-y-1">${navItems}</nav>

        <div class="px-4 py-4 border-t" style="border-color:#1e1e1e;">
          <a href="${publicUrl}" target="_blank"
             class="flex items-center gap-2 text-xs text-amber-500 hover:text-amber-400 transition-colors">
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/>
            </svg>
            Link de agendamento
          </a>
        </div>

        <div class="px-4 py-4 border-t" style="border-color:#1e1e1e;">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0"
                 style="background:rgba(201,168,76,0.2); color:#C9A84C; font-family:'Bebas Neue',cursive;"
                 id="user-avatar">J</div>
            <div class="flex-1 min-w-0">
              <p id="user-name" class="text-sm font-medium text-white truncate">—</p>
              <p class="text-xs text-gray-500">Administrador</p>
            </div>
            <button onclick="Auth.logout()" title="Sair"
                    class="text-gray-500 hover:text-red-400 transition-colors flex-shrink-0">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
              </svg>
            </button>
          </div>
        </div>
      </aside>

      <!-- ── MAIN ── -->
      <div class="main-wrapper">

        <!-- Header mobile -->
        <header class="mobile-header">
          <button onclick="openMobileMenu()" class="menu-btn">
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
            </svg>
          </button>
          <span class="font-display text-xl tracking-widest gold">BARBERFLOW</span>
          <button onclick="Auth.logout()" class="menu-btn" style="color:#71717a;">
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
            </svg>
          </button>
        </header>

        <main id="page-content" class="page-content"></main>
      </div>

    </div>
  `;

  fillBarbershopInfo();
  const uname = Auth.getUserName() || '';
  const avatar = document.getElementById('user-avatar');
  if (avatar && uname) avatar.textContent = uname.charAt(0).toUpperCase();
}

function openMobileMenu() {
  document.getElementById('sidebar').classList.add('open');
  document.getElementById('sidebar-overlay').classList.add('show');
  document.body.style.overflow = 'hidden';
}

function closeMobileMenu() {
  document.getElementById('sidebar').classList.remove('open');
  document.getElementById('sidebar-overlay').classList.remove('show');
  document.body.style.overflow = '';
}

// ── ÍCONES ──
function dashboardIcon() {
  return `<svg class="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
          d="M4 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1V5zm10 0a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1v-4zm10 0a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z"/>
  </svg>`;
}
function calendarIcon() {
  return `<svg class="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
          d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
  </svg>`;
}
function usersIcon() {
  return `<svg class="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
          d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/>
  </svg>`;
}
function personIcon() {
  return `<svg class="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
          d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
  </svg>`;
}
function scissorsIcon() {
  return `<svg class="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <circle cx="6" cy="6" r="3" stroke-width="2"/>
    <circle cx="6" cy="18" r="3" stroke-width="2"/>
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 4L8.12 15.88M14.47 14.48L20 20M8.12 8.12L12 12"/>
  </svg>`;
}

// ── CSS INJETADO ──
(function injectStyles() {
  const style = document.createElement('style');
  style.textContent = `
    :root {
      --gold: #C9A84C; --gold-light: #E8C97A;
      --dark: #0D0D0D; --dark-2: #111; --dark-3: #161616; --dark-4: #1e1e1e;
      --sidebar-w: 256px;
    }
    * { box-sizing: border-box; }
    body { font-family: 'DM Sans', sans-serif; background: #0D0D0D; color: #e5e5e5; margin: 0; }
    .font-display { font-family: 'Bebas Neue', cursive; }
    .gold { color: var(--gold); }
    .bg-gold { background: var(--gold); }
    .text-dark { color: #0D0D0D; }
    .bg-dark-4 { background: var(--dark-4); }

    /* ── LAYOUT ── */
    .app-container { display: flex; min-height: 100vh; }

    .sidebar {
      width: var(--sidebar-w); flex-shrink: 0;
      display: flex; flex-direction: column;
      position: fixed; inset-y: 0; left: 0; z-index: 40;
      background: #111; border-right: 1px solid #1e1e1e;
      transition: transform 0.25s ease;
    }

    .main-wrapper {
      flex: 1; margin-left: var(--sidebar-w);
      display: flex; flex-direction: column; min-height: 100vh;
    }

    /* Mobile header — escondido no desktop */
    .mobile-header { display: none; }

    /* Overlay mobile */
    .sidebar-overlay {
      display: none; position: fixed; inset: 0;
      background: rgba(0,0,0,0.6); z-index: 39;
      backdrop-filter: blur(2px);
    }
    .sidebar-overlay.show { display: block; }

    /* ── RESPONSIVO ── */
    @media (max-width: 768px) {
      .sidebar {
        transform: translateX(-100%);
      }
      .sidebar.open {
        transform: translateX(0);
        box-shadow: 8px 0 32px rgba(0,0,0,0.5);
      }
      .main-wrapper {
        margin-left: 0;
      }
      .mobile-header {
        display: flex; align-items: center; justify-content: space-between;
        padding: 12px 16px;
        background: #111; border-bottom: 1px solid #1e1e1e;
        position: sticky; top: 0; z-index: 30;
      }
      .menu-btn {
        width: 36px; height: 36px; border-radius: 10px;
        background: #1e1e1e; border: none; cursor: pointer;
        color: #e5e5e5; display: flex; align-items: center; justify-content: center;
        transition: background 0.15s;
      }
      .menu-btn:active { background: #2a2a2a; }
      .page-content { padding: 16px !important; }
    }

    /* ── CONTEÚDO ── */
    .page-content { flex: 1; padding: 32px; }

    /* ── CARDS ── */
    .card { background: #111; border: 1px solid #1e1e1e; border-radius: 16px; }

    /* ── INPUTS ── */
    .input-field {
      background: #1a1a1a; border: 1px solid #2a2a2a; color: #e5e5e5;
      border-radius: 10px; padding: 10px 14px; font-size: 14px; width: 100%;
      transition: border-color 0.2s; font-family: 'DM Sans', sans-serif;
    }
    .input-field:focus { outline: none; border-color: var(--gold); box-shadow: 0 0 0 3px rgba(201,168,76,0.12); }
    .input-field::placeholder { color: #444; }
    select.input-field option { background: #1a1a1a; }

    /* ── BOTÕES ── */
    .btn-gold {
      background: var(--gold); color: #0D0D0D; font-weight: 600;
      border: none; cursor: pointer; transition: all 0.2s;
      border-radius: 10px; padding: 10px 20px; font-size: 14px;
      font-family: 'DM Sans', sans-serif; display: inline-flex; align-items: center;
    }
    .btn-gold:hover { background: var(--gold-light); transform: translateY(-1px); }
    .btn-ghost {
      background: transparent; color: #888; border: 1px solid #2a2a2a;
      cursor: pointer; transition: all 0.2s; border-radius: 10px;
      padding: 10px 16px; font-size: 13px; font-family: 'DM Sans', sans-serif;
    }
    .btn-ghost:hover { border-color: #444; color: #ccc; }

    /* ── BADGES ── */
    .badge-confirmed { background: rgba(16,185,129,0.15); color: #34d399; border: 1px solid rgba(16,185,129,0.2); }
    .badge-pending   { background: rgba(245,158,11,0.15);  color: #fbbf24; border: 1px solid rgba(245,158,11,0.2); }
    .badge-completed { background: rgba(99,102,241,0.15);  color: #a5b4fc; border: 1px solid rgba(99,102,241,0.2); }
    .badge-cancelled { background: rgba(107,114,128,0.15); color: #9ca3af; border: 1px solid rgba(107,114,128,0.2); }

    /* ── MODAL ── */
    .modal-overlay {
      position: fixed; inset: 0; background: rgba(0,0,0,0.75);
      display: none; align-items: center; justify-content: center;
      z-index: 100; padding: 16px; backdrop-filter: blur(4px);
    }
    .modal-overlay.show { display: flex; }
    .modal-box {
      background: #161616; border: 1px solid #2a2a2a; border-radius: 16px;
      padding: 28px; width: 100%; max-width: 480px;
      animation: modalIn 0.2s ease; max-height: 90vh; overflow-y: auto;
    }
    @media (max-width: 768px) {
      .modal-box { padding: 20px; border-radius: 20px 20px 0 0; margin-top: auto; max-height: 85vh; }
      .modal-overlay.show { align-items: flex-end; padding: 0; }
    }
    @keyframes modalIn { from { opacity:0; transform: scale(0.96) translateY(8px); } to { opacity:1; transform: scale(1) translateY(0); } }

    /* ── TABELA ── */
    .table-row { border-bottom: 1px solid #1a1a1a; transition: background 0.15s; }
    .table-row:hover { background: rgba(255,255,255,0.02); }
    .table-row:last-child { border-bottom: none; }

    /* ── ANIMAÇÃO ── */
    .fade-in { animation: fadeIn 0.3s ease; }
    @keyframes fadeIn { from { opacity:0; transform: translateY(6px); } to { opacity:1; transform: translateY(0); } }

    /* ── SCROLLBAR ── */
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-track { background: #111; }
    ::-webkit-scrollbar-thumb { background: #2a2a2a; border-radius: 3px; }

    /* ── MOBILE AJUSTES ── */
    @media (max-width: 768px) {
      .grid-responsive { grid-template-columns: 1fr !important; }
      .hide-mobile { display: none !important; }
      h1.font-display { font-size: 2rem !important; }
      .page-header { flex-direction: column !important; align-items: flex-start !important; gap: 12px !important; }
      .page-header .btn-gold, .page-header .btn-ghost, .page-header a.btn-gold { width: 100% !important; justify-content: center; box-sizing: border-box; }
      .filters-bar { flex-wrap: wrap !important; gap: 8px !important; }
      .filters-bar input[type="date"], .filters-bar select { width: 100% !important; }
      .filters-bar .divider { display: none !important; }
      .table-header-row { display: none !important; }
      .table-row { display: none !important; }
      .table-row-mobile { display: flex !important; flex-direction: column; gap: 6px; padding: 14px 16px !important; border-bottom: 1px solid #1a1a1a; }
      .table-row-mobile:last-child { border-bottom: none; }
      .mobile-row-top { display: flex; justify-content: space-between; align-items: flex-start; }
      .mobile-row-mid { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; margin-top: 2px; }
      .mobile-row-actions { display: flex; gap: 14px; padding-top: 6px; border-top: 1px solid #1e1e1e; margin-top: 4px; }
      .metrics-grid { grid-template-columns: repeat(2, 1fr) !important; }
      .metrics-grid .metric-last { grid-column: span 2; }
      .schedule-day { flex-wrap: wrap !important; }
      .schedule-times { width: 100% !important; padding-left: 28px !important; margin-top: 6px; }
    }
    @media (min-width: 769px) {
      .table-row-mobile { display: none !important; }
    }
  `;
  document.head.appendChild(style);

  const link = document.createElement('link');
  link.rel = 'stylesheet';
  link.href = 'https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500;600&display=swap';
  document.head.appendChild(link);
})();

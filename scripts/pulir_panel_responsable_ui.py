from pathlib import Path
import re

path = Path('mi-cuenta/index.html')
s = path.read_text(encoding='utf-8')


def must_replace(old, new, label):
    global s
    if old not in s:
        raise SystemExit(f'No encontré el bloque esperado: {label}')
    s = s.replace(old, new, 1)


def must_sub(pattern, repl, label):
    global s
    ns, n = re.subn(pattern, repl, s, count=1, flags=re.S)
    if n != 1:
        raise SystemExit(f'No pude reemplazar {label}: coincidencias={n}')
    s = ns

# 1) Header: logo un poco más presente + menú discreto de cuenta.
must_replace(
    '<header><div class="brand"><div class="logo"></div><div>Patas a Casa<div class="small muted">Mi cuenta</div></div></div></header>',
    '<header><div class="brand"><div class="logo"></div><div>Patas a Casa<div class="small muted">Mi cuenta</div></div></div><button id="accountMenuBtn" class="header-menu hidden" type="button" onclick="openAccountMenu()" aria-label="Opciones de cuenta" title="Opciones de cuenta"><span aria-hidden="true">•••</span></button></header>',
    'header de Mi cuenta',
)

# 2) Iconos SVG consistentes, sin depender de emojis del sistema.
needle = 'const esc=(v="")=>String(v??"").replace(/[&<>"\']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",\'"\':"&quot;","\'":"&#039;"}[m]));\n'
icons = r'''const esc=(v="")=>String(v??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]));
function uiIcon(name){
 const icons={
  alert:`<svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M10.3 2.9 1.8 17a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 2.9a2 2 0 0 0-3.4 0Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>`,
  plus:`<svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>`,
  pencil:`<svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>`,
  eye:`<svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/></svg>`,
  image:`<svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="m21 15-5-5L5 21"/></svg>`,
  pin:`<svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M20 10c0 5-8 12-8 12S4 15 4 10a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10" r="2.5"/></svg>`,
  more:`<svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true"><circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/></svg>`,
  users:`<svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
  home:`<svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="m3 11 9-8 9 8"/><path d="M5 10v10h14V10"/><path d="M9 20v-6h6v6"/></svg>`,
  logout:`<svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="m16 17 5-5-5-5"/><path d="M21 12H9"/></svg>`
 };
 return icons[name]||"";
}
'''
must_replace(needle, icons, 'helper de iconos')

# 3) Menú de cuenta: cerrar sesión deja de competir con las acciones principales.
needle = 'async function logout(){const s=getSession();try{if(s?.access_token)await authPost("/logout",{},s.access_token)}catch{}setSession(null);pets=[];currentUser=null;showAuth()}\n'
menu_fn = '''async function logout(){const s=getSession();try{if(s?.access_token)await authPost("/logout",{},s.access_token)}catch{}setSession(null);pets=[];currentUser=null;showAuth()}
function openAccountMenu(){
 openModal(`<div class="sheethead"><div><div class="kicker">MI CUENTA</div><h2>Opciones</h2></div><button class="x" onclick="closeModal()">×</button></div><button class="btn soft wide account-logout" onclick="closeModal();logout()">${uiIcon("logout")} Cerrar sesión</button>`);
}
'''
must_replace(needle, menu_fn, 'menú de cuenta')

# 4) Mostrar/ocultar el menú solo cuando corresponde.
must_replace('function showAuth(message=""){\n const pre=', 'function showAuth(message=""){\n document.getElementById("accountMenuBtn")?.classList.add("hidden");\n const pre=', 'ocultar menú en login')
must_replace('function showActivationProfile(c){\n document.title=', 'function showActivationProfile(c){\n document.getElementById("accountMenuBtn")?.classList.add("hidden");\n document.title=', 'ocultar menú durante alta')

# 5) Tarjeta de mascota: jerarquía clara y herramientas contextuales.
pet_card = r'''function petCard(p){
 const lost=p.status==="perdido";
 const avatar=p.photo_url?`<button type="button" class="avatar pet-photo-btn" onclick="openPetPhoto('${esc(p.public_code)}')" aria-label="Agrandar foto de ${esc(p.name)}"><img src="${esc(p.photo_url)}" alt="Foto de ${esc(p.name)}"></button>`:`<div class="avatar">${p.species==="Gato"?"🐱":"🐶"}</div>`;
 const primary=`<button class="btn ${lost?"green":"red"} pet-primary-action" onclick="toggleLost('${esc(p.public_code)}','${lost?"normal":"perdido"}')">${uiIcon(lost?"home":"alert")}<span>${lost?"Ya volvió a casa":"Marcar como perdido"}</span></button>`;
 const core=`<div class="pet-secondary-grid"><button class="btn quiet" onclick="editPet('${esc(p.public_code)}')">${uiIcon("pencil")}<span>Editar perfil</span></button><a class="btn quiet" href="/?tag=${encodeURIComponent(p.public_code)}" target="_blank" rel="noopener">${uiIcon("eye")}<span>Ver perfil público</span></a></div>`;
 const recoveryTools=lost?`<div class="pet-recovery-grid"><button class="btn recovery" onclick="openFlyer('${esc(p.public_code)}')">${uiIcon("image")}<span>Crear flyer</span></button><button class="btn recovery" onclick="showSightings('${esc(p.public_code)}')">${uiIcon("pin")}<span>Avistamientos</span></button></div>`:`<details class="pet-more"><summary>${uiIcon("more")}<span>Más opciones</span></summary><div class="pet-more-grid"><button class="btn quiet" onclick="openFlyer('${esc(p.public_code)}')">${uiIcon("image")}<span>Crear flyer</span></button><button class="btn quiet" onclick="showSightings('${esc(p.public_code)}')">${uiIcon("pin")}<span>Avistamientos</span></button></div></details>`;
 return `<article class="pet" data-code="${esc(p.public_code)}"><div class="pethead">${avatar}<div class="petidentity"><div class="petname">${esc(p.name)}</div><div class="meta">${esc([p.breed,p.sex,p.age_text].filter(Boolean).join(" · ")||p.species)}</div><span class="pill ${lost?"lost":""}">${lost?"PERDIDO":"● EN CASA"}</span><div class="tag-code">Chapita ${esc(p.public_code)}</div></div></div><div class="pet-actions-v2">${primary}${recoveryTools}${core}</div></article>`;
}
'''
must_sub(r'function petCard\(p\)\{.*?\n\}\nfunction openPetPhoto', pet_card + 'function openPetPhoto', 'petCard')

# 6) Dashboard: una sola acción principal arriba, comunidad neutra y acceso rápido contextual.
dashboard = r'''function renderDashboard(){
 document.getElementById("accountMenuBtn")?.classList.remove("hidden");
 const quickAccess=isStandalone()?"":`<section class="card quick-access-card"><h2>Acceso rápido</h2><p class="muted small">Instalá este panel en tu celular para abrirlo desde un ícono, sin escanear ninguna chapita.</p><button class="btn dark wide" onclick="installApp()">${uiIcon("home")}<span>Añadir Patas a Casa al inicio</span></button></section>`;
 root.innerHTML=`<section class="card account-overview"><div class="topline"><div><div class="kicker">MI CUENTA</div><h1 style="font-size:31px;margin-bottom:6px">Tus mascotas.</h1><div class="account-email">${esc(currentUser?.email||"")}</div></div><button id="installBtn" class="btn primary install ${isStandalone()?"hidden":""}" onclick="installApp()">${uiIcon("home")}<span>Añadir al inicio</span></button></div><button class="btn soft wide add-tag-btn" onclick="openClaim()">${uiIcon("plus")}<span>Agregar chapita</span></button></section>
 <section class="community-card"><a class="community-link" href="/mi-cuenta/perdidas/">${uiIcon("users")}<span>Mascotas perdidas</span><span class="community-arrow" aria-hidden="true">→</span></a></section>
 <section class="card pets-card"><h2>Mis mascotas</h2><div class="pets">${pets.length?pets.map(petCard).join(""):`<div class="empty">Todavía no hay mascotas vinculadas.<br><button class="btn primary" style="margin-top:12px" onclick="openClaim()">${uiIcon("plus")} Agregar mi chapita</button></div>`}</div></section>
 ${quickAccess}
 <div class="small muted" style="text-align:center;padding:8px 4px 2px"><a href="/privacidad.html" style="color:inherit;font-weight:850">Privacidad</a> · <a href="/terminos.html" style="color:inherit;font-weight:850">Condiciones de uso</a></div>`;
}
'''
must_sub(r'function renderDashboard\(\)\{.*?\n\}\nasync function resolveTagCodeByPin', dashboard + 'async function resolveTagCodeByPin', 'renderDashboard')

# 7) CSS de pulido visual: override no destructivo sobre la base actual.
style = r'''
<style id="pac-owner-polish-v1">
.ui-icon{width:20px;height:20px;flex:0 0 20px;fill:none;stroke:currentColor;stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round}
.logo{width:51px!important;height:51px!important;background-size:88px 88px!important;background-position:center -5px!important;border-radius:16px!important}
.brand{gap:12px!important}
.header-menu{appearance:none;border:0;width:44px;height:44px;border-radius:15px;background:rgba(255,253,250,.78);color:#403a34;display:grid;place-items:center;font-weight:950;letter-spacing:2px;box-shadow:0 4px 15px rgba(53,38,25,.045);border:1px solid var(--pac-line);cursor:pointer;backdrop-filter:blur(10px)}
.header-menu:active{transform:scale(.96)}
.account-overview{padding-bottom:16px!important}.add-tag-btn{margin-top:14px;background:#f2ede6!important;color:#2f2a26!important}
.account-logout{justify-content:flex-start!important;padding-left:18px!important;color:#443c36!important}
.community-card{margin-bottom:12px;border:1px solid var(--pac-line);border-radius:20px;background:rgba(255,253,250,.72);box-shadow:0 5px 18px rgba(53,38,25,.035);overflow:hidden}
.community-link{min-height:58px;padding:0 17px;display:flex;align-items:center;gap:11px;color:#2f2b27;text-decoration:none;font-weight:900}.community-link .ui-icon{color:#796f65}.community-arrow{margin-left:auto;color:#9a9087;font-size:20px;font-weight:600}.community-link:active{background:#f7f1e9}
.pets-card{padding:19px!important}.pet{padding:16px!important;box-shadow:0 3px 13px rgba(53,38,25,.035)!important}.petidentity{min-width:0}.petname{margin-bottom:5px}.meta{margin-top:0!important;line-height:1.35}.pill{margin-top:9px!important}.tag-code{font-size:10px;color:#9a928a;margin-top:6px;font-weight:700;letter-spacing:.01em}
.pet-actions-v2{display:grid;gap:9px;margin-top:15px}.pet-primary-action{width:100%;min-height:54px!important;font-size:14px}.pet-primary-action.red{background:#fff0f2!important;color:#ad2d3b!important;border:1px solid #f3cdd3!important;box-shadow:none!important}.pet-primary-action.green{background:#eaf5ee!important;color:#176b45!important;border:1px solid #cde3d5!important;box-shadow:none!important}
.pet-secondary-grid,.pet-recovery-grid,.pet-more-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}.quiet{background:#faf7f2!important;color:#3b3530!important;border:1px solid rgba(58,46,37,.075)!important;box-shadow:none!important}.recovery{background:#f4eee7!important;color:#332e29!important;border:1px solid rgba(58,46,37,.07)!important;box-shadow:none!important}
.pet-more{border-top:1px solid rgba(58,46,37,.07);padding-top:3px}.pet-more summary{list-style:none;min-height:45px;display:flex;align-items:center;justify-content:center;gap:8px;color:#766e66;font-size:12px;font-weight:850;cursor:pointer;border-radius:14px}.pet-more summary::-webkit-details-marker{display:none}.pet-more[open] summary{margin-bottom:7px;color:#49423c}.pet-more summary:active{background:#f8f3ed}
.quick-access-card{padding-top:18px!important}.quick-access-card .dark{background:#292621!important;box-shadow:none!important}
@media(max-width:390px){.logo{width:48px!important;height:48px!important}.pet-secondary-grid,.pet-recovery-grid,.pet-more-grid{grid-template-columns:1fr}.community-link{padding:0 14px}}
</style>
'''
must_replace('</head>\n<body>', style + '</head>\n<body>', 'CSS de pulido')

path.write_text(s, encoding='utf-8')
print('Panel de responsable actualizado:', path)

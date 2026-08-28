from pathlib import Path

path = Path('mi-cuenta/index.html')
s = path.read_text(encoding='utf-8')

old = 'const GOOGLE_PENDING_KEY="pac_google_activation_v1";\nconst GOOGLE_REDIRECT_URL="https://patas-a-casa.vercel.app/mi-cuenta/?google=1";'
new = 'const GOOGLE_PENDING_KEY="pac_google_activation_v1";\nconst INSTALL_PENDING_KEY="pac_install_pending_v1";\nconst IOS_SESSION_BRIDGE_COOKIE="pac_ios_session_bridge";\nconst GOOGLE_REDIRECT_URL="https://patas-a-casa.vercel.app/mi-cuenta/?google=1";'
if old not in s:
    raise SystemExit('No encontré constantes esperadas')
s = s.replace(old, new, 1)

old = 'function getSession(){try{return JSON.parse(localStorage.getItem(SESSION_KEY)||"null")}catch{return null}}\nfunction queueGoogleActivation(publicCode,activationCode){'
new = '''function getSession(){try{return JSON.parse(localStorage.getItem(SESSION_KEY)||"null")}catch{return null}}
function setInstallPending(on){try{on?localStorage.setItem(INSTALL_PENDING_KEY,"1"):localStorage.removeItem(INSTALL_PENDING_KEY)}catch{}}
function installPending(){try{return localStorage.getItem(INSTALL_PENDING_KEY)==="1"}catch{return false}}
function clearIosSessionBridge(){document.cookie=`${IOS_SESSION_BRIDGE_COOKIE}=; Max-Age=0; Path=/mi-cuenta/; SameSite=Lax; Secure`}
function writeIosSessionBridge(){
 if(!isiOS()||isStandalone())return;const s=getSession();if(!s?.access_token||!s?.refresh_token)return;
 const payload=encodeURIComponent(JSON.stringify({access_token:s.access_token,refresh_token:s.refresh_token,expires_in:s.expires_in,expires_at:s.expires_at,token_type:s.token_type||"bearer"}));
 if(payload.length>3600)return;document.cookie=`${IOS_SESSION_BRIDGE_COOKIE}=${payload}; Max-Age=1200; Path=/mi-cuenta/; SameSite=Lax; Secure`;
}
function consumeIosSessionBridge(){
 if(getSession())return false;const match=document.cookie.match(new RegExp(`(?:^|;\\s*)${IOS_SESSION_BRIDGE_COOKIE}=([^;]+)`));if(!match)return false;
 try{const s=JSON.parse(decodeURIComponent(match[1]));if(!s?.access_token||!s?.refresh_token)return false;setSession(s);clearIosSessionBridge();return true}catch{clearIosSessionBridge();return false}
}
function queueGoogleActivation(publicCode,activationCode){'''
if old not in s:
    raise SystemExit('No encontré getSession esperado')
s = s.replace(old, new, 1)

old = 'window.addEventListener("appinstalled",()=>{deferredInstall=null;document.getElementById("installBtn")?.classList.add("hidden");toast("Patas a Casa quedó instalada ✅")});'
new = 'window.addEventListener("appinstalled",()=>{deferredInstall=null;document.getElementById("installBtn")?.classList.add("hidden");if(installPending()){setInstallPending(false);showInstallFinish(true)}else toast("Patas a Casa quedó instalada ✅")});'
if old not in s:
    raise SystemExit('No encontré appinstalled esperado')
s = s.replace(old, new, 1)

marker = 'function showAuth(message=""){'
fn = '''function showInstallFinish(installed=false){
 if(isStandalone()){setInstallPending(false);clearIosSessionBridge();loadDashboard();return}
 setInstallPending(true);if(isiOS())writeIosSessionBridge();
 const ios=isiOS();
 root.innerHTML=`<section class="card hero"><div class="kicker">ÚLTIMO PASO</div><h1>${installed?"Patas a Casa ya está agregada ✅":"Agregá Patas a Casa al inicio."}</h1><p class="muted">Tu cuenta y los datos de tu mascota ya quedaron guardados. Ahora dejá Patas a Casa en la pantalla de inicio para tenerla siempre a mano.</p></section>
 <section class="card">${installed?`<div class="status ok"><b>Instalación completada.</b><br>Buscá el ícono 🐾 de Patas a Casa en tu pantalla de inicio y abrilo desde ahí.</div>`:ios?`<h2>En iPhone</h2><div class="install-steps"><div class="step"><b>1.</b> Asegurate de estar en <b>Safari</b>.</div><div class="step"><b>2.</b> Tocá <b>Compartir</b> (el cuadrado con la flecha hacia arriba).</div><div class="step"><b>3.</b> Elegí <b>Agregar a pantalla de inicio</b> y confirmá.</div><div class="step"><b>4.</b> Cerrá Safari y abrí <b>Patas a Casa</b> desde el nuevo ícono 🐾.</div></div><button class="btn primary wide" style="margin-top:14px" onclick="installApp()">📲 Mostrar cómo agregarla</button><p class="small muted" style="margin-top:12px">Preparamos tu sesión para que al abrir el ícono puedas continuar con tu cuenta.</p>`:`<h2>Instalá Patas a Casa</h2><p class="muted small">Tocá el botón y confirmá <b>Instalar</b> o <b>Añadir a pantalla de inicio</b>.</p><button class="btn primary wide" onclick="installApp()">📲 Agregar Patas a Casa al inicio</button>`}</section>`;
}
'''
if fn.strip() not in s:
    if marker not in s:
        raise SystemExit('No encontré punto para showInstallFinish')
    s = s.replace(marker, fn + marker, 1)

old = 'try{if(photo){button.textContent="Preparando foto…";o.photo_data=await compressPhoto(photo)}button.textContent="Creando mascota…";await accountPost(o);history.replaceState({},document.title,"/mi-cuenta/");await loadDashboard();toast("Mascota creada y vinculada ✅")} '
new = 'try{if(photo){button.textContent="Preparando foto…";o.photo_data=await compressPhoto(photo)}button.textContent="Creando mascota…";await accountPost(o);history.replaceState({},document.title,"/mi-cuenta/");setInstallPending(true);if(isiOS())writeIosSessionBridge();showInstallFinish();toast("Mascota creada y vinculada ✅")} '
if old not in s:
    raise SystemExit('No encontré éxito de complete_activation')
s = s.replace(old, new, 1)

old = 'async function boot(){\n if("serviceWorker" in navigator)navigator.serviceWorker.register("/mi-cuenta/sw.js",{scope:"/mi-cuenta/"}).catch(()=>{});'
new = 'async function boot(){\n if("serviceWorker" in navigator)navigator.serviceWorker.register("/mi-cuenta/sw.js",{scope:"/mi-cuenta/"}).catch(()=>{});\n consumeIosSessionBridge();'
if old not in s:
    raise SystemExit('No encontré inicio de boot')
s = s.replace(old, new, 1)

old = ' history.replaceState({},document.title,"/mi-cuenta/");await loadDashboard();\n}\nboot();'
new = ' history.replaceState({},document.title,"/mi-cuenta/");if(isStandalone()){setInstallPending(false);clearIosSessionBridge()}else if(installPending()){showInstallFinish();return}await loadDashboard();\n}\nboot();'
if old not in s:
    raise SystemExit('No encontré cierre de boot')
s = s.replace(old, new, 1)

path.write_text(s, encoding='utf-8')
print('OK: instalación como paso final + puente iOS aplicados')

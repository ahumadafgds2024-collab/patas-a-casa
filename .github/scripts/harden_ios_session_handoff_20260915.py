from pathlib import Path

html_path = Path("mi-cuenta/index.html")
sw_path = Path("mi-cuenta/sw.js")
html = html_path.read_text(encoding="utf-8")
sw = sw_path.read_text(encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: esperaba 1 coincidencia y encontré {count}")
    return text.replace(old, new, 1)


# 1) Recordar si el usuario ya recorrió la guía de iPhone. Esto permite un escape
# explícito si Safari vuelve a mostrar el onboarding después de haber instalado.
html = replace_once(
    html,
    'const INSTALL_DONE_COOKIE="pac_install_done_v1";\n',
    'const INSTALL_DONE_COOKIE="pac_install_done_v1";\nconst IOS_GUIDE_SEEN_KEY="pac_ios_install_guide_seen_v1";\n',
    "constante guía vista",
)

html = replace_once(
    html,
    'function markInstallDone(){setInstallPending(false);try{document.cookie=`${INSTALL_DONE_COOKIE}=1; Max-Age=31536000; Path=/mi-cuenta/; SameSite=Lax; Secure`}catch{}}\n',
    'function markInstallDone(){setInstallPending(false);try{document.cookie=`${INSTALL_DONE_COOKIE}=1; Max-Age=31536000; Path=/mi-cuenta/; SameSite=Lax; Secure`}catch{}}\n'
    'function iosGuideSeen(){try{return localStorage.getItem(IOS_GUIDE_SEEN_KEY)==="1"}catch{return false}}\n'
    'function setIosGuideSeen(){try{localStorage.setItem(IOS_GUIDE_SEEN_KEY,"1")}catch{}}\n',
    "helpers guía vista",
)

# 2) Puente de sesión más resistente y más chico: transportar sólo el refresh token.
# Si el primer refresh falla (por ejemplo, iPhone sin conexión), la cookie se conserva
# durante una hora y el siguiente arranque puede reintentar.
old_bridge = '''function writeIosSessionBridge(){
 if(!isiOS()||isStandalone())return;const s=getSession();if(!s?.access_token||!s?.refresh_token)return;
 const payload=encodeURIComponent(JSON.stringify({access_token:s.access_token,refresh_token:s.refresh_token,expires_in:s.expires_in,expires_at:s.expires_at,token_type:s.token_type||"bearer"}));
 if(payload.length>3600)return;document.cookie=`${IOS_SESSION_BRIDGE_COOKIE}=${payload}; Max-Age=1200; Path=/mi-cuenta/; SameSite=Lax; Secure`;
}
function consumeIosSessionBridge(){
 if(getSession())return false;const match=document.cookie.match(new RegExp(`(?:^|;\\s*)${IOS_SESSION_BRIDGE_COOKIE}=([^;]+)`));if(!match)return false;
 try{const s=JSON.parse(decodeURIComponent(match[1]));if(!s?.access_token||!s?.refresh_token)return false;setSession(s);clearIosSessionBridge();return true}catch{clearIosSessionBridge();return false}
}
'''
new_bridge = '''function writeIosSessionBridge(){
 if(!isiOS()||isStandalone())return;const s=getSession();if(!s?.refresh_token)return;
 const payload=encodeURIComponent(JSON.stringify({refresh_token:s.refresh_token,token_type:s.token_type||"bearer"}));
 if(payload.length>3000)return;document.cookie=`${IOS_SESSION_BRIDGE_COOKIE}=${payload}; Max-Age=3600; Path=/mi-cuenta/; SameSite=Lax; Secure`;
}
function consumeIosSessionBridge(){
 if(getSession())return false;const match=document.cookie.match(new RegExp(`(?:^|;\\s*)${IOS_SESSION_BRIDGE_COOKIE}=([^;]+)`));if(!match)return false;
 try{const s=JSON.parse(decodeURIComponent(match[1]));if(!s?.refresh_token)return false;setSession({refresh_token:s.refresh_token,expires_at:0,token_type:s.token_type||"bearer"});return true}catch{clearIosSessionBridge();return false}
}
'''
html = replace_once(html, old_bridge, new_bridge, "puente de sesión iOS")

# 3) Al terminar de mirar los cuatro pasos, recordar que la guía ya fue vista y volver
# al onboarding. Si después Safari queda abierto, aparecerá un botón de confirmación.
html = replace_once(
    html,
    'function moveIosGuide(delta){if(iosGuideStep===IOS_INSTALL_GUIDE.length-1&&delta>0){closeModal();return}renderIosGuide(iosGuideStep+delta)}',
    'function moveIosGuide(delta){if(iosGuideStep===IOS_INSTALL_GUIDE.length-1&&delta>0){setIosGuideSeen();closeModal();showInstallFinish();return}renderIosGuide(iosGuideStep+delta)}',
    "fin del carrusel",
)

# 4) Recuperación manual segura para Safari: sólo se ofrece después de haber recorrido
# la guía. Evita que Safari quede atrapado para siempre en el onboarding aunque la PWA
# ya esté funcionando en la pantalla de inicio.
html = replace_once(
    html,
    'function showInstallFinish(installed=false){\n',
    'function confirmIosInstalled(){markInstallDone();clearIosSessionBridge();loadDashboard();toast("Listo. Patas a Casa quedó marcada como agregada ✅")}\nfunction showInstallFinish(installed=false){\n',
    "confirmación manual iOS",
)

html = replace_once(
    html,
    ' const ios=isiOS();\n',
    ' const ios=isiOS();\n const iosDoneButton=ios&&iosGuideSeen()?`<button class="btn soft wide" style="margin-top:10px" type="button" onclick="confirmIosInstalled()">✅ Ya la agregué y abre bien</button>`:"";\n',
    "botón recuperación iOS",
)

html = replace_once(
    html,
    '<p class="small muted" style="margin:9px 0 0;text-align:center">Si estas opciones no coinciden con tu navegador, abrí esta página en <b>Safari</b> y seguí los 4 pasos.</p>',
    '<p class="small muted" style="margin:9px 0 0;text-align:center">Si estas opciones no coinciden con tu navegador, abrí esta página en <b>Safari</b> y seguí los 4 pasos.</p>${iosDoneButton}',
    "insertar recuperación tras guía",
)

# 5) Mensajes de recuperación pueden ser informativos (verde), no siempre errores rojos.
html = replace_once(
    html,
    'function showAuth(message=""){',
    'function showAuth(message="",messageKind="err"){',
    "firma showAuth",
)
html = replace_once(
    html,
    '${message?`<div class="status err">${esc(message)}</div>`:""}',
    '${message?`<div class="status ${messageKind==="ok"?"ok":"err"}">${esc(message)}</div>`:""}',
    "tipo de mensaje auth",
)

# 6) Si una PWA de iPhone se abre sin sesión (iOS viejo, transferencia fallida o sin
# conexión en el primer intento), no mostrar un login genérico como si se hubiera perdido
# todo. Marcar que la app sí está instalada y explicar la recuperación.
html = replace_once(
    html,
    ' const s=await validSession();\n if(!s){\n',
    ' const s=await validSession();\n if(!s){\n  if(isStandalone()&&isiOS()){markInstallDone();showAuth("Patas a Casa ya está instalada ✅. No pudimos recuperar la sesión automáticamente en este intento. Si estabas sin internet, conectate y volvé a abrir; si sigue igual, ingresá una vez con la misma cuenta. Tus mascotas y chapitas guardadas no se perdieron.","ok");return}\n',
    "fallback standalone iOS",
)

# 7) Si el usuario tuvo que ingresar manualmente dentro de la PWA, completar el estado
# de instalación y limpiar cualquier puente temporal sobrante.
html = replace_once(
    html,
    'history.replaceState({},document.title,"/mi-cuenta/");await loadDashboard();if(fin?.linked&&!fin?.already)toast("Correo verificado. Tu mascota ya está vinculada ✅")',
    'history.replaceState({},document.title,"/mi-cuenta/");if(isStandalone()){markInstallDone();clearIosSessionBridge()}await loadDashboard();if(fin?.linked&&!fin?.already)toast("Correo verificado. Tu mascota ya está vinculada ✅")',
    "login manual dentro de PWA",
)

# 8) Nueva versión de cache para que los iPhone instalados reciban el blindaje y sigan
# teniendo las cuatro imágenes disponibles.
sw = replace_once(sw, 'const CACHE="pac-owner-v10";', 'const CACHE="pac-owner-v11";', "cache SW v11")

# Sanity checks críticos.
required = [
    'const IOS_GUIDE_SEEN_KEY="pac_ios_install_guide_seen_v1";',
    'Max-Age=3600; Path=/mi-cuenta/; SameSite=Lax; Secure',
    'setSession({refresh_token:s.refresh_token,expires_at:0',
    '✅ Ya la agregué y abre bien',
    'function showAuth(message="",messageKind="err")',
    'if(isStandalone()&&isiOS()){markInstallDone();showAuth(',
    'pac-owner-v11',
]
for needle in required:
    hay = html if needle != 'pac-owner-v11' else sw
    if needle not in hay:
        raise SystemExit(f"Falta sanity check: {needle}")

for i in range(1, 5):
    asset = f'/mi-cuenta/ios-guia/paso-{i}.jpg'
    if asset not in html or asset not in sw:
        raise SystemExit(f"Falta la imagen iOS {i} en HTML o SW")

html_path.write_text(html, encoding="utf-8")
sw_path.write_text(sw, encoding="utf-8")
print("OK: handoff iPhone, recuperación y carrusel blindados")

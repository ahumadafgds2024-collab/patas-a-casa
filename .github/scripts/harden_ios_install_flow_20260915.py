from pathlib import Path
import re

html_path = Path("mi-cuenta/index.html")
sw_path = Path("mi-cuenta/sw.js")
html = html_path.read_text(encoding="utf-8")
sw = sw_path.read_text(encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: esperaba 1 coincidencia y encontré {count}")
    return text.replace(old, new, 1)

# 1) Estado explícito de instalación completada, compartible entre Safari y la PWA.
html = replace_once(
    html,
    'const IOS_SESSION_BRIDGE_COOKIE="pac_ios_session_bridge";\n',
    'const IOS_SESSION_BRIDGE_COOKIE="pac_ios_session_bridge";\nconst INSTALL_DONE_COOKIE="pac_install_done_v1";\n',
    "constante cookie instalación",
)

html = replace_once(
    html,
    'function installPending(){try{return localStorage.getItem(INSTALL_PENDING_KEY)==="1"}catch{return false}}\n',
    'function installPending(){try{return localStorage.getItem(INSTALL_PENDING_KEY)==="1"}catch{return false}}\n'
    'function installDone(){try{return document.cookie.split(";").some(part=>part.trim()===`${INSTALL_DONE_COOKIE}=1`)}catch{return false}}\n'
    'function markInstallDone(){setInstallPending(false);try{document.cookie=`${INSTALL_DONE_COOKIE}=1; Max-Age=31536000; Path=/mi-cuenta/; SameSite=Lax; Secure`}catch{}}\n',
    "helpers instalación",
)

# 2) El último botón del carrusel no promete una instalación automática que iOS no permite.
html = replace_once(
    html,
    'next.textContent=iosGuideStep===IOS_INSTALL_GUIDE.length-1?"Cerrar y hacerlo ahora":"Siguiente paso →";',
    'next.textContent=iosGuideStep===IOS_INSTALL_GUIDE.length-1?"Listo, voy a agregarla":"Siguiente paso →";',
    "texto final carrusel",
)

# 3) appinstalled marca la instalación como completada.
html = replace_once(
    html,
    'window.addEventListener("appinstalled",()=>{deferredInstall=null;setInstallPending(false);clearIosSessionBridge();toast("Patas a Casa quedó instalada ✅");if(document.getElementById("installOnboarding"))loadDashboard()});',
    'window.addEventListener("appinstalled",()=>{deferredInstall=null;markInstallDone();clearIosSessionBridge();toast("Patas a Casa quedó instalada ✅");if(document.getElementById("installOnboarding"))loadDashboard()});',
    "appinstalled",
)

# 4) En iPhone el onboarding sigue pendiente hasta abrir realmente como app instalada.
html = replace_once(
    html,
    'function showInstallFinish(installed=false){\n if(isStandalone()){setInstallPending(false);clearIosSessionBridge();loadDashboard();return}\n setInstallPending(false);\n if(isiOS())writeIosSessionBridge();',
    'function showInstallFinish(installed=false){\n if(isStandalone()){markInstallDone();clearIosSessionBridge();loadDashboard();return}\n setInstallPending(true);\n if(isiOS())writeIosSessionBridge();',
    "persistencia showInstallFinish",
)

html = replace_once(
    html,
    '<h2>Agregarla en iPhone</h2><p class="muted">Te mostramos exactamente dónde tocar en Safari. Son los mismos cuatro pasos con imágenes que ya tenías.</p><div class="note" style="margin-bottom:12px">Al elegir <b>Agregar a Inicio</b>, dejá activado <b>Abrir como app web</b> antes de tocar Agregar.</div><button class="btn primary wide" onclick="installApp()">📱 Ver los 4 pasos</button><p class="small muted" style="margin:12px 0 0;text-align:center">Después abrí Patas a Casa desde el ícono de la pantalla de inicio para continuar.</p>',
    '<h2>Agregarla en iPhone</h2><p class="muted">Te mostramos exactamente dónde tocar en Safari. Son los mismos cuatro pasos con imágenes que ya tenías.</p><div class="note" style="margin-bottom:12px">Al elegir <b>Agregar a Inicio</b>, dejá activado <b>Abrir como app web</b> antes de tocar Agregar.</div><button class="btn primary wide" onclick="installApp()">📱 Ver los 4 pasos</button><p class="small muted" style="margin:12px 0 0;text-align:center">Después abrí Patas a Casa desde el ícono de la pantalla de inicio para continuar.</p><p class="small muted" style="margin:9px 0 0;text-align:center">Si estas opciones no coinciden con tu navegador, abrí esta página en <b>Safari</b> y seguí los 4 pasos.</p>',
    "ayuda Safari",
)

# 5) Primera mascota: dejar pendiente la instalación. Si el usuario toca atrás, cierra la guía o recarga, vuelve al onboarding.
html = replace_once(
    html,
    'if(hadPetsBefore===false){setInstallPending(false);if(isiOS())writeIosSessionBridge();showInstallFinish();toast("Mascota creada y vinculada ✅");return}',
    'if(hadPetsBefore===false){setInstallPending(true);if(isiOS())writeIosSessionBridge();showInstallFinish();toast("Mascota creada y vinculada ✅");return}',
    "primera mascota pendiente",
)

html = replace_once(
    html,
    'setInstallPending(false);clearIosSessionBridge();await loadDashboard();toast("Mascota creada y vinculada ✅")}',
    'if(installPending()&&!isStandalone()&&!installDone()){if(isiOS())writeIosSessionBridge();showInstallFinish();toast("Mascota creada y vinculada ✅");return}setInstallPending(false);clearIosSessionBridge();await loadDashboard();toast("Mascota creada y vinculada ✅")}',
    "no saltar onboarding pendiente",
)

# 6) Arranque robusto: standalone completa; Safari con onboarding pendiente no puede saltearlo recargando/reabriendo.
html = replace_once(
    html,
    'history.replaceState({},document.title,"/mi-cuenta/");setInstallPending(false);if(isStandalone())clearIosSessionBridge();await loadDashboard();setTimeout(()=>maybeOfferGooglePasswordBackup(),80);',
    'history.replaceState({},document.title,"/mi-cuenta/");if(isStandalone()){markInstallDone();clearIosSessionBridge()}else if(installPending()&&!installDone()){if(isiOS())writeIosSessionBridge();showInstallFinish();return}else if(installDone()){setInstallPending(false)}await loadDashboard();setTimeout(()=>maybeOfferGooglePasswordBackup(),80);',
    "boot instalación",
)

# Sanity checks del carrusel y flujo.
required = [
    'const INSTALL_DONE_COOKIE="pac_install_done_v1";',
    'function markInstallDone()',
    'setInstallPending(true);',
    'Listo, voy a agregarla',
    'abrí esta página en <b>Safari</b>',
    '/mi-cuenta/ios-guia/paso-1.jpg',
    '/mi-cuenta/ios-guia/paso-2.jpg',
    '/mi-cuenta/ios-guia/paso-3.jpg',
    '/mi-cuenta/ios-guia/paso-4.jpg',
]
for needle in required:
    if needle not in html:
        raise SystemExit(f"Falta sanity check: {needle}")
if 'Cerrar y hacerlo ahora' in html:
    raise SystemExit("Quedó el texto final viejo del carrusel")

# Fuerza actualización del service worker para que el iPhone reciba esta revisión y mantenga las 4 imágenes cacheadas.
sw = replace_once(sw, 'const CACHE="pac-owner-v9";', 'const CACHE="pac-owner-v10";', "cache SW v10")
for i in range(1, 5):
    asset = f'/mi-cuenta/ios-guia/paso-{i}.jpg'
    if asset not in sw:
        raise SystemExit(f"El SW no precachea {asset}")

html_path.write_text(html, encoding="utf-8")
sw_path.write_text(sw, encoding="utf-8")
print("OK: flujo iPhone endurecido y carrusel 4/4 preservado")

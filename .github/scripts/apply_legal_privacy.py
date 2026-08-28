from pathlib import Path

VERSION = "2026-08-28"


def patch_once(path, old, new, marker):
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if marker in text:
        return False
    if old not in text:
        raise SystemExit(f"No encontré el punto de inserción {marker} en {path}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")
    return True


legal_check_activation = '''     <label class="check"><input id="legalActivation" type="checkbox" required><div><b>Acepto las condiciones de uso y la privacidad</b><div class="small muted">Al crear la cuenta aceptás las <a href="/terminos.html" target="_blank" rel="noopener" style="font-weight:900;color:#171719">Condiciones de uso</a> y consentís el tratamiento de tus datos según la <a href="/privacidad.html" target="_blank" rel="noopener" style="font-weight:900;color:#171719">Política de Privacidad</a>.</div></div></label>\n     <button class="btn primary" id="accountContinue" type="submit">Crear cuenta y verificar correo</button>'''

patch_once(
    "index.html",
    '     <button class="btn primary" id="accountContinue" type="submit">Crear cuenta y verificar correo</button>',
    legal_check_activation,
    'id="legalActivation"',
)

patch_once(
    "index.html",
    ' document.getElementById("googleActivation").addEventListener("click",()=>{\n   sessionStorage.setItem(GOOGLE_PENDING_KEY,JSON.stringify({public_code:c,activation_code:pin,created_at:Date.now()}));',
    ' document.getElementById("googleActivation").addEventListener("click",()=>{\n   if(!document.getElementById("legalActivation")?.checked){toast("Aceptá las condiciones de uso y la Política de Privacidad para continuar.");return}\n   localStorage.setItem("pac_legal_consent",JSON.stringify({version:"'+VERSION+'",accepted_at:new Date().toISOString()}));\n   sessionStorage.setItem(GOOGLE_PENDING_KEY,JSON.stringify({public_code:c,activation_code:pin,created_at:Date.now()}));',
    'pac_legal_consent",JSON.stringify({version:"'+VERSION+'"',
)

patch_once(
    "index.html",
    'try{await registerPost({action:"start_registration",public_code:c,activation_code:pin,email:mail,password});activationComplete(mail)}',
    'try{localStorage.setItem("pac_legal_consent",JSON.stringify({version:"'+VERSION+'",accepted_at:new Date().toISOString()}));await registerPost({action:"start_registration",public_code:c,activation_code:pin,email:mail,password,legal_consent:true,legal_version:"'+VERSION+'"});activationComplete(mail)}',
    'legal_version:"'+VERSION+'"});activationComplete(mail)',
)

legal_check_signup = '''  <label class="check"><input id="legalSignup" type="checkbox" required><div><b>Acepto las condiciones de uso y la privacidad</b><div class="small muted">Al crear la cuenta aceptás las <a href="/terminos.html" target="_blank" rel="noopener" style="font-weight:900;color:#171719">Condiciones de uso</a> y consentís el tratamiento de tus datos según la <a href="/privacidad.html" target="_blank" rel="noopener" style="font-weight:900;color:#171719">Política de Privacidad</a>.</div></div></label>\n  <button class="btn primary wide" type="submit">Crear cuenta y verificar email</button>'''

patch_once(
    "mi-cuenta/index.html",
    '  <button class="btn primary wide" type="submit">Crear cuenta y verificar email</button>',
    legal_check_signup,
    'id="legalSignup"',
)

patch_once(
    "mi-cuenta/index.html",
    ' document.getElementById("googleSignup").addEventListener("click",async e=>{const b=e.currentTarget,bak=b.innerHTML,f=new FormData(sf);b.disabled=true;b.textContent="Abriendo Google…";try{await startGoogleSignIn({public_code:f.get("code"),activation_code:f.get("pin")})}',
    ' document.getElementById("googleSignup").addEventListener("click",async e=>{const b=e.currentTarget,bak=b.innerHTML,f=new FormData(sf);if(!document.getElementById("legalSignup")?.checked){toast("Aceptá las condiciones de uso y la Política de Privacidad para continuar.");return}localStorage.setItem("pac_legal_consent",JSON.stringify({version:"'+VERSION+'",accepted_at:new Date().toISOString()}));b.disabled=true;b.textContent="Abriendo Google…";try{await startGoogleSignIn({public_code:f.get("code"),activation_code:f.get("pin")})}',
    'googleSignup").addEventListener("click",async e=>{const b=e.currentTarget,bak=b.innerHTML,f=new FormData(sf);if(!document.getElementById("legalSignup")',
)

patch_once(
    "mi-cuenta/index.html",
    'await registerPost({action:"start_registration",public_code:tagCode,activation_code:f.get("pin"),email:mail,password:pass},false);',
    'localStorage.setItem("pac_legal_consent",JSON.stringify({version:"'+VERSION+'",accepted_at:new Date().toISOString()}));await registerPost({action:"start_registration",public_code:tagCode,activation_code:f.get("pin"),email:mail,password:pass,legal_consent:true,legal_version:"'+VERSION+'"},false);',
    'password:pass,legal_consent:true,legal_version:"'+VERSION+'"',
)

patch_once(
    "mi-cuenta/index.html",
    '<section class="card"><h2>Acceso rápido</h2><p class="muted small">Instalá este panel en tu celular para abrirlo desde un ícono, sin escanear ninguna chapita.</p><button class="btn dark wide ${isStandalone()?"hidden":""}" onclick="installApp()">📲 Añadir Patas a Casa a mi pantalla de inicio</button></section>`;',
    '<section class="card"><h2>Acceso rápido</h2><p class="muted small">Instalá este panel en tu celular para abrirlo desde un ícono, sin escanear ninguna chapita.</p><button class="btn dark wide ${isStandalone()?"hidden":""}" onclick="installApp()">📲 Añadir Patas a Casa a mi pantalla de inicio</button></section>\n <div class="small muted" style="text-align:center;padding:8px 4px 2px"><a href="/privacidad.html" style="color:inherit;font-weight:850">Privacidad</a> · <a href="/terminos.html" style="color:inherit;font-weight:850">Condiciones de uso</a></div>`;',
    'href="/privacidad.html" style="color:inherit;font-weight:850">Privacidad</a> · <a href="/terminos.html"',
)

privacy = r'''<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#f6f1e9">
<title>Política de Privacidad · Patas a Casa</title>
<style>
:root{--bg:#f6f1e9;--card:#fffdfa;--ink:#181817;--muted:#756e65;--line:rgba(49,39,31,.10);--orange:#ff6a36}*{box-sizing:border-box}body{margin:0;background:linear-gradient(180deg,#faf7f2,var(--bg));color:var(--ink);font-family:Inter,system-ui,-apple-system,"Segoe UI",sans-serif}.wrap{max-width:720px;margin:auto;padding:24px 15px 70px}.top{display:flex;align-items:center;gap:11px;margin-bottom:18px}.logo{width:44px;height:44px;border-radius:50%;background:#181817;color:white;display:grid;place-items:center;font-size:22px}.brand{font-weight:950}.card{background:var(--card);border:1px solid var(--line);border-radius:24px;padding:22px;box-shadow:0 12px 34px rgba(53,38,25,.07)}h1{font-size:34px;line-height:1.03;letter-spacing:-.045em;margin:4px 0 8px}h2{font-size:18px;margin:25px 0 8px}p,li{line-height:1.58}p{margin:8px 0}.muted{color:var(--muted);font-size:13px}ul{padding-left:20px}.back{display:inline-flex;margin-top:18px;text-decoration:none;background:#181817;color:white;padding:12px 15px;border-radius:14px;font-weight:900}.legal-links{text-align:center;margin-top:16px;font-size:12px}.legal-links a{color:inherit}
</style>
</head>
<body><main class="wrap">
<div class="top"><div class="logo">🐾</div><div><div class="brand">Patas a Casa</div><div class="muted">Protección e identificación de mascotas</div></div></div>
<article class="card">
<div class="muted">Última actualización: 28 de agosto de 2026</div>
<h1>Política de Privacidad</h1>
<p>Esta política explica qué información utiliza Patas a Casa, para qué la utiliza y qué opciones tiene cada persona sobre sus datos.</p>
<h2>1. Responsable y contacto</h2>
<p>El responsable del servicio es <strong>Patas a Casa</strong>. Para consultas, acceso, corrección o eliminación de datos podés comunicarte por los canales oficiales de la marca, incluido Instagram <strong>@patas.a.casa</strong>.</p>
<h2>2. Datos que podemos tratar</h2>
<ul><li><strong>Cuenta:</strong> correo electrónico e información técnica necesaria para autenticar y mantener la sesión. Las contraseñas son gestionadas por el sistema de autenticación y no se muestran públicamente.</li><li><strong>Mascota:</strong> nombre, foto, especie, raza, sexo, edad, tamaño, color o señas y demás datos que el responsable decida cargar.</li><li><strong>Contacto:</strong> nombre del responsable, teléfono o WhatsApp y contacto alternativo cuando se complete.</li><li><strong>Salud y cuidados de la mascota:</strong> enfermedades, medicación, alergias, cuidados especiales o información veterinaria que el responsable decida incorporar.</li><li><strong>Modo perdido:</strong> estado de pérdida, zona o lugar informado, fecha/hora y detalles cargados por el responsable.</li></ul>
<h2>3. Para qué usamos los datos</h2>
<p>Los usamos para crear y proteger la cuenta, vincular una chapita con su responsable, mostrar el perfil de la mascota al escanear el QR, facilitar el contacto en caso de hallazgo, administrar el modo perdido y prestar las funciones propias de Patas a Casa.</p>
<h2>4. Qué información puede ser pública</h2>
<p>El perfil asociado al QR está pensado para ser consultado por quien encuentre o escanee la chapita. Por eso, los datos que el responsable configure como visibles pueden mostrarse públicamente. La información de acceso a la cuenta, las credenciales y el PIN privado de activación no forman parte del perfil público.</p>
<p>Antes de cargar datos personales de terceros, el usuario debe contar con autorización para hacerlo.</p>
<h2>5. Fotos y galería</h2>
<p>Cuando elegís una foto, el navegador o el sistema del teléfono abre su selector de archivos. Patas a Casa recibe la imagen que vos seleccionás; no necesita acceso general o permanente a toda tu galería.</p>
<h2>6. Ubicación</h2>
<p>La ubicación se solicita únicamente cuando una función la necesita y después de una acción voluntaria del usuario. Por ejemplo, una persona que encontró una mascota puede elegir compartir su ubicación para preparar un mensaje de WhatsApp. El navegador solicita el permiso correspondiente y la función puede utilizarse sin compartir ubicación.</p>
<h2>7. Proveedores tecnológicos y servicios externos</h2>
<p>Para operar el servicio podemos utilizar proveedores de infraestructura, alojamiento, base de datos, almacenamiento y autenticación, incluyendo <strong>Supabase</strong> y <strong>Vercel</strong>. Si elegís funciones como ingreso con Google, mapas o contacto por WhatsApp, también se aplican las políticas del servicio externo correspondiente. Dependiendo de la infraestructura de esos proveedores, el procesamiento técnico puede involucrar servidores fuera de Argentina.</p>
<h2>8. Conservación y seguridad</h2>
<p>Conservamos los datos mientras sean necesarios para brindar el servicio, mantener la cuenta o cumplir obligaciones aplicables. Aplicamos medidas técnicas y organizativas razonables para reducir accesos no autorizados, pérdida o uso indebido de la información.</p>
<h2>9. Tus derechos</h2>
<p>Podés solicitar acceso, actualización, rectificación o supresión de tus datos personales. También podés modificar la información de la mascota desde las herramientas disponibles en tu cuenta. Si necesitás ejercer un derecho que no esté disponible desde la aplicación, contactanos por los canales indicados arriba.</p>
<p>La Agencia de Acceso a la Información Pública (AAIP) es la autoridad de aplicación de la Ley 25.326 en Argentina y recibe denuncias y reclamos relacionados con protección de datos personales.</p>
<h2>10. Cambios en esta política</h2>
<p>Podemos actualizar esta política cuando cambien las funciones o la forma de tratar información. La fecha de la versión vigente se muestra al comienzo del documento.</p>
<a class="back" href="/mi-cuenta/">← Volver a Patas a Casa</a>
</article><div class="legal-links"><a href="/terminos.html">Condiciones de uso</a></div>
</main></body></html>'''

terms = r'''<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#f6f1e9"><title>Condiciones de uso · Patas a Casa</title>
<style>:root{--bg:#f6f1e9;--card:#fffdfa;--ink:#181817;--muted:#756e65;--line:rgba(49,39,31,.10)}*{box-sizing:border-box}body{margin:0;background:linear-gradient(180deg,#faf7f2,var(--bg));color:var(--ink);font-family:Inter,system-ui,-apple-system,"Segoe UI",sans-serif}.wrap{max-width:720px;margin:auto;padding:24px 15px 70px}.top{display:flex;align-items:center;gap:11px;margin-bottom:18px}.logo{width:44px;height:44px;border-radius:50%;background:#181817;color:white;display:grid;place-items:center;font-size:22px}.brand{font-weight:950}.card{background:var(--card);border:1px solid var(--line);border-radius:24px;padding:22px;box-shadow:0 12px 34px rgba(53,38,25,.07)}h1{font-size:34px;line-height:1.03;letter-spacing:-.045em;margin:4px 0 8px}h2{font-size:18px;margin:25px 0 8px}p,li{line-height:1.58}p{margin:8px 0}.muted{color:var(--muted);font-size:13px}ul{padding-left:20px}.back{display:inline-flex;margin-top:18px;text-decoration:none;background:#181817;color:white;padding:12px 15px;border-radius:14px;font-weight:900}.legal-links{text-align:center;margin-top:16px;font-size:12px}.legal-links a{color:inherit}</style>
</head><body><main class="wrap"><div class="top"><div class="logo">🐾</div><div><div class="brand">Patas a Casa</div><div class="muted">Protección e identificación de mascotas</div></div></div><article class="card"><div class="muted">Última actualización: 28 de agosto de 2026</div><h1>Condiciones de uso</h1>
<p>Estas condiciones regulan el uso de Patas a Casa y de los perfiles digitales asociados a sus chapitas QR.</p>
<h2>1. Finalidad del servicio</h2><p>Patas a Casa facilita la identificación de mascotas, el acceso a información cargada por su responsable y el contacto en caso de hallazgo o pérdida. Es una herramienta complementaria de identificación y comunicación.</p>
<h2>2. No garantiza la recuperación de una mascota</h2><p>El servicio no puede garantizar que una mascota perdida sea encontrada, que una persona escanee la chapita o que los datos de contacto estén disponibles. El responsable debe mantener actualizada la información y utilizar, cuando corresponda, otras medidas de identificación y búsqueda.</p>
<h2>3. Cuenta, QR y PIN</h2><p>El usuario es responsable de proteger sus credenciales y el PIN privado de activación. El QR público puede ser escaneado por terceros; el PIN no debe publicarse ni compartirse salvo cuando sea necesario para una gestión autorizada.</p>
<h2>4. Información cargada</h2><p>El usuario debe cargar información verdadera y pertinente y contar con autorización para publicar datos de contacto de otras personas. No debe utilizar Patas a Casa para suplantar identidades, acosar, engañar, cometer fraude ni cargar contenido ilícito.</p>
<h2>5. Información pública del perfil</h2><p>Los datos configurados para mostrarse en el perfil de la mascota pueden ser vistos por cualquier persona que acceda al QR o al enlace correspondiente. El usuario decide qué información cargar y debe evitar publicar información que no sea necesaria para identificar o asistir a la mascota.</p>
<h2>6. Disponibilidad y cambios</h2><p>Procuramos mantener el servicio disponible y seguro, pero pueden existir interrupciones por mantenimiento, conectividad, proveedores externos o causas técnicas. Las funciones pueden ajustarse o actualizarse para mejorar seguridad, compatibilidad o funcionamiento.</p>
<h2>7. Servicios de terceros</h2><p>Algunas funciones pueden abrir o utilizar servicios externos, como Google o WhatsApp. El uso de esos servicios se rige también por sus propias condiciones y políticas.</p>
<h2>8. Privacidad</h2><p>El tratamiento de datos personales se explica en la <a href="/privacidad.html">Política de Privacidad</a>, que forma parte de estas condiciones.</p>
<h2>9. Legislación aplicable y contacto</h2><p>Estas condiciones se interpretan de acuerdo con la legislación aplicable de la República Argentina. Para consultas sobre el servicio podés utilizar los canales oficiales de Patas a Casa, incluido Instagram <strong>@patas.a.casa</strong>.</p>
<h2>10. Modificaciones</h2><p>Podemos actualizar estas condiciones cuando cambien las funciones o sea necesario aclarar reglas de uso. La versión vigente muestra su fecha de actualización al comienzo.</p>
<a class="back" href="/mi-cuenta/">← Volver a Patas a Casa</a></article><div class="legal-links"><a href="/privacidad.html">Política de Privacidad</a></div></main></body></html>'''

Path("privacidad.html").write_text(privacy, encoding="utf-8")
Path("terminos.html").write_text(terms, encoding="utf-8")

print("Privacidad y condiciones preparadas.")

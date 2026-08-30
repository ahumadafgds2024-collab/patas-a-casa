from pathlib import Path
import re
import subprocess
import tempfile


def replace_once_if_present(text, old, new):
    if old in text:
        return text.replace(old, new, 1)
    return text


def validate_inline_js(html, label):
    scripts = re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', html, flags=re.S | re.I)
    for i, js in enumerate(scripts, 1):
        if not js.strip():
            continue
        with tempfile.NamedTemporaryFile('w', suffix='.js', encoding='utf-8', delete=False) as f:
            f.write(js)
            name = f.name
        result = subprocess.run(['node', '--check', name], capture_output=True, text=True)
        if result.returncode != 0:
            raise SystemExit(f'JavaScript inválido en {label}, script {i}:\n{result.stderr}')


# ---------- Activación pública ----------
home_path = Path('index.html')
home = home_path.read_text(encoding='utf-8')

# Copy limpio para el lote nuevo.
home = home.replace('Etiqueta ya activada (Modo Demo)', 'Etiqueta ya activada')
home = home.replace('Activación de prueba:', 'Activación de esta chapita:')
home = replace_once_if_present(
    home,
    '<div class="kicker">SEGURIDAD DE LA CUENTA</div>\n   <h1>Configurá tu acceso.</h1>',
    '<div class="kicker">ACTIVAR CHAPITA</div>\n   <h1>Activá tu chapita.</h1>'
)
home = replace_once_if_present(
    home,
    '${emailMode?"No necesitás un PIN. Verificamos tu correo para vincular esta chapita de forma segura.":"Antes de crear el perfil, elegí el correo y la contraseña con los que vas a administrarlo."}',
    '${emailMode?"Creá una cuenta o ingresá con la que ya tenés. Después vas a cargar los datos de tu mascota.":"Antes de crear el perfil, elegí el correo y la contraseña con los que vas a administrarlo."}'
)
home = replace_once_if_present(
    home,
    '<div class="note" style="margin-bottom:14px"><b>Chapita ${esc(c)} ${emailMode?"lista para vincular":"verificada"} ✅</b><br>${emailMode?"El QR de esta chapita reemplaza al PIN impreso.":"No tenés que ingresar el código ni el PIN otra vez."}</div>',
    '<div class="note" style="margin-bottom:14px">${emailMode?`<b>Tu chapita está lista ✅</b><br>Creá una cuenta o ingresá a la que ya tenés para continuar.`:`<b>Chapita ${esc(c)} verificada ✅</b><br>No tenés que ingresar el código ni el PIN otra vez.`}</div>'
)

# En iPhone/iPad Google no se muestra: se elimina del DOM por completo.
old_google_settings = ' fetch(SUPABASE_URL+"/auth/v1/settings",{headers:{apikey:PUBLISHABLE_KEY}}).then(r=>r.ok?r.json():null).then(settings=>{if(settings?.external?.google)document.getElementById("googleActivationOptions")?.classList.remove("hidden")}).catch(()=>{});'
new_google_settings = ' const activationIsiOS=/iphone|ipad|ipod/i.test(navigator.userAgent)||(navigator.platform==="MacIntel"&&navigator.maxTouchPoints>1);\n if(activationIsiOS){document.getElementById("googleActivationOptions")?.remove()}else{fetch(SUPABASE_URL+"/auth/v1/settings",{headers:{apikey:PUBLISHABLE_KEY}}).then(r=>r.ok?r.json():null).then(settings=>{if(settings?.external?.google)document.getElementById("googleActivationOptions")?.classList.remove("hidden")}).catch(()=>{})}'
if old_google_settings in home:
    home = home.replace(old_google_settings, new_google_settings, 1)
elif 'const activationIsiOS=' not in home:
    raise SystemExit('No pude ubicar el bloque Google de la activación pública.')

home = replace_once_if_present(
    home,
    ' document.getElementById("googleActivation").addEventListener("click",()=>{',
    ' document.getElementById("googleActivation")?.addEventListener("click",()=>{'
)

# ---------- Mi cuenta ----------
account_path = Path('mi-cuenta/index.html')
account = account_path.read_text(encoding='utf-8')

if 'const SECURITY_API=' not in account:
    marker = 'const ACCOUNT_API=SUPABASE_URL+"/functions/v1/patas-account";'
    if marker not in account:
        raise SystemExit('No pude ubicar ACCOUNT_API.')
    account = account.replace(marker, marker + '\nconst SECURITY_API=SUPABASE_URL+"/functions/v1/patas-account-security";', 1)

old_reveal = '''async function revealGoogleOptions(){
 try{const r=await fetch(AUTH+"/settings",{headers:{apikey:PUBLISHABLE_KEY}}),settings=r.ok?await r.json():null;if(settings?.external?.google)document.querySelectorAll("[data-google-options]").forEach(el=>el.classList.remove("hidden"))}catch{}
}'''
new_reveal = '''async function revealGoogleOptions(){
 if(isiOS()){document.querySelectorAll("[data-google-options]").forEach(el=>el.remove());return}
 try{const r=await fetch(AUTH+"/settings",{headers:{apikey:PUBLISHABLE_KEY}}),settings=r.ok?await r.json():null;if(settings?.external?.google)document.querySelectorAll("[data-google-options]").forEach(el=>el.classList.remove("hidden"))}catch{}
}'''
if old_reveal in account:
    account = account.replace(old_reveal, new_reveal, 1)
elif 'if(isiOS()){document.querySelectorAll("[data-google-options]").forEach(el=>el.remove());return}' not in account:
    raise SystemExit('No pude ubicar revealGoogleOptions().')

# Al eliminar los botones de Google en iPhone, estos listeners deben tolerar que no existan.
account = replace_once_if_present(account, ' document.getElementById("googleLogin").addEventListener(', ' document.getElementById("googleLogin")?.addEventListener(')
account = replace_once_if_present(account, ' document.getElementById("googleSignup").addEventListener(', ' document.getElementById("googleSignup")?.addEventListener(')

# Helper autenticado para seguridad de cuenta.
if 'async function securityPost(' not in account:
    account_post = 'async function accountPost(data,requiresAuth=true){let s=requiresAuth?await validSession():null;const h={"Content-Type":"application/json","apikey":PUBLISHABLE_KEY};if(s?.access_token)h.Authorization="Bearer "+s.access_token;const r=await fetch(ACCOUNT_API,{method:"POST",headers:h,body:JSON.stringify(data)});const j=await r.json().catch(()=>({}));if(r.status===401&&requiresAuth){setSession(null);showAuth("Tu sesión venció. Volvé a ingresar.");throw new Error("Sesión vencida.")}if(!r.ok)throw new Error(j.error||"Ocurrió un error.");return j}'
    if account_post not in account:
        raise SystemExit('No pude ubicar accountPost().')
    security_post = '''async function securityPost(data){let s=await validSession();if(!s)throw new Error("Sesión vencida.");const h={"Content-Type":"application/json","apikey":PUBLISHABLE_KEY,"Authorization":"Bearer "+s.access_token};const r=await fetch(SECURITY_API,{method:"POST",headers:h,body:JSON.stringify(data)});const j=await r.json().catch(()=>({}));if(r.status===401){setSession(null);showAuth("Tu sesión venció. Volvé a ingresar.");throw new Error("Sesión vencida.")}if(!r.ok)throw new Error(j.error||"No pudimos completar esta acción.");return j}'''
    account = account.replace(account_post, account_post + '\n' + security_post, 1)

# Reemplaza el menú mínimo por Seguridad y cuenta.
if 'function openPasswordSettings()' not in account:
    pattern = r'function openAccountMenu\(\)\{\n.*?\n\}\nfunction openModal'
    replacement = '''function openAccountMenu(){
 openModal(`<div class="sheethead"><div><div class="kicker">MI CUENTA</div><h2>Seguridad y cuenta</h2></div><button class="x" onclick="closeModal()">×</button></div><p class="muted small" style="margin-top:-4px">${esc(currentUser?.email||"")}</p><div class="stack" style="display:grid;gap:9px"><button class="btn soft wide" type="button" onclick="openPasswordSettings()">🔐 Crear o cambiar contraseña</button><button class="btn soft wide account-logout" type="button" onclick="closeModal();logout()">${uiIcon("logout")} Cerrar sesión</button></div><div style="height:1px;background:var(--line);margin:18px 0 14px"></div><div class="small muted" style="margin-bottom:8px;font-weight:850">ZONA SENSIBLE</div><button class="btn red wide" type="button" onclick="openDeleteAccount()">🗑️ Eliminar cuenta</button>`);
}
function openPasswordSettings(){
 openModal(`<div class="sheethead"><div><div class="kicker">SEGURIDAD</div><h2>Crear o cambiar contraseña</h2></div><button class="x" onclick="closeModal()">×</button></div><p class="muted small">Esta contraseña es de Patas a Casa. Te permite entrar con tu email aunque hayas creado la cuenta con Google.</p><form id="passwordSettingsForm"><div class="field"><label>Nueva contraseña</label><div class="password-wrap"><input id="newAccountPassword" name="password" type="password" minlength="8" autocomplete="new-password" required><button class="password-toggle" type="button" data-password-toggle="newAccountPassword" aria-label="Mostrar contraseña" aria-pressed="false">👁</button></div><div class="small muted" style="margin-top:6px">Mínimo 8 caracteres.</div></div><div class="field"><label>Repetir contraseña</label><div class="password-wrap"><input id="repeatAccountPassword" name="repeat" type="password" minlength="8" autocomplete="new-password" required><button class="password-toggle" type="button" data-password-toggle="repeatAccountPassword" aria-label="Mostrar contraseña" aria-pressed="false">👁</button></div></div><button class="btn primary wide" type="submit">Guardar contraseña</button><button class="btn soft wide" type="button" style="margin-top:9px" onclick="openAccountMenu()">Cancelar</button></form>`);
 bindPasswordToggles(modal);document.getElementById("passwordSettingsForm").addEventListener("submit",async e=>{e.preventDefault();const f=new FormData(e.currentTarget),password=String(f.get("password")||""),repeat=String(f.get("repeat")||""),b=e.submitter,bak=b.textContent;if(password.length<8){toast("Usá una contraseña de al menos 8 caracteres.");return}if(password!==repeat){toast("Las contraseñas no coinciden.");return}b.disabled=true;b.textContent="Guardando…";try{await securityPost({action:"password",password});closeModal();toast("Contraseña guardada ✅")}catch(err){toast(err.message)}finally{if(document.body.contains(b)){b.disabled=false;b.textContent=bak}}});
}
function openDeleteAccount(){
 openModal(`<div class="sheethead"><div><div class="kicker">ELIMINAR CUENTA</div><h2>¿Querés eliminar tu cuenta?</h2></div><button class="x" onclick="closeModal()">×</button></div><div class="status err" style="margin:0 0 14px"><b>Esta acción es permanente.</b><br>Se eliminan tu cuenta, los perfiles de tus mascotas y sus fotos. Tus chapitas quedan libres para poder activarlas nuevamente.</div><div class="field"><label>Para confirmar, escribí ELIMINAR</label><input id="deleteAccountWord" type="text" autocomplete="off" autocapitalize="characters" placeholder="ELIMINAR"></div><button class="btn soft wide" type="button" onclick="openAccountMenu()">Cancelar</button><button class="btn red wide" id="deleteAccountConfirm" type="button" style="margin-top:9px">Eliminar definitivamente</button>`);
 document.getElementById("deleteAccountConfirm").addEventListener("click",async e=>{const word=String(document.getElementById("deleteAccountWord")?.value||"").trim().toUpperCase();if(word!=="ELIMINAR"){toast("Escribí ELIMINAR para confirmar.");return}const b=e.currentTarget,bak=b.textContent;b.disabled=true;b.textContent="Eliminando…";try{await securityPost({action:"delete_account"});setSession(null);pets=[];currentUser=null;closeModal();showAuth();toast("Tu cuenta fue eliminada ✅")}catch(err){toast(err.message);b.disabled=false;b.textContent=bak}});
}
function openModal'''
    account, n = re.subn(pattern, replacement, account, count=1, flags=re.S)
    if n != 1:
        raise SystemExit(f'No pude reemplazar el menú de cuenta (matches={n}).')

# Copy más natural al terminar una activación.
account = replace_once_if_present(
    account,
    '<div class="kicker">CHAPITA VERIFICADA</div><h1>Creá el perfil de tu mascota.</h1><p class="muted">La chapita ya está validada. Cargá ahora los datos de quien la va a llevar.</p>',
    '<div class="kicker">ÚLTIMO PASO</div><h1>Creá el perfil de tu mascota.</h1><p class="muted">Tu cuenta ya está lista. Cargá los datos de tu mascota para terminar.</p>'
)
account = replace_once_if_present(
    account,
    '<section class="card"><div class="note" style="margin-bottom:14px"><b>Chapita ${esc(c)} verificada ✅</b><br>No necesitás volver a ingresar el código ni el PIN.</div>',
    '<section class="card"><div class="note" style="margin-bottom:14px"><b>Todo listo con la chapita ✅</b><br>Ahora completá los datos de tu mascota.</div>'
)

# Validaciones de resultado.
required_home = ['const activationIsiOS=', 'googleActivation")?.addEventListener', 'Activá tu chapita.']
for item in required_home:
    if item not in home:
        raise SystemExit(f'Falta resultado esperado en index.html: {item}')
required_account = ['const SECURITY_API=', 'async function securityPost(', 'function openPasswordSettings()', 'function openDeleteAccount()', 'googleLogin")?.addEventListener', 'googleSignup")?.addEventListener', 'forEach(el=>el.remove())']
for item in required_account:
    if item not in account:
        raise SystemExit(f'Falta resultado esperado en mi-cuenta/index.html: {item}')

validate_inline_js(home, 'index.html')
validate_inline_js(account, 'mi-cuenta/index.html')

home_path.write_text(home, encoding='utf-8')
account_path.write_text(account, encoding='utf-8')
print('Account security + iPhone auth cleanup applied and validated')

from pathlib import Path
import re


def replace_once(text, old, new, label):
    if old not in text:
        raise SystemExit(f"Missing expected text for {label}")
    return text.replace(old, new, 1)


def regex_once(text, pattern, repl, label):
    out, n = re.subn(pattern, repl, text, count=1, flags=re.S)
    if n != 1:
        raise SystemExit(f"Expected one match for {label}, got {n}")
    return out

# Public activation page
p = Path("index.html")
text = p.read_text(encoding="utf-8")
if "function isiOS()" not in text:
    text = regex_once(
        text,
        r"(const code=\(params\.get\('tag'\).*?\.toUpperCase\(\);\n\n)(function esc)",
        r"\1function isiOS(){return /iphone|ipad|ipod/i.test(navigator.userAgent)||(navigator.platform===\"MacIntel\"&&navigator.maxTouchPoints>1)}\n\2",
        "public iOS detector",
    )
text = replace_once(
    text,
    'then(settings=>{if(settings?.external?.google)document.getElementById("googleActivationOptions")?.classList.remove("hidden")})',
    'then(settings=>{if(!isiOS()&&settings?.external?.google)document.getElementById("googleActivationOptions")?.classList.remove("hidden")})',
    "hide activation Google on iPhone",
)
text = replace_once(text, '<div class="kicker">SEGURIDAD DE LA CUENTA</div>\n   <h1>Configurá tu acceso.</h1>', '<div class="kicker">ACTIVAR CHAPITA</div>\n   <h1>Activá tu chapita.</h1>', "activation heading")
text = replace_once(
    text,
    '${emailMode?"No necesitás un PIN. Verificamos tu correo para vincular esta chapita de forma segura.":"Antes de crear el perfil, elegí el correo y la contraseña con los que vas a administrarlo."}',
    '${emailMode?"Creá una cuenta o ingresá con la que ya tenés. Después vas a cargar los datos de tu mascota.":"Antes de crear el perfil, elegí el correo y la contraseña con los que vas a administrarlo."}',
    "activation intro copy",
)
text = replace_once(
    text,
    '<div class="note" style="margin-bottom:14px"><b>Chapita ${esc(c)} ${emailMode?"lista para vincular":"verificada"} ✅</b><br>${emailMode?"El QR de esta chapita reemplaza al PIN impreso.":"No tenés que ingresar el código ni el PIN otra vez."}</div>',
    '<div class="note" style="margin-bottom:14px">${emailMode?`<b>Tu chapita está lista ✅</b><br>Creá una cuenta o ingresá a la que ya tenés para continuar.`:`<b>Chapita ${esc(c)} verificada ✅</b><br>No tenés que ingresar el código ni el PIN otra vez.`}</div>',
    "activation note copy",
)
p.write_text(text, encoding="utf-8")

# Owner account page
p = Path("mi-cuenta/index.html")
text = p.read_text(encoding="utf-8")
text = replace_once(
    text,
    'const ACCOUNT_API=SUPABASE_URL+"/functions/v1/patas-account";',
    'const ACCOUNT_API=SUPABASE_URL+"/functions/v1/patas-account";\nconst SECURITY_API=SUPABASE_URL+"/functions/v1/patas-account-security";',
    "security API constant",
)
text = replace_once(
    text,
    'async function revealGoogleOptions(){\n try{const r=await fetch(AUTH+"/settings",{headers:{apikey:PUBLISHABLE_KEY}}),settings=r.ok?await r.json():null;if(settings?.external?.google)document.querySelectorAll("[data-google-options]").forEach(el=>el.classList.remove("hidden"))}catch{}\n}',
    'async function revealGoogleOptions(){\n if(isiOS())return;\n try{const r=await fetch(AUTH+"/settings",{headers:{apikey:PUBLISHABLE_KEY}}),settings=r.ok?await r.json():null;if(settings?.external?.google)document.querySelectorAll("[data-google-options]").forEach(el=>el.classList.remove("hidden"))}catch{}\n}',
    "hide account Google on iPhone",
)
needle = 'async function accountPost(data,requiresAuth=true){let s=requiresAuth?await validSession():null;const h={"Content-Type":"application/json","apikey":PUBLISHABLE_KEY};if(s?.access_token)h.Authorization="Bearer "+s.access_token;const r=await fetch(ACCOUNT_API,{method:"POST",headers:h,body:JSON.stringify(data)});const j=await r.json().catch(()=>({}));if(r.status===401&&requiresAuth){setSession(null);showAuth("Tu sesión venció. Volvé a ingresar.");throw new Error("Sesión vencida.")}if(!r.ok)throw new Error(j.error||"Ocurrió un error.");return j}\n'
addition = needle + '''async function securityPost(data){let s=await validSession();if(!s)throw new Error("Sesión vencida.");const h={"Content-Type":"application/json","apikey":PUBLISHABLE_KEY,"Authorization":"Bearer "+s.access_token};const r=await fetch(SECURITY_API,{method:"POST",headers:h,body:JSON.stringify(data)});const j=await r.json().catch(()=>({}));if(r.status===401){setSession(null);showAuth("Tu sesión venció. Volvé a ingresar.");throw new Error("Sesión vencida.")}if(!r.ok)throw new Error(j.error||"No pudimos completar esta acción.");return j}\nasync function updateAccountPassword(password){let s=await validSession();if(!s)throw new Error("Sesión vencida.");const r=await fetch(AUTH+"/user",{method:"PUT",headers:{"Content-Type":"application/json","apikey":PUBLISHABLE_KEY,"Authorization":"Bearer "+s.access_token},body:JSON.stringify({password})});const j=await r.json().catch(()=>({}));if(r.status===401){setSession(null);showAuth("Tu sesión venció. Volvé a ingresar.");throw new Error("Sesión vencida.")}if(!r.ok)throw new Error(j.msg||j.message||j.error_description||"No pudimos guardar la contraseña.");return j}\n'''
text = replace_once(text, needle, addition, "security helpers")
text = regex_once(
    text,
    r'function openAccountMenu\(\)\{\n.*?\n\}\nfunction openModal',
    '''function openAccountMenu(){
 openModal(`<div class="sheethead"><div><div class="kicker">MI CUENTA</div><h2>Seguridad y cuenta</h2></div><button class="x" onclick="closeModal()">×</button></div><p class="muted small" style="margin-top:-4px">${esc(currentUser?.email||"")}</p><div class="stack" style="display:grid;gap:9px"><button class="btn soft wide" type="button" onclick="openPasswordSettings()">🔐 Crear o cambiar contraseña</button><button class="btn soft wide account-logout" type="button" onclick="closeModal();logout()">${uiIcon("logout")} Cerrar sesión</button></div><div style="height:1px;background:var(--line);margin:18px 0 14px"></div><div class="small muted" style="margin-bottom:8px;font-weight:850">ZONA SENSIBLE</div><button class="btn red wide" type="button" onclick="openDeleteAccount()">🗑️ Borrar cuenta</button>`);
}
function openPasswordSettings(){
 openModal(`<div class="sheethead"><div><div class="kicker">SEGURIDAD</div><h2>Crear o cambiar contraseña</h2></div><button class="x" onclick="closeModal()">×</button></div><p class="muted small">Esta contraseña te permite entrar con tu email, incluso si originalmente creaste la cuenta con Google.</p><form id="passwordSettingsForm"><div class="field"><label>Nueva contraseña</label><div class="password-wrap"><input id="newAccountPassword" name="password" type="password" minlength="8" autocomplete="new-password" required><button class="password-toggle" type="button" data-password-toggle="newAccountPassword" aria-label="Mostrar contraseña" aria-pressed="false">👁</button></div><div class="small muted" style="margin-top:6px">Mínimo 8 caracteres.</div></div><div class="field"><label>Repetir contraseña</label><div class="password-wrap"><input id="repeatAccountPassword" name="repeat" type="password" minlength="8" autocomplete="new-password" required><button class="password-toggle" type="button" data-password-toggle="repeatAccountPassword" aria-label="Mostrar contraseña" aria-pressed="false">👁</button></div></div><button class="btn primary wide" type="submit">Guardar contraseña</button></form>`);
 bindPasswordToggles(modal);document.getElementById("passwordSettingsForm").addEventListener("submit",async e=>{e.preventDefault();const f=new FormData(e.currentTarget),password=String(f.get("password")||""),repeat=String(f.get("repeat")||""),b=e.submitter,bak=b.textContent;if(password.length<8){toast("Usá una contraseña de al menos 8 caracteres.");return}if(password!==repeat){toast("Las contraseñas no coinciden.");return}b.disabled=true;b.textContent="Guardando…";try{await updateAccountPassword(password);closeModal();toast("Contraseña guardada ✅")}catch(err){toast(err.message)}finally{if(document.body.contains(b)){b.disabled=false;b.textContent=bak}}});
}
function openDeleteAccount(){
 openModal(`<div class="sheethead"><div><div class="kicker">BORRAR CUENTA</div><h2>¿Querés eliminar tu cuenta?</h2></div><button class="x" onclick="closeModal()">×</button></div><div class="status err" style="margin:0 0 14px"><b>Esta acción es permanente.</b><br>Se eliminan tu cuenta, los perfiles de tus mascotas y sus fotos. Tus chapitas quedan libres para poder activarlas nuevamente.</div><button class="btn soft wide" type="button" onclick="openAccountMenu()">Cancelar</button><button class="btn red wide" id="deleteAccountConfirm" type="button" style="margin-top:9px">Sí, borrar mi cuenta</button>`);
 document.getElementById("deleteAccountConfirm").addEventListener("click",async e=>{const b=e.currentTarget,bak=b.textContent;b.disabled=true;b.textContent="Eliminando…";try{await securityPost({action:"delete_account"});setSession(null);pets=[];currentUser=null;closeModal();showAuth();toast("Tu cuenta fue eliminada ✅")}catch(err){toast(err.message);b.disabled=false;b.textContent=bak}});
}
function openModal''',
    "account security menu",
)
text = replace_once(text, '<div class="kicker">CHAPITA VERIFICADA</div><h1>Creá el perfil de tu mascota.</h1><p class="muted">La chapita ya está validada. Cargá ahora los datos de quien la va a llevar.</p>', '<div class="kicker">ÚLTIMO PASO</div><h1>Creá el perfil de tu mascota.</h1><p class="muted">Tu cuenta ya está lista. Cargá los datos de tu mascota para terminar.</p>', "profile heading copy")
text = replace_once(text, '<section class="card"><div class="note" style="margin-bottom:14px"><b>Chapita ${esc(c)} verificada ✅</b><br>No necesitás volver a ingresar el código ni el PIN.</div>', '<section class="card"><div class="note" style="margin-bottom:14px"><b>Todo listo con la chapita ✅</b><br>Ahora completá los datos de tu mascota.</div>', "profile note copy")
p.write_text(text, encoding="utf-8")

print("Account security + iPhone auth cleanup applied")

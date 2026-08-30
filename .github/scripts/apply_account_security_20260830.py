from pathlib import Path
import re
import subprocess
import tempfile


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

path = Path('mi-cuenta/index.html')
html = path.read_text(encoding='utf-8')

# API de seguridad ya desplegada en Supabase para borrado de cuenta.
marker = 'const ACCOUNT_API=SUPABASE_URL+"/functions/v1/patas-account";'
if 'const SECURITY_API=' not in html:
    if marker not in html: raise SystemExit('No encontré ACCOUNT_API')
    html = html.replace(marker, marker+'\nconst SECURITY_API=SUPABASE_URL+"/functions/v1/patas-account-security";', 1)

account_post = 'async function accountPost(data,requiresAuth=true){let s=requiresAuth?await validSession():null;const h={"Content-Type":"application/json","apikey":PUBLISHABLE_KEY};if(s?.access_token)h.Authorization="Bearer "+s.access_token;const r=await fetch(ACCOUNT_API,{method:"POST",headers:h,body:JSON.stringify(data)});const j=await r.json().catch(()=>({}));if(r.status===401&&requiresAuth){setSession(null);showAuth("Tu sesión venció. Volvé a ingresar.");throw new Error("Sesión vencida.")}if(!r.ok)throw new Error(j.error||"Ocurrió un error.");return j}'
if 'async function securityPost(' not in html:
    if account_post not in html: raise SystemExit('No encontré accountPost')
    helpers = '''async function securityPost(data){let s=await validSession();if(!s)throw new Error("Sesión vencida.");const h={"Content-Type":"application/json","apikey":PUBLISHABLE_KEY,"Authorization":"Bearer "+s.access_token};const r=await fetch(SECURITY_API,{method:"POST",headers:h,body:JSON.stringify(data)});const j=await r.json().catch(()=>({}));if(r.status===401){setSession(null);showAuth("Tu sesión venció. Volvé a ingresar.");throw new Error("Sesión vencida.")}if(!r.ok)throw new Error(j.error||"No pudimos completar esta acción.");return j}
async function updateAccountPassword(password){let s=await validSession();if(!s)throw new Error("Sesión vencida.");const r=await fetch(AUTH+"/user",{method:"PUT",headers:{"Content-Type":"application/json",apikey:PUBLISHABLE_KEY,Authorization:"Bearer "+s.access_token},body:JSON.stringify({password})});const j=await r.json().catch(()=>({}));if(r.status===401){setSession(null);showAuth("Tu sesión venció. Volvé a ingresar.");throw new Error("Sesión vencida.")}if(!r.ok)throw new Error(j.msg||j.error_description||j.error||"No pudimos guardar la contraseña.");return j}'''
    html = html.replace(account_post, account_post+'\n'+helpers, 1)

old_menu = '''function openAccountMenu(){
 openModal(`<div class="sheethead"><div><div class="kicker">MI CUENTA</div><h2>Opciones</h2></div><button class="x" onclick="closeModal()">×</button></div><button class="btn soft wide account-logout" onclick="closeModal();logout()">${uiIcon("logout")} Cerrar sesión</button>`);
}'''
new_menu = '''function openAccountMenu(){
 openModal(`<div class="sheethead"><div><div class="kicker">MI CUENTA</div><h2>Seguridad y cuenta</h2></div><button class="x" onclick="closeModal()">×</button></div><p class="muted small" style="margin-top:-4px">${esc(currentUser?.email||"")}</p><div class="stack" style="display:grid;gap:9px"><button class="btn soft wide" type="button" onclick="openPasswordSettings()">🔐 Crear o cambiar contraseña</button><button class="btn soft wide account-logout" type="button" onclick="closeModal();logout()">${uiIcon("logout")} Cerrar sesión</button></div><div style="height:1px;background:var(--line);margin:18px 0 14px"></div><div class="small muted" style="margin-bottom:8px;font-weight:850">ZONA SENSIBLE</div><button class="btn red wide" type="button" onclick="openDeleteAccount()">🗑️ Eliminar cuenta</button>`);
}
function openPasswordSettings(){
 openModal(`<div class="sheethead"><div><div class="kicker">SEGURIDAD</div><h2>Crear o cambiar contraseña</h2></div><button class="x" onclick="closeModal()">×</button></div><p class="muted small">Esta contraseña es de Patas a Casa. Te permite entrar con tu email aunque hayas creado la cuenta con Google.</p><form id="passwordSettingsForm"><div class="field"><label>Nueva contraseña</label><div class="password-wrap"><input id="newAccountPassword" name="password" type="password" minlength="8" autocomplete="new-password" required><button class="password-toggle" type="button" data-password-toggle="newAccountPassword" aria-label="Mostrar contraseña" aria-pressed="false">👁</button></div><div class="small muted" style="margin-top:6px">Mínimo 8 caracteres.</div></div><div class="field"><label>Repetir contraseña</label><div class="password-wrap"><input id="repeatAccountPassword" name="repeat" type="password" minlength="8" autocomplete="new-password" required><button class="password-toggle" type="button" data-password-toggle="repeatAccountPassword" aria-label="Mostrar contraseña" aria-pressed="false">👁</button></div></div><button class="btn primary wide" type="submit">Guardar contraseña</button><button class="btn soft wide" type="button" style="margin-top:9px" onclick="openAccountMenu()">Cancelar</button></form>`);
 bindPasswordToggles(modal);document.getElementById("passwordSettingsForm").addEventListener("submit",async e=>{e.preventDefault();const f=new FormData(e.currentTarget),password=String(f.get("password")||""),repeat=String(f.get("repeat")||""),b=e.submitter,bak=b.textContent;if(password.length<8){toast("Usá una contraseña de al menos 8 caracteres.");return}if(password!==repeat){toast("Las contraseñas no coinciden.");return}b.disabled=true;b.textContent="Guardando…";try{await updateAccountPassword(password);closeModal();toast("Contraseña guardada ✅")}catch(err){toast(err.message)}finally{if(document.body.contains(b)){b.disabled=false;b.textContent=bak}}});
}
function openDeleteAccount(){
 openModal(`<div class="sheethead"><div><div class="kicker">ELIMINAR CUENTA</div><h2>¿Querés eliminar tu cuenta?</h2></div><button class="x" onclick="closeModal()">×</button></div><div class="status err" style="margin:0 0 14px"><b>Esta acción es permanente.</b><br>Se eliminan tu cuenta, los perfiles de tus mascotas y sus fotos. Tus chapitas quedan libres para poder activarlas nuevamente.</div><div class="field"><label>Para confirmar, escribí ELIMINAR</label><input id="deleteAccountWord" type="text" autocomplete="off" autocapitalize="characters" placeholder="ELIMINAR"></div><button class="btn soft wide" type="button" onclick="openAccountMenu()">Cancelar</button><button class="btn red wide" id="deleteAccountConfirm" type="button" style="margin-top:9px">Eliminar definitivamente</button>`);
 document.getElementById("deleteAccountConfirm").addEventListener("click",async e=>{const word=String(document.getElementById("deleteAccountWord")?.value||"").trim().toUpperCase();if(word!=="ELIMINAR"){toast("Escribí ELIMINAR para confirmar.");return}const b=e.currentTarget,bak=b.textContent;b.disabled=true;b.textContent="Eliminando…";try{await securityPost({action:"delete_account"});setSession(null);pets=[];currentUser=null;closeModal();showAuth();toast("Tu cuenta fue eliminada ✅")}catch(err){toast(err.message);b.disabled=false;b.textContent=bak}});
}'''

if old_menu in html:
    html = html.replace(old_menu, new_menu, 1)
elif 'function openPasswordSettings()' not in html:
    raise SystemExit('No encontré openAccountMenu exacto')

validate_inline_js(html, 'mi-cuenta/index.html')
for required in ['const SECURITY_API=', 'function openPasswordSettings()', 'function openDeleteAccount()', 'async function updateAccountPassword(', 'Eliminar definitivamente']:
    if required not in html: raise SystemExit('Falta '+required)
path.write_text(html, encoding='utf-8')
print('PARTE 2 aplicada y validada')

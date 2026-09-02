from pathlib import Path
import re
import subprocess
import tempfile

path = Path('mi-cuenta/index.html')
text = path.read_text(encoding='utf-8')

# 1) El aviso de contraseña de respaldo solo aparece después de un login real con Google
# y vuelve a ser opcional. Nunca debe interrumpir una activación/perfil en curso.
pattern = r'async function maybeOfferGooglePasswordBackup\(\)\{.*?\n\}\nfunction openAccountMenu\(\)\{'
replacement = '''async function maybeOfferGooglePasswordBackup(){
 if(sessionStorage.getItem(GOOGLE_JUST_SIGNED_IN_KEY)!=="1")return;
 sessionStorage.removeItem(GOOGLE_JUST_SIGNED_IN_KEY);
 try{
  const st=await securityPost({action:"status"});
  if(!st?.google||st?.has_password)return;
  openModal(`<div class="sheethead"><div><div class="kicker">SEGURIDAD</div><h2>Creá una contraseña de respaldo</h2></div><button class="x" onclick="closeModal()">×</button></div><p class="muted">Así también vas a poder entrar con tu email si algún día no podés usar Google.</p><button class="btn primary wide" id="passwordBackupNow" type="button">Crear contraseña</button><button class="btn soft wide" id="passwordBackupLater" type="button" style="margin-top:9px">Ahora no</button>`);
  document.getElementById("passwordBackupNow").onclick=()=>{closeModal();setTimeout(()=>openPasswordSettings(),0)};
  document.getElementById("passwordBackupLater").onclick=()=>closeModal();
 }catch(err){console.warn("password backup offer",err)}
}
function openAccountMenu(){'''
text, n = re.subn(pattern, lambda _m: replacement, text, count=1, flags=re.S)
if n != 1:
    raise SystemExit('No pude actualizar maybeOfferGooglePasswordBackup')

# 2) La contraseña se agrega a la MISMA cuenta autenticada mediante /auth/v1/user.
# No se fuerza un segundo login, porque eso era lo que podía cambiar/romper el estado
# de sesión en medio del flujo de chapita y perfil.
old = 'const sessionEmail=String(currentUser?.email||getSession()?.user?.email||"").trim().toLowerCase();await securityPost({action:"password",password});if(sessionEmail){try{await login(sessionEmail,password)}catch{setSession(null);closeModal();showAuth("Contraseña guardada. Ingresá con tu email y la nueva contraseña.");return}}closeModal();toast("Contraseña guardada ✅")'
new = 'await updateAccountPassword(password);closeModal();toast("Contraseña guardada ✅")'
if old not in text:
    raise SystemExit('No encontré el guardado viejo de contraseña')
text = text.replace(old, new, 1)

# 3) Mantener el usuario actualizado dentro de la sesión local sin cambiar tokens.
pattern_update = r'async function updateAccountPassword\(password\)\{.*?return j\}'
replacement_update = '''async function updateAccountPassword(password){let s=await validSession();if(!s)throw new Error("Sesión vencida.");const r=await fetch(AUTH+"/user",{method:"PUT",headers:{"Content-Type":"application/json",apikey:PUBLISHABLE_KEY,Authorization:"Bearer "+s.access_token},body:JSON.stringify({password})});const j=await r.json().catch(()=>({}));if(r.status===401){setSession(null);showAuth("Tu sesión venció. Volvé a ingresar.");throw new Error("Sesión vencida.")}if(!r.ok)throw new Error(j.msg||j.error_description||j.error||"No pudimos guardar la contraseña.");if(j?.id){const stored=getSession();if(stored){stored.user=j;setSession(stored)}if(currentUser?.id===j.id)currentUser={...currentUser,...j}}return j}'''
text, n = re.subn(pattern_update, lambda _m: replacement_update, text, count=1, flags=re.S)
if n != 1:
    raise SystemExit('No pude reforzar updateAccountPassword')

# 4) Jamás abrir el aviso de contraseña encima del formulario de alta de mascota.
text = text.replace('showActivationProfile(fin.public_code);setTimeout(()=>maybeOfferGooglePasswordBackup(),80);return', 'showActivationProfile(fin.public_code);return')
text = text.replace('showActivationProfile(claim.public_code||googlePending.public_code);setTimeout(()=>maybeOfferGooglePasswordBackup(),80);return', 'showActivationProfile(claim.public_code||googlePending.public_code);return')

# Invariantes del arreglo.
required = [
    'if(sessionStorage.getItem(GOOGLE_JUST_SIGNED_IN_KEY)!=="1")return;',
    'id="passwordBackupLater"',
    '>Ahora no</button>',
    'await updateAccountPassword(password);closeModal();toast("Contraseña guardada ✅")',
    'await loadDashboard();setTimeout(()=>maybeOfferGooglePasswordBackup(),80);',
    'function openClaim(){openPinClaim()}',
    'find_tag_by_activation_pin',
]
for value in required:
    if value not in text:
        raise SystemExit('Falta una garantía requerida: ' + value)

for forbidden in [
    'openPasswordSettings(true)',
    'await securityPost({action:"password",password})',
    'await login(sessionEmail,password)',
    'showActivationProfile(fin.public_code);setTimeout(()=>maybeOfferGooglePasswordBackup(),80);return',
    'showActivationProfile(claim.public_code||googlePending.public_code);setTimeout(()=>maybeOfferGooglePasswordBackup(),80);return',
]:
    if forbidden in text:
        raise SystemExit('Quedó un flujo riesgoso: ' + forbidden)

# Validar sintaxis de todos los scripts inline.
scripts = re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', text, flags=re.S | re.I)
for i, js in enumerate(scripts, 1):
    if not js.strip():
        continue
    with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as f:
        f.write(js)
        tmp = f.name
    result = subprocess.run(['node', '--check', tmp], capture_output=True, text=True)
    if result.returncode:
        raise SystemExit(f'JavaScript inválido en script {i}: {result.stderr}')

path.write_text(text, encoding='utf-8')
print('Flujo Google/contraseña corregido sin relogueo ni interrupción de activación')

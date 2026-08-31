from pathlib import Path
import re
import subprocess
import tempfile

path = Path('mi-cuenta/index.html')
text = path.read_text(encoding='utf-8')

# 1) La comprobación debe ejecutarse siempre: si la cuenta usa Google y todavía
# no tiene contraseña de Patas a Casa, abre directamente el formulario obligatorio.
pattern = r'async function maybeOfferGooglePasswordBackup\(\)\{.*?\n\}\nfunction openAccountMenu\(\)\{'
replacement = '''async function maybeOfferGooglePasswordBackup(){
 try{
  const st=await securityPost({action:"status"});
  if(!st?.google||st?.has_password)return;
  sessionStorage.removeItem(GOOGLE_JUST_SIGNED_IN_KEY);
  openPasswordSettings(true);
 }catch(err){console.warn("google password required",err)}
}
function openAccountMenu(){'''
text, n = re.subn(pattern, lambda _m: replacement, text, count=1, flags=re.S)
if n != 1:
    raise SystemExit('No pude actualizar la comprobación de contraseña de Google')

# 2) El formulario de contraseña puede ser normal (desde Mi cuenta) u obligatorio
# (después de entrar con Google). En modo obligatorio no hay X, Cancelar ni cierre
# tocando el fondo del modal.
start = text.find('function openPasswordSettings(){')
end = text.find('\nfunction openDeleteAccount(){', start)
if start < 0 or end < 0:
    raise SystemExit('No encontré openPasswordSettings')
block = text[start:end]
block = block.replace('function openPasswordSettings(){', 'function openPasswordSettings(required=false){', 1)
block = block.replace('onclick="openAccountMenu()">Cancelar</button>', 'id="passwordSettingsCancel" onclick="openAccountMenu()">Cancelar</button>', 1)
block, m = re.subn(r'openModal\((`.*?`)\);', lambda x: f'openModal({x.group(1)},!required);', block, count=1, flags=re.S)
if m != 1:
    raise SystemExit('No pude hacer no cerrable el formulario obligatorio')
needle = ' bindPasswordToggles(modal);'
if needle not in block:
    raise SystemExit('No encontré el punto de inicialización del formulario')
block = block.replace(needle, ' if(required){modal.querySelector(".sheethead .x")?.remove();document.getElementById("passwordSettingsCancel")?.remove()}'+needle, 1)
text = text[:start] + block + text[end:]

# 3) El modal acepta modo no cerrable para pasos realmente obligatorios.
old_modal = 'function openModal(content){modal.innerHTML=`<div class="sheet">${content}</div>`;modal.classList.remove("hidden");modal.addEventListener("click",e=>{if(e.target===modal)closeModal()},{once:true})}'
new_modal = 'function openModal(content,closable=true){modal.innerHTML=`<div class="sheet">${content}</div>`;modal.classList.remove("hidden");if(closable)modal.addEventListener("click",e=>{if(e.target===modal)closeModal()},{once:true})}'
if old_modal not in text:
    raise SystemExit('No encontré openModal para aplicar modo obligatorio')
text = text.replace(old_modal, new_modal, 1)

# Invariantes de seguridad y del flujo actual.
required = [
    'function openClaim(){openPinClaim()}',
    'find_tag_by_activation_pin',
    'async function maybeOfferGooglePasswordBackup()',
    'if(!st?.google||st?.has_password)return;',
    'openPasswordSettings(true);',
    'function openPasswordSettings(required=false)',
    'securityPost({action:"password",password})',
    'Esta contraseña es de Patas a Casa. Te permite entrar con tu email aunque hayas creado la cuenta con Google.',
]
for value in required:
    if value not in text:
        raise SystemExit('Falta una garantía requerida: ' + value)

for forbidden in ['passwordBackupLater', '>Ahora no</button>', 'patas-tag-scan', 'Html5Qrcode', 'patas-email-activation']:
    if forbidden in text:
        raise SystemExit('Quedó un flujo que no debe existir: ' + forbidden)

# Validar sintaxis de todos los scripts inline antes de escribir.
scripts = re.findall(r'<script(?![^>]*\\bsrc=)[^>]*>(.*?)</script>', text, flags=re.S | re.I)
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
print('Google conserva login y ahora exige contraseña de Patas a Casa hasta que se guarde')

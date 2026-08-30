from pathlib import Path
import re
import subprocess
import tempfile

root_path = Path('index.html')
account_path = Path('mi-cuenta/index.html')
root = root_path.read_text(encoding='utf-8')
account = account_path.read_text(encoding='utf-8')

old = 'try{const data=await getTag(code);if(data.state==="unactivated"){const emailMode=await emailActivationMode(code).catch(()=>false);if(emailMode)accountSetupForm(code,"","email");else unactivated(code)}else{const lostInfo=await getLostInfo(code).catch(()=>null);active(code,{...data.pet,...(lostInfo||{})})}}'
new = 'try{const data=await getTag(code);if(data.state==="unactivated"){unactivated(code)}else{const lostInfo=await getLostInfo(code).catch(()=>null);active(code,{...data.pet,...(lostInfo||{})})}}'

if old in root:
    root = root.replace(old, new, 1)
elif new not in root:
    raise SystemExit('No encontré el boot de activación esperado')

# Invariantes del rollback y de las funciones que sí deben conservarse.
required_root = [
    'if(data.state==="unactivated"){unactivated(code)}',
    'const activationIsiOS=/iphone|ipad|ipod/i.test(navigator.userAgent)',
    'if(activationIsiOS){document.getElementById("googleActivationOptions")?.remove()}',
]
required_account = [
    'function openClaim(){openPinClaim()}',
    'function openPinClaim(knownCode="")',
    'if(isiOS()){document.querySelectorAll("[data-google-options]").forEach(el=>el.remove());return}',
    'Crear o cambiar contraseña',
    'securityPost({action:"password",password})',
    'Esta contraseña es de Patas a Casa. Te permite entrar con tu email aunque hayas creado la cuenta con Google.',
]
for value in required_root:
    if value not in root:
        raise SystemExit('Falta en index.html: ' + value)
for value in required_account:
    if value not in account:
        raise SystemExit('Falta en mi-cuenta/index.html: ' + value)

# El camino activo de una chapita nueva ya no debe consultar el método email.
boot_start = root.find('async function boot(){')
boot_end = root.find('\nboot();', boot_start)
if boot_start < 0 or boot_end < 0:
    raise SystemExit('No encontré boot()')
boot_block = root[boot_start:boot_end]
if 'emailActivationMode(' in boot_block:
    raise SystemExit('boot() todavía consulta activación por email')

# Validar JavaScript inline de las dos pantallas principales.
def check_inline_js(name, html):
    scripts = re.findall(r'<script(?![^>]*\\bsrc=)[^>]*>(.*?)</script>', html, flags=re.S | re.I)
    for i, js in enumerate(scripts, 1):
        if not js.strip():
            continue
        with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as f:
            f.write(js)
            tmp = f.name
        result = subprocess.run(['node', '--check', tmp], capture_output=True, text=True)
        if result.returncode:
            raise SystemExit(f'JS inválido en {name}, script {i}: {result.stderr}')

check_inline_js('index.html', root)
check_inline_js('mi-cuenta/index.html', account)

root_path.write_text(root, encoding='utf-8')
print('Flujo público directo a PIN; Google iPhone y contraseña Google preservados; JS validado')

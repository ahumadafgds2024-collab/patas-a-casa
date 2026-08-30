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

# PARTE 1: limpiar activación pública + ocultar Google en iPhone/iPad
home_path = Path('index.html')
home = home_path.read_text(encoding='utf-8')

home = home.replace('Etiqueta ya activada (Modo Demo)', 'Etiqueta ya activada')
home = home.replace('Activación de prueba:', 'Activación de esta chapita:')
home = home.replace('<div class="kicker">SEGURIDAD DE LA CUENTA</div>\n   <h1>Configurá tu acceso.</h1>', '<div class="kicker">ACTIVAR CHAPITA</div>\n   <h1>Activá tu chapita.</h1>', 1)
home = home.replace('${emailMode?"No necesitás un PIN. Verificamos tu correo para vincular esta chapita de forma segura.":"Antes de crear el perfil, elegí el correo y la contraseña con los que vas a administrarlo."}', '${emailMode?"Creá una cuenta o ingresá con la que ya tenés. Después vas a cargar los datos de tu mascota.":"Antes de crear el perfil, elegí el correo y la contraseña con los que vas a administrarlo."}', 1)
home = home.replace('<div class="note" style="margin-bottom:14px"><b>Chapita ${esc(c)} ${emailMode?"lista para vincular":"verificada"} ✅</b><br>${emailMode?"El QR de esta chapita reemplaza al PIN impreso.":"No tenés que ingresar el código ni el PIN otra vez."}</div>', '<div class="note" style="margin-bottom:14px">${emailMode?`<b>Tu chapita está lista ✅</b><br>Creá una cuenta o ingresá a la que ya tenés para continuar.`:`<b>Chapita ${esc(c)} verificada ✅</b><br>No tenés que ingresar el código ni el PIN otra vez.`}</div>', 1)

old = ' fetch(SUPABASE_URL+"/auth/v1/settings",{headers:{apikey:PUBLISHABLE_KEY}}).then(r=>r.ok?r.json():null).then(settings=>{if(settings?.external?.google)document.getElementById("googleActivationOptions")?.classList.remove("hidden")}).catch(()=>{});'
new = ' const activationIsiOS=/iphone|ipad|ipod/i.test(navigator.userAgent)||(navigator.platform==="MacIntel"&&navigator.maxTouchPoints>1);\n if(activationIsiOS){document.getElementById("googleActivationOptions")?.remove()}else{fetch(SUPABASE_URL+"/auth/v1/settings",{headers:{apikey:PUBLISHABLE_KEY}}).then(r=>r.ok?r.json():null).then(settings=>{if(settings?.external?.google)document.getElementById("googleActivationOptions")?.classList.remove("hidden")}).catch(()=>{})}'
if old in home:
    home = home.replace(old, new, 1)
elif 'const activationIsiOS=' not in home:
    raise SystemExit('No pude ubicar Google en activación pública')
home = home.replace(' document.getElementById("googleActivation").addEventListener("click",()=>{', ' document.getElementById("googleActivation")?.addEventListener("click",()=>{', 1)

account_path = Path('mi-cuenta/index.html')
account = account_path.read_text(encoding='utf-8')
old_reveal = '''async function revealGoogleOptions(){
 try{const r=await fetch(AUTH+"/settings",{headers:{apikey:PUBLISHABLE_KEY}}),settings=r.ok?await r.json():null;if(settings?.external?.google)document.querySelectorAll("[data-google-options]").forEach(el=>el.classList.remove("hidden"))}catch{}
}'''
new_reveal = '''async function revealGoogleOptions(){
 if(isiOS()){document.querySelectorAll("[data-google-options]").forEach(el=>el.remove());return}
 try{const r=await fetch(AUTH+"/settings",{headers:{apikey:PUBLISHABLE_KEY}}),settings=r.ok?await r.json():null;if(settings?.external?.google)document.querySelectorAll("[data-google-options]").forEach(el=>el.classList.remove("hidden"))}catch{}
}'''
if old_reveal in account:
    account = account.replace(old_reveal, new_reveal, 1)
elif 'forEach(el=>el.remove());return' not in account:
    raise SystemExit('No pude ubicar revealGoogleOptions')
account = account.replace(' document.getElementById("googleLogin").addEventListener(', ' document.getElementById("googleLogin")?.addEventListener(', 1)
account = account.replace(' document.getElementById("googleSignup").addEventListener(', ' document.getElementById("googleSignup")?.addEventListener(', 1)

validate_inline_js(home, 'index.html')
validate_inline_js(account, 'mi-cuenta/index.html')

for required in ['const activationIsiOS=', 'Activá tu chapita.']:
    if required not in home: raise SystemExit('Falta '+required)
if 'forEach(el=>el.remove());return' not in account: raise SystemExit('Falta ocultar Google en iPhone dentro de Mi cuenta')

home_path.write_text(home, encoding='utf-8')
account_path.write_text(account, encoding='utf-8')
print('PARTE 1 aplicada y validada')

from pathlib import Path
import re
import subprocess
import tempfile

root_path = Path('index.html')
account_path = Path('mi-cuenta/index.html')
root = root_path.read_text(encoding='utf-8')
account = account_path.read_text(encoding='utf-8')


def remove_line(text, fragment):
    return ''.join(line for line in text.splitlines(True) if fragment not in line)


def replace_if_present(text, old, new):
    return text.replace(old, new) if old in text else text


# --- Sitio publico: conservar exclusivamente activacion por PIN ---
root = remove_line(root, 'const EMAIL_ACTIVATION_API=')
root = re.sub(r'^async function emailActivationPost\(data\)\{.*\}\n', '', root, flags=re.M)
root = re.sub(r'^async function emailActivationMode\(c\)\{.*\}\n', '', root, flags=re.M)
root = replace_if_present(root, 'function accountSetupForm(c,pin,method="pin"){\n const emailMode=method==="email";', 'function accountSetupForm(c,pin){')
root = replace_if_present(
    root,
    '<p class="muted">${emailMode?"Creá una cuenta o ingresá con la que ya tenés. Después vas a cargar los datos de tu mascota.":"Antes de crear el perfil, elegí el correo y la contraseña con los que vas a administrarlo."}</p>',
    '<p class="muted">Antes de crear el perfil, elegí el correo y la contraseña con los que vas a administrarlo.</p>'
)
root = replace_if_present(
    root,
    '<div class="note" style="margin-bottom:14px">${emailMode?`<b>Tu chapita está lista ✅</b><br>Creá una cuenta o ingresá a la que ya tenés para continuar.`:`<b>Chapita ${esc(c)} verificada ✅</b><br>No tenés que ingresar el código ni el PIN otra vez.`}</div>',
    '<div class="note" style="margin-bottom:14px"><b>Chapita ${esc(c)} verificada ✅</b><br>No tenés que ingresar el código ni el PIN otra vez.</div>'
)
root = replace_if_present(
    root,
    '   ${emailMode?`<button class="btn soft" id="existingActivationAccount" type="button" style="margin-bottom:10px">Ya tengo cuenta</button><div class="auth-divider">o creá una cuenta nueva</div>`:""}\n',
    ''
)
root = replace_if_present(
    root,
    '   (emailMode?localStorage:sessionStorage).setItem(GOOGLE_PENDING_KEY,JSON.stringify({public_code:c,activation_code:emailMode?"":pin,activation_method:emailMode?"email":"pin",created_at:Date.now()}));',
    '   sessionStorage.setItem(GOOGLE_PENDING_KEY,JSON.stringify({public_code:c,activation_code:pin,created_at:Date.now()}));'
)
root = re.sub(r'^ document\.getElementById\("existingActivationAccount"\)\?\.addEventListener\(.*\n', '', root, flags=re.M)
root = replace_if_present(
    root,
    'try{localStorage.setItem("pac_legal_consent",JSON.stringify({version:"2026-08-28",accepted_at:new Date().toISOString()}));const payload={action:"start_registration",public_code:c,email:mail,password,legal_consent:true,legal_version:"2026-08-28"};if(emailMode)await emailActivationPost(payload);else await registerPost({...payload,activation_code:pin});activationComplete(mail)}',
    'try{localStorage.setItem("pac_legal_consent",JSON.stringify({version:"2026-08-28",accepted_at:new Date().toISOString()}));const payload={action:"start_registration",public_code:c,email:mail,password,legal_consent:true,legal_version:"2026-08-28"};await registerPost({...payload,activation_code:pin});activationComplete(mail)}'
)

# --- Mi cuenta: sacar lector QR y cualquier bifurcacion email-only ---
account = remove_line(account, 'const EMAIL_ACTIVATION_API=')
account = remove_line(account, 'const TAG_SCAN_API=')
account = account.replace(',tagScanner=null,tagScanLocked=false,qrScannerLibPromise=null', '')
account = re.sub(r'^async function emailActivationPost\(data\)\{.*\}\n', '', account, flags=re.M)
account = re.sub(r'^async function tagScanPost\(scan\)\{.*\}\n', '', account, flags=re.M)

scanner_pattern = r'function loadQrScannerLibrary\(\)\{.*?\n\}\n\nfunction openClaim\(\)\{openPinClaim\(\)\}'
account, scanner_removed = re.subn(scanner_pattern, 'function openClaim(){openPinClaim()}', account, count=1, flags=re.S)
if scanner_removed == 0 and 'function loadQrScannerLibrary()' in account:
    raise SystemExit('No pude retirar de forma segura el bloque del lector QR')

queue_pattern = r'function queueGoogleActivation\(publicCode,activationCode="",activationMethod="pin"\)\{.*?\n\}\nfunction pendingGoogleActivation\(\)\{.*?\n\}'
queue_replacement = '''function queueGoogleActivation(publicCode,activationCode=""){
 const c=String(publicCode||"").trim().toUpperCase().replace(/[^A-Z0-9]/g,"").slice(0,12),pin=String(activationCode||"").replace(/\\D/g,"").slice(0,8);
 if(!c)throw new Error("Ingresá el código de la chapita.");
 if(!/^\\d{8}$/.test(pin))throw new Error("Ingresá los 8 números del PIN.");
 const pending={public_code:c,activation_code:pin,created_at:Date.now()};sessionStorage.setItem(GOOGLE_PENDING_KEY,JSON.stringify(pending));return pending;
}
function pendingGoogleActivation(){
 try{localStorage.removeItem(GOOGLE_PENDING_KEY);const raw=sessionStorage.getItem(GOOGLE_PENDING_KEY);const pending=JSON.parse(raw||"null");if(!pending||Date.now()-Number(pending.created_at)>15*60*1000){sessionStorage.removeItem(GOOGLE_PENDING_KEY);return null}return pending}catch{sessionStorage.removeItem(GOOGLE_PENDING_KEY);return null}
}'''
account, queue_changed = re.subn(queue_pattern, queue_replacement, account, count=1, flags=re.S)
if queue_changed == 0 and 'activationMethod="pin"' in account:
    raise SystemExit('No pude simplificar la activacion Google a PIN')

account = replace_if_present(
    account,
    'if(pending)queueGoogleActivation(pending.public_code,pending.activation_code,pending.activation_method);',
    'if(pending)queueGoogleActivation(pending.public_code,pending.activation_code);'
)
account = re.sub(
    r'async function prepareQueuedActivation\(pending\)\{[^\n]*\}',
    'async function prepareQueuedActivation(pending){if(!pending)return null;return await accountPost({action:"prepare_activation",public_code:pending.public_code,activation_code:pending.activation_code})}',
    account,
    count=1,
)
account = replace_if_present(
    account,
    'function closeModal(){stopTagScanner();if(flyerObjectUrl)',
    'function closeModal(){if(flyerObjectUrl)'
)

# --- Invariantes: lo que SI queda ---
required_root = [
    'action:"verify_pin"',
    'function accountSetupForm(c,pin)',
    'await registerPost({...payload,activation_code:pin})',
    'sessionStorage.setItem(GOOGLE_PENDING_KEY',
]
required_account = [
    'function openClaim(){openPinClaim()}',
    'function openPinClaim(knownCode="")',
    'find_tag_by_activation_pin',
    'maybeOfferGooglePasswordBackup',
    'Crear o cambiar contraseña',
    'securityPost({action:"password",password})',
    'Esta contraseña es de Patas a Casa. Te permite entrar con tu email aunque hayas creado la cuenta con Google.',
    'async function prepareQueuedActivation(pending){if(!pending)return null;return await accountPost({action:"prepare_activation",public_code:pending.public_code,activation_code:pending.activation_code})}',
]
for value in required_root:
    if value not in root:
        raise SystemExit('Falta en index.html una funcion que debe conservarse: ' + value)
for value in required_account:
    if value not in account:
        raise SystemExit('Falta en mi-cuenta/index.html una funcion que debe conservarse: ' + value)

forbidden_root = [
    'patas-email-activation', 'EMAIL_ACTIVATION_API', 'emailActivationPost', 'emailActivationMode',
    'emailMode', 'activation_method:"email"', 'existingActivationAccount'
]
forbidden_account = [
    'patas-email-activation', 'EMAIL_ACTIVATION_API', 'patas-tag-scan', 'TAG_SCAN_API',
    'emailActivationPost', 'tagScanPost', 'loadQrScannerLibrary', 'Html5Qrcode', 'openQrScanner',
    'startTagCamera', 'scanQrPhoto', 'stopTagScanner', 'tagScanner', 'tagScanLocked', 'qrScannerLibPromise',
    'activation_method', 'activationMethod="pin"'
]
for value in forbidden_root:
    if value in root:
        raise SystemExit('Quedó un resto obsoleto en index.html: ' + value)
for value in forbidden_account:
    if value in account:
        raise SystemExit('Quedó un resto obsoleto en mi-cuenta/index.html: ' + value)


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
account_path.write_text(account, encoding='utf-8')
print('Limpieza completada: PIN preservado, lector QR retirado, email-only retirado, Google + contraseña preservados')

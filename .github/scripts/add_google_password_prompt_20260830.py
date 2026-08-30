from pathlib import Path
import re, subprocess, tempfile

def check_js(html):
    scripts=re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>',html,re.S|re.I)
    for js in scripts:
        if not js.strip(): continue
        with tempfile.NamedTemporaryFile('w',suffix='.js',encoding='utf-8',delete=False) as f:
            f.write(js); name=f.name
        r=subprocess.run(['node','--check',name],capture_output=True,text=True)
        if r.returncode: raise SystemExit(r.stderr)

p=Path('mi-cuenta/index.html'); h=p.read_text(encoding='utf-8')

# Marca de retorno OAuth Google.
marker='const GOOGLE_PENDING_KEY="pac_google_activation_v1";'
if 'GOOGLE_JUST_SIGNED_IN_KEY' not in h:
    if marker not in h: raise SystemExit('No encontré GOOGLE_PENDING_KEY')
    h=h.replace(marker,marker+'\nconst GOOGLE_JUST_SIGNED_IN_KEY="pac_google_just_signed_in_v1";',1)

old='const session=data.session;setSession({access_token:session.access_token,refresh_token:session.refresh_token,expires_in:session.expires_in,expires_at:session.expires_at,token_type:session.token_type,user:session.user});history.replaceState({},document.title,"/mi-cuenta/");return true;'
new='const session=data.session;setSession({access_token:session.access_token,refresh_token:session.refresh_token,expires_in:session.expires_in,expires_at:session.expires_at,token_type:session.token_type,user:session.user});sessionStorage.setItem(GOOGLE_JUST_SIGNED_IN_KEY,"1");history.replaceState({},document.title,"/mi-cuenta/");return true;'
if old in h: h=h.replace(old,new,1)
elif 'sessionStorage.setItem(GOOGLE_JUST_SIGNED_IN_KEY,"1")' not in h: raise SystemExit('No encontré retorno OAuth')

# Guardar contraseña mediante endpoint seguro para registrar que ya existe.
h=h.replace('await updateAccountPassword(password);closeModal();toast("Contraseña guardada ✅")','await securityPost({action:"password",password});closeModal();toast("Contraseña guardada ✅")',1)

# Supabase invalida la sesión activa al cambiar la contraseña. Volvemos a iniciar
# sesión inmediatamente con la contraseña recién creada para que el usuario no
# salga del flujo ni vea "Sesión vencida".
old_save='try{await securityPost({action:"password",password});closeModal();toast("Contraseña guardada ✅")}catch(err){toast(err.message)}finally{if(document.body.contains(b)){b.disabled=false;b.textContent=bak}}'
new_save='try{const sessionEmail=String(currentUser?.email||getSession()?.user?.email||"").trim().toLowerCase();await securityPost({action:"password",password});if(sessionEmail){try{await login(sessionEmail,password)}catch{setSession(null);closeModal();showAuth("Contraseña guardada. Ingresá con tu email y la nueva contraseña.");return}}closeModal();toast("Contraseña guardada ✅")}catch(err){toast(err.message)}finally{if(document.body.contains(b)){b.disabled=false;b.textContent=bak}}'
if old_save in h:
    h=h.replace(old_save,new_save,1)
elif 'const sessionEmail=String(currentUser?.email||getSession()?.user?.email||"")' not in h:
    raise SystemExit('No encontré guardado de contraseña')

# Oferta opcional y solo tras Google.
if 'async function maybeOfferGooglePasswordBackup()' not in h:
    anchor='function openAccountMenu(){'
    if anchor not in h: raise SystemExit('No encontré openAccountMenu')
    fn='''async function maybeOfferGooglePasswordBackup(){\n if(sessionStorage.getItem(GOOGLE_JUST_SIGNED_IN_KEY)!=="1")return;\n sessionStorage.removeItem(GOOGLE_JUST_SIGNED_IN_KEY);\n try{const st=await securityPost({action:"status"});if(!st?.google||st?.has_password)return;openModal(`<div class="sheethead"><div><div class="kicker">SEGURIDAD</div><h2>Creá una contraseña de respaldo</h2></div><button class="x" onclick="closeModal()">×</button></div><p class="muted">Así también vas a poder entrar con tu email si algún día no podés usar Google.</p><button class="btn primary wide" id="passwordBackupNow" type="button">Crear contraseña</button><button class="btn soft wide" id="passwordBackupLater" type="button" style="margin-top:9px">Ahora no</button>`);document.getElementById("passwordBackupNow").onclick=()=>{closeModal();setTimeout(()=>openPasswordSettings(),0)};document.getElementById("passwordBackupLater").onclick=()=>closeModal()}catch(err){console.warn("password backup offer",err)}\n}\n'''
    h=h.replace(anchor,fn+anchor,1)

# Mostrar oferta sin bloquear el formulario de mascota / dashboard.
old1='showActivationProfile(claim.public_code||googlePending.public_code);return'
new1='showActivationProfile(claim.public_code||googlePending.public_code);setTimeout(()=>maybeOfferGooglePasswordBackup(),80);return'
if old1 in h: h=h.replace(old1,new1,1)
elif new1 not in h: raise SystemExit('No encontré claim profile')
old2='showActivationProfile(fin.public_code);return'
new2='showActivationProfile(fin.public_code);setTimeout(()=>maybeOfferGooglePasswordBackup(),80);return'
if old2 in h: h=h.replace(old2,new2,1)

old3='await loadDashboard();\n}\nboot();'
new3='await loadDashboard();setTimeout(()=>maybeOfferGooglePasswordBackup(),80);\n}\nboot();'
if old3 in h: h=h.replace(old3,new3,1)
elif new3 not in h: raise SystemExit('No encontré final de boot')

check_js(h)
for x in ['async function maybeOfferGooglePasswordBackup()','securityPost({action:"status"})','securityPost({action:"password",password})','GOOGLE_JUST_SIGNED_IN_KEY','const sessionEmail=String(currentUser?.email||getSession()?.user?.email||"")']:
    if x not in h: raise SystemExit('Falta '+x)
p.write_text(h,encoding='utf-8')
print('OK aviso contraseña Google + sesión renovada')

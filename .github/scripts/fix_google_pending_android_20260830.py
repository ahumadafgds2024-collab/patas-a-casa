from pathlib import Path
import re, subprocess, tempfile


def check_js(html, label):
    scripts=re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>',html,re.S|re.I)
    for i,js in enumerate(scripts,1):
        if not js.strip(): continue
        with tempfile.NamedTemporaryFile('w',suffix='.js',encoding='utf-8',delete=False) as f:
            f.write(js); name=f.name
        r=subprocess.run(['node','--check',name],capture_output=True,text=True)
        if r.returncode!=0: raise SystemExit(f'JS inválido en {label} script {i}:\n{r.stderr}')

# Página pública: para activaciones email persistir la intención fuera de sessionStorage.
p=Path('index.html'); h=p.read_text(encoding='utf-8')
old='sessionStorage.setItem(GOOGLE_PENDING_KEY,JSON.stringify({public_code:c,activation_code:emailMode?"":pin,activation_method:emailMode?"email":"pin",created_at:Date.now()}));'
new='(emailMode?localStorage:sessionStorage).setItem(GOOGLE_PENDING_KEY,JSON.stringify({public_code:c,activation_code:emailMode?"":pin,activation_method:emailMode?"email":"pin",created_at:Date.now()}));'
if old in h: h=h.replace(old,new,1)
elif new not in h: raise SystemExit('No encontré pending de Google en index.html')
old2='document.getElementById("existingActivationAccount")?.addEventListener("click",()=>{sessionStorage.setItem(GOOGLE_PENDING_KEY,JSON.stringify({public_code:c,activation_code:"",activation_method:"email",created_at:Date.now()}));location.assign("/mi-cuenta/")});'
new2='document.getElementById("existingActivationAccount")?.addEventListener("click",()=>{localStorage.setItem(GOOGLE_PENDING_KEY,JSON.stringify({public_code:c,activation_code:"",activation_method:"email",created_at:Date.now()}));location.assign("/mi-cuenta/")});'
if old2 in h: h=h.replace(old2,new2,1)
elif new2 not in h: raise SystemExit('No encontré existingActivationAccount')
check_js(h,'index.html'); p.write_text(h,encoding='utf-8')

# Mi cuenta: leer primero localStorage (sobrevive OAuth Android), con fallback al storage viejo.
p=Path('mi-cuenta/index.html'); a=p.read_text(encoding='utf-8')
oldq='const pending={public_code:c,activation_code:method==="email"?"":pin,activation_method:method,created_at:Date.now()};sessionStorage.setItem(GOOGLE_PENDING_KEY,JSON.stringify(pending));return pending;'
newq='const pending={public_code:c,activation_code:method==="email"?"":pin,activation_method:method,created_at:Date.now()};(method==="email"?localStorage:sessionStorage).setItem(GOOGLE_PENDING_KEY,JSON.stringify(pending));return pending;'
if oldq in a: a=a.replace(oldq,newq,1)
elif newq not in a: raise SystemExit('No encontré queueGoogleActivation')
oldp='try{const pending=JSON.parse(sessionStorage.getItem(GOOGLE_PENDING_KEY)||"null");if(!pending||Date.now()-Number(pending.created_at)>15*60*1000){sessionStorage.removeItem(GOOGLE_PENDING_KEY);return null}pending.activation_method=pending.activation_method==="email"?"email":"pin";return pending}catch{sessionStorage.removeItem(GOOGLE_PENDING_KEY);return null}'
newp='try{const raw=localStorage.getItem(GOOGLE_PENDING_KEY)||sessionStorage.getItem(GOOGLE_PENDING_KEY);const pending=JSON.parse(raw||"null");if(!pending||Date.now()-Number(pending.created_at)>15*60*1000){localStorage.removeItem(GOOGLE_PENDING_KEY);sessionStorage.removeItem(GOOGLE_PENDING_KEY);return null}pending.activation_method=pending.activation_method==="email"?"email":"pin";return pending}catch{localStorage.removeItem(GOOGLE_PENDING_KEY);sessionStorage.removeItem(GOOGLE_PENDING_KEY);return null}'
if oldp in a: a=a.replace(oldp,newp,1)
elif newp not in a: raise SystemExit('No encontré pendingGoogleActivation')
oldc='function clearGoogleActivation(){sessionStorage.removeItem(GOOGLE_PENDING_KEY)}'
newc='function clearGoogleActivation(){localStorage.removeItem(GOOGLE_PENDING_KEY);sessionStorage.removeItem(GOOGLE_PENDING_KEY)}'
if oldc in a: a=a.replace(oldc,newc,1)
elif newc not in a: raise SystemExit('No encontré clearGoogleActivation')
check_js(a,'mi-cuenta/index.html'); p.write_text(a,encoding='utf-8')

for x in ['localStorage.getItem(GOOGLE_PENDING_KEY)||sessionStorage.getItem(GOOGLE_PENDING_KEY)','method==="email"?localStorage:sessionStorage']:
    if x not in a: raise SystemExit('Falta '+x)
print('OK continuidad OAuth Android')

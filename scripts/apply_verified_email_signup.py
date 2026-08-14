from pathlib import Path

p = Path('mi-cuenta/index.html')
s = p.read_text(encoding='utf-8')

repls = []

repls.append((
'const ACCOUNT_API=SUPABASE_URL+"/functions/v1/patas-account";\nconst LOST_API=SUPABASE_URL+"/functions/v1/patas-lost";',
'const ACCOUNT_API=SUPABASE_URL+"/functions/v1/patas-account";\nconst REGISTER_API=SUPABASE_URL+"/functions/v1/patas-register-v2";\nconst LOST_API=SUPABASE_URL+"/functions/v1/patas-lost";'
))

repls.append((
'async function accountPost(data,requiresAuth=true){let s=requiresAuth?await validSession():null;const h={"Content-Type":"application/json","apikey":PUBLISHABLE_KEY};if(s?.access_token)h.Authorization="Bearer "+s.access_token;const r=await fetch(ACCOUNT_API,{method:"POST",headers:h,body:JSON.stringify(data)});const j=await r.json().catch(()=>({}));if(r.status===401&&requiresAuth){setSession(null);showAuth("Tu sesión venció. Volvé a ingresar.");throw new Error("Sesión vencida.")}if(!r.ok)throw new Error(j.error||"Ocurrió un error.");return j}',
'async function accountPost(data,requiresAuth=true){let s=requiresAuth?await validSession():null;const h={"Content-Type":"application/json","apikey":PUBLISHABLE_KEY};if(s?.access_token)h.Authorization="Bearer "+s.access_token;const r=await fetch(ACCOUNT_API,{method:"POST",headers:h,body:JSON.stringify(data)});const j=await r.json().catch(()=>({}));if(r.status===401&&requiresAuth){setSession(null);showAuth("Tu sesión venció. Volvé a ingresar.");throw new Error("Sesión vencida.")}if(!r.ok)throw new Error(j.error||"Ocurrió un error.");return j}\nasync function registerPost(data,requiresAuth=false){let s=requiresAuth?await validSession():null;const h={"Content-Type":"application/json","apikey":PUBLISHABLE_KEY};if(s?.access_token)h.Authorization="Bearer "+s.access_token;const r=await fetch(REGISTER_API,{method:"POST",headers:h,body:JSON.stringify(data)});const j=await r.json().catch(()=>({}));if(r.status===401&&requiresAuth){setSession(null);showAuth("Tu sesión venció. Volvé a ingresar.");throw new Error("Sesión vencida.")}if(!r.ok)throw new Error(j.error||"Ocurrió un error.");return j}'
))

repls.append((
'  <button class="btn primary wide" type="submit">Entrar a mi cuenta</button>\n </form>',
'  <button class="btn primary wide" type="submit">Entrar a mi cuenta</button>\n  <a href="/mi-cuenta/recuperar/" style="display:block;text-align:center;margin-top:12px;color:#555;font-size:13px;font-weight:800;text-decoration:none">¿Olvidaste tu contraseña?</a>\n </form>'
))

repls.append((
'  <div class="note" style="margin-bottom:14px">Para crear tu cuenta necesitás una <b>chapita ya activada</b> y su PIN privado. Esto evita que otra persona se apropie del perfil.</div>',
'  <div class="note" style="margin-bottom:14px">Para crear tu cuenta necesitás una <b>chapita ya activada</b> y su PIN privado. Después te vamos a enviar un correo para verificar que el email realmente sea tuyo.</div>'
))

repls.append((
'  <button class="btn primary wide" type="submit">Crear mi cuenta y vincular mascota</button>',
'  <button class="btn primary wide" type="submit">Crear cuenta y verificar email</button>'
))

old_login = ' lf.addEventListener("submit",async e=>{e.preventDefault();const b=e.submitter,bak=b.textContent,f=new FormData(e.currentTarget);b.disabled=true;b.textContent="Ingresando…";try{await login(f.get("email"),f.get("password"));await loadDashboard()}catch(err){toast(err.message)}finally{b.disabled=false;b.textContent=bak}});'
new_login = ' lf.addEventListener("submit",async e=>{e.preventDefault();const b=e.submitter,bak=b.textContent,f=new FormData(e.currentTarget);b.disabled=true;b.textContent="Ingresando…";try{await login(f.get("email"),f.get("password"));let fin=null;try{fin=await registerPost({action:"finalize_registration"},true)}catch(err){console.warn("finalize_registration",err)}history.replaceState({},document.title,"/mi-cuenta/");await loadDashboard();if(fin?.linked&&!fin?.already)toast("Correo verificado. Tu mascota ya está vinculada ✅")}catch(err){const m=/email not confirmed/i.test(String(err?.message||""))?"Primero confirmá tu correo desde el enlace que te enviamos.":err.message;toast(m)}finally{b.disabled=false;b.textContent=bak}});'
repls.append((old_login, new_login))

old_signup = ' sf.addEventListener("submit",async e=>{e.preventDefault();const b=e.submitter,bak=b.textContent,f=new FormData(e.currentTarget),mail=String(f.get("email")),pass=String(f.get("password"));b.disabled=true;b.textContent="Creando cuenta…";try{await accountPost({action:"register_owner",public_code:f.get("code"),activation_code:f.get("pin"),email:mail,password:pass},false);await login(mail,pass);history.replaceState({},document.title,"/mi-cuenta/");await loadDashboard();toast("Cuenta creada. Tu mascota ya está vinculada ✅")}catch(err){toast(err.message)}finally{b.disabled=false;b.textContent=bak}});'
new_signup = ' sf.addEventListener("submit",async e=>{e.preventDefault();const form=e.currentTarget,b=e.submitter,bak=b.textContent,f=new FormData(form),mail=String(f.get("email")).trim().toLowerCase(),pass=String(f.get("password"));b.disabled=true;b.textContent="Enviando verificación…";try{await registerPost({action:"start_registration",public_code:f.get("code"),activation_code:f.get("pin"),email:mail,password:pass},false);form.innerHTML=`<div class="status ok"><b>Revisá tu correo ✅</b><br>Te enviamos un enlace de verificación a ${esc(mail)}.</div><p class="muted small">Abrí el correo y tocá el enlace. Después volvé a Mi cuenta e ingresá con tu email y contraseña. La mascota se vincula recién después de verificar el correo.</p><button class="btn dark wide" type="button" id="goLogin">Ir a ingresar</button>`;document.getElementById("goLogin").onclick=()=>tab("login")}catch(err){toast(err.message)}finally{if(document.body.contains(b)){b.disabled=false;b.textContent=bak}}});'
repls.append((old_signup, new_signup))

old_boot = ' const s=await validSession();if(s)await loadDashboard();else showAuth();'
new_boot = ' const s=await validSession();if(s){try{await registerPost({action:"finalize_registration"},true)}catch(err){console.warn("finalize_registration",err)}await loadDashboard()}else showAuth();'
repls.append((old_boot, new_boot))

for old, new in repls:
    count = s.count(old)
    if count != 1:
        raise SystemExit(f'Guard failed: expected exactly 1 occurrence, got {count}: {old[:100]!r}')
    s = s.replace(old, new, 1)

p.write_text(s, encoding='utf-8')
print('Verified email signup patch applied successfully.')

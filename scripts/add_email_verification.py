from pathlib import Path

page = Path("mi-cuenta/index.html")
s = page.read_text(encoding="utf-8")

def rep(old: str, new: str, label: str) -> None:
    global s
    count = s.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly 1 match, found {count}")
    s = s.replace(old, new, 1)

rep(
'''  <button class="btn primary wide" type="submit">Entrar a mi cuenta</button>
 </form>
 <form id="signupForm" class="hidden">''',
'''  <button class="btn primary wide" type="submit">Entrar a mi cuenta</button>
  <div style="text-align:center;margin-top:12px"><a href="/mi-cuenta/recuperar/" style="color:#555;font-size:13px;font-weight:850;text-decoration:none">¿Olvidaste tu contraseña?</a></div>
 </form>
 <form id="signupForm" class="hidden">''',
"forgot-password link",
)

rep(
'''  <div class="note" style="margin-bottom:14px">Para crear tu cuenta necesitás una <b>chapita ya activada</b> y su PIN privado. Esto evita que otra persona se apropie del perfil.</div>
  <div class="split"><div class="field"><label>Código de chapita</label><input name="code" value="${esc(pre)}" maxlength="12" placeholder="7B958A9D" required></div><div class="field"><label>PIN privado</label><input name="pin" maxlength="50" placeholder="0000-0000" required></div></div>
  <div class="field"><label>Email</label><input name="email" type="email" autocomplete="email" required></div>
  <div class="field"><label>Elegí una contraseña</label><input name="password" type="password" autocomplete="new-password" minlength="8" required></div>
  <button class="btn primary wide" type="submit">Crear mi cuenta y vincular mascota</button>''',
'''  <div class="note" style="margin-bottom:14px">Primero creás tu cuenta y verificás tu email. Después te vamos a pedir el <b>PIN privado</b> de la chapita para vincular la mascota. Así evitamos dejar una mascota asociada a un correo mal escrito.</div>
  <div class="field"><label>Código de chapita</label><input name="code" value="${esc(pre)}" maxlength="12" placeholder="7B958A9D" required></div>
  <div class="field"><label>Email</label><input name="email" type="email" autocomplete="email" required></div>
  <div class="field"><label>Elegí una contraseña</label><input name="password" type="password" autocomplete="new-password" minlength="8" required></div>
  <button class="btn primary wide" type="submit">Crear cuenta y verificar email</button>''',
"signup form",
)

rep(
''' sf.addEventListener("submit",async e=>{e.preventDefault();const b=e.submitter,bak=b.textContent,f=new FormData(e.currentTarget),mail=String(f.get("email")),pass=String(f.get("password"));b.disabled=true;b.textContent="Creando cuenta…";try{await accountPost({action:"register_owner",public_code:f.get("code"),activation_code:f.get("pin"),email:mail,password:pass},false);await login(mail,pass);history.replaceState({},document.title,"/mi-cuenta/");await loadDashboard();toast("Cuenta creada. Tu mascota ya está vinculada ✅")}catch(err){toast(err.message)}finally{b.disabled=false;b.textContent=bak}});''',
''' sf.addEventListener("submit",async e=>{e.preventDefault();const b=e.submitter,bak=b.textContent,f=new FormData(e.currentTarget),mail=String(f.get("email")||"").trim(),pass=String(f.get("password")||""),petCode=String(f.get("code")||"").trim().toUpperCase().replace(/[^A-Z0-9]/g,"").slice(0,12);if(!petCode){toast("Ingresá el código de la chapita.");return}b.disabled=true;b.textContent="Enviando verificación…";try{const redirect="https://patas-a-casa.vercel.app/mi-cuenta/confirmar/";const created=await authPost("/signup?redirect_to="+encodeURIComponent(redirect),{email:mail,password:pass,data:{source:"patas-a-casa",first_pet_code:petCode}});const u=created?.user||created;if(Array.isArray(u?.identities)&&u.identities.length===0)throw new Error("Ese email ya tiene una cuenta. Iniciá sesión o recuperá tu contraseña.");root.innerHTML=`<section class="card hero"><div class="kicker">VERIFICÁ TU EMAIL</div><h1>Revisá tu correo.</h1><p class="muted">Te enviamos un enlace a <b>${esc(mail)}</b>. Abrilo para confirmar que el correo es tuyo.</p><div class="note" style="margin-top:16px">Después de verificarlo, Patas a Casa te va a pedir el PIN privado de la chapita <b>${esc(petCode)}</b> para terminar de vincular la mascota.</div><p class="small muted" style="margin-top:14px">Si no lo ves, revisá Spam. El enlace puede tardar unos segundos.</p><button class="btn soft wide" style="margin-top:10px" onclick="showAuth()">Volver</button></section>`}catch(err){toast(err.message)}finally{b.disabled=false;b.textContent=bak}});''',
"signup handler",
)

rep(
'''async function loadDashboard(){
 root.innerHTML='<section class="card loading">Cargando tus mascotas…</section>';
 try{const d=await accountPost({action:"list_my_pets"});pets=d.pets||[];currentUser=d.user;renderDashboard()}catch(err){if(getSession())root.innerHTML=`<section class="card"><h2>No pudimos cargar tu cuenta</h2><p class="muted">${esc(err.message)}</p><button class="btn soft" onclick="loadDashboard()">Reintentar</button></section>`}
}''',
'''async function loadDashboard(){
 root.innerHTML='<section class="card loading">Cargando tus mascotas…</section>';
 try{const d=await accountPost({action:"list_my_pets"});pets=d.pets||[];currentUser=d.user;renderDashboard();const q=new URLSearchParams(location.search),pending=q.get("vincular")||"",confirmed=q.get("confirmado")==="1";if(pending){history.replaceState({},document.title,"/mi-cuenta/");setTimeout(()=>{if(confirmed)toast("Correo verificado ✅ Ahora ingresá el PIN de tu chapita.");openClaim(pending)},120)}}catch(err){if(getSession())root.innerHTML=`<section class="card"><h2>No pudimos cargar tu cuenta</h2><p class="muted">${esc(err.message)}</p><button class="btn soft" onclick="loadDashboard()">Reintentar</button></section>`}
}''',
"dashboard confirmation handoff",
)

rep('''function openClaim(){''', '''function openClaim(prefill=""){''', "claim function signature")
rep(
'''<input name="code" maxlength="12" required></div><div class="field"><label>PIN privado</label>''',
'''<input name="code" value="${esc(prefill)}" maxlength="12" required></div><div class="field"><label>PIN privado</label>''',
"claim code prefill",
)

page.write_text(s, encoding="utf-8")

confirm = Path("mi-cuenta/confirmar/index.html")
confirm.parent.mkdir(parents=True, exist_ok=True)
confirm.write_text(r'''<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#171719">
<title>Verificar email · Patas a Casa</title>
<style>
:root{--bg:#f4f4f1;--card:#fff;--ink:#171719;--muted:#737373;--line:#e7e6e1;--orange:#ff6a36;--orange2:#ff8c65;--green:#177346;--red:#a92f3b;--shadow:0 18px 55px rgba(20,20,20,.08);--r:26px}*{box-sizing:border-box}html{background:var(--bg)}body{margin:0;color:var(--ink);font-family:Inter,system-ui,-apple-system,"Segoe UI",sans-serif;background:radial-gradient(circle at 50% -10%,#fff 0,#f7f7f4 38%,#f2f2ef 100%);min-height:100vh}.app{max-width:620px;margin:auto;padding:18px 15px 70px}header{display:flex;align-items:center;gap:10px;margin:3px 2px 20px;font-weight:950;letter-spacing:-.03em}.logo{width:43px;height:43px;border-radius:15px;background:#171719;display:grid;place-items:center;color:#fff}.small{font-size:12px}.muted{color:var(--muted)}.card{background:rgba(255,255,255,.98);border:1px solid var(--line);border-radius:var(--r);padding:24px;box-shadow:var(--shadow)}.kicker{font-size:11px;letter-spacing:.08em;font-weight:950;color:#ce4d20}h1{font-size:36px;line-height:1.02;letter-spacing:-.055em;margin:10px 0 12px}p{line-height:1.5}.status{padding:12px 14px;border-radius:15px;font-size:13px;margin-top:14px;line-height:1.45}.ok{background:#ebf8f0;color:var(--green)}.err{background:#fff0f1;color:var(--red)}
</style>
</head>
<body>
<div class="app"><header><div class="logo">🐾</div><div>Patas a Casa<div class="small muted">Verificación de cuenta</div></div></header><main><section class="card"><div class="kicker">VERIFICANDO EMAIL</div><h1 id="title">Un segundo…</h1><p class="muted" id="text">Estamos confirmando tu correo y preparando tu cuenta.</p><div id="status"></div></section></main></div>
<script>
const SUPABASE_URL="https://cgciwutqwnssdphugupq.supabase.co";
const PUBLISHABLE_KEY="sb_publishable_oozsLV8QMoy_ooLIqgh_qg_vvjV6IY5";
const SESSION_KEY="pac_owner_session_v1";
const hash=new URLSearchParams(location.hash.replace(/^#/,""));
const access=hash.get("access_token")||"",refresh=hash.get("refresh_token")||"",err=hash.get("error_description")||hash.get("error")||"";
const title=document.getElementById("title"),text=document.getElementById("text"),status=document.getElementById("status");
function fail(m){title.textContent="No pudimos verificar el correo.";text.textContent="El enlace puede haber vencido o ya haber sido usado.";status.innerHTML=`<div class="status err">${m||"Pedí un nuevo correo de verificación e intentá otra vez."}</div>`}
(async()=>{if(err){fail(err);return}if(!access||!refresh){fail("El enlace de verificación no contiene una sesión válida.");return}try{const r=await fetch(SUPABASE_URL+"/auth/v1/user",{headers:{apikey:PUBLISHABLE_KEY,Authorization:"Bearer "+access}});const user=await r.json();if(!r.ok||!user?.id)throw new Error("No pudimos validar la cuenta.");const expiresIn=Number(hash.get("expires_in")||3600);localStorage.setItem(SESSION_KEY,JSON.stringify({access_token:access,refresh_token:refresh,token_type:hash.get("token_type")||"bearer",expires_in:expiresIn,expires_at:Math.floor(Date.now()/1000)+expiresIn,user}));const code=String(user?.user_metadata?.first_pet_code||"").trim().toUpperCase().replace(/[^A-Z0-9]/g,"").slice(0,12);history.replaceState({},document.title,location.pathname);title.textContent="Email verificado ✅";text.textContent="Ahora falta vincular tu chapita con el PIN privado.";status.innerHTML='<div class="status ok">Tu cuenta ya está confirmada. Te llevamos a Mi cuenta…</div>';setTimeout(()=>location.replace("/mi-cuenta/?confirmado=1"+(code?"&vincular="+encodeURIComponent(code):"")),900)}catch(e){fail(e.message)}})();
</script>
</body>
</html>
''', encoding="utf-8")

print("Email verification patch applied")

from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected 1 occurrence, found {count}")
    return text.replace(old, new, 1)

# Public QR page
path = Path("index.html")
text = path.read_text(encoding="utf-8")

text = replace_once(
    text,
    'const REGISTER_API=SUPABASE_URL+"/functions/v1/patas-register-v2";\n',
    'const REGISTER_API=SUPABASE_URL+"/functions/v1/patas-register-v2";\nconst EMAIL_ACTIVATION_API=SUPABASE_URL+"/functions/v1/patas-email-activation";\n',
    "root constant",
)

text = replace_once(
    text,
    'async function registerPost(data){const r=await fetch(REGISTER_API,{method:"POST",headers:{"Content-Type":"application/json","apikey":PUBLISHABLE_KEY},body:JSON.stringify(data)});const j=await r.json().catch(()=>({}));if(!r.ok)throw new Error(j.error||"No pudimos configurar el correo");return j}\n',
    'async function registerPost(data){const r=await fetch(REGISTER_API,{method:"POST",headers:{"Content-Type":"application/json","apikey":PUBLISHABLE_KEY},body:JSON.stringify(data)});const j=await r.json().catch(()=>({}));if(!r.ok)throw new Error(j.error||"No pudimos configurar el correo");return j}\nasync function emailActivationPost(data){const r=await fetch(EMAIL_ACTIVATION_API,{method:"POST",headers:{"Content-Type":"application/json","apikey":PUBLISHABLE_KEY},body:JSON.stringify(data)});const j=await r.json().catch(()=>({}));if(!r.ok)throw new Error(j.error||"No pudimos preparar la activación");return j}\nasync function emailActivationMode(c){const r=await fetch(EMAIL_ACTIVATION_API+"?action=mode&code="+encodeURIComponent(c),{headers:{apikey:PUBLISHABLE_KEY},cache:"no-store"});if(!r.ok)throw new Error("No pudimos comprobar el método de activación");const j=await r.json();return j?.email_activation===true}\n',
    "root email helpers",
)

text = replace_once(
    text,
    'function accountSetupForm(c,pin){\n root.innerHTML=`<section class="card hero">',
    'function accountSetupForm(c,pin,method="pin"){\n const emailMode=method==="email";\n root.innerHTML=`<section class="card hero">',
    "root account setup signature",
)

text = replace_once(
    text,
    '   <p class="muted">Antes de crear el perfil, elegí el correo y la contraseña con los que vas a administrarlo.</p>',
    '   <p class="muted">${emailMode?"No necesitás un PIN. Verificamos tu correo para vincular esta chapita de forma segura.":"Antes de crear el perfil, elegí el correo y la contraseña con los que vas a administrarlo."}</p>',
    "root account setup intro",
)

text = replace_once(
    text,
    '   <div class="note" style="margin-bottom:14px"><b>Chapita ${esc(c)} verificada ✅</b><br>No tenés que ingresar el código ni el PIN otra vez.</div>\n   <div class="hidden" id="googleActivationOptions">',
    '   <div class="note" style="margin-bottom:14px"><b>Chapita ${esc(c)} ${emailMode?"lista para vincular":"verificada"} ✅</b><br>${emailMode?"El QR de esta chapita reemplaza al PIN impreso.":"No tenés que ingresar el código ni el PIN otra vez."}</div>\n   <div class="hidden" id="googleActivationOptions">',
    "root verification note",
)

text = replace_once(
    text,
    '    <div class="auth-divider">o creá tu acceso con email</div>\n   </div>\n   <form id="accountSetup" method="post">',
    '    <div class="auth-divider">o</div>\n   </div>\n   ${emailMode?`<button class="btn soft" id="existingActivationAccount" type="button" style="margin-bottom:10px">Ya tengo cuenta</button><div class="auth-divider">o creá una cuenta nueva</div>`:""}\n   <form id="accountSetup" method="post">',
    "root existing account button",
)

text = replace_once(
    text,
    '   sessionStorage.setItem(GOOGLE_PENDING_KEY,JSON.stringify({public_code:c,activation_code:pin,created_at:Date.now()}));\n   location.assign("/mi-cuenta/?google=1");',
    '   sessionStorage.setItem(GOOGLE_PENDING_KEY,JSON.stringify({public_code:c,activation_code:emailMode?"":pin,activation_method:emailMode?"email":"pin",created_at:Date.now()}));\n   location.assign("/mi-cuenta/?google=1");',
    "root google pending",
)

text = replace_once(
    text,
    ' document.getElementById("accountSetup").addEventListener("submit",async e=>{',
    ' document.getElementById("existingActivationAccount")?.addEventListener("click",()=>{sessionStorage.setItem(GOOGLE_PENDING_KEY,JSON.stringify({public_code:c,activation_code:"",activation_method:"email",created_at:Date.now()}));location.assign("/mi-cuenta/")});\n document.getElementById("accountSetup").addEventListener("submit",async e=>{',
    "root existing account handler",
)

text = replace_once(
    text,
    '   try{localStorage.setItem("pac_legal_consent",JSON.stringify({version:"2026-08-28",accepted_at:new Date().toISOString()}));await registerPost({action:"start_registration",public_code:c,activation_code:pin,email:mail,password,legal_consent:true,legal_version:"2026-08-28"});activationComplete(mail)}',
    '   try{localStorage.setItem("pac_legal_consent",JSON.stringify({version:"2026-08-28",accepted_at:new Date().toISOString()}));const payload={action:"start_registration",public_code:c,email:mail,password,legal_consent:true,legal_version:"2026-08-28"};if(emailMode)await emailActivationPost(payload);else await registerPost({...payload,activation_code:pin});activationComplete(mail)}',
    "root registration branch",
)

text = replace_once(
    text,
    ' try{const data=await getTag(code);if(data.state==="unactivated")unactivated(code);else{const lostInfo=await getLostInfo(code).catch(()=>null);active(code,{...data.pet,...(lostInfo||{})})}}',
    ' try{const data=await getTag(code);if(data.state==="unactivated"){const emailMode=await emailActivationMode(code).catch(()=>false);if(emailMode)accountSetupForm(code,"","email");else unactivated(code)}else{const lostInfo=await getLostInfo(code).catch(()=>null);active(code,{...data.pet,...(lostInfo||{})})}}',
    "root boot method switch",
)

path.write_text(text, encoding="utf-8")

# Private account page
path = Path("mi-cuenta/index.html")
text = path.read_text(encoding="utf-8")

text = replace_once(
    text,
    'const REGISTER_API=SUPABASE_URL+"/functions/v1/patas-register-v2";\n',
    'const REGISTER_API=SUPABASE_URL+"/functions/v1/patas-register-v2";\nconst EMAIL_ACTIVATION_API=SUPABASE_URL+"/functions/v1/patas-email-activation";\n',
    "account constant",
)

old_queue = '''function queueGoogleActivation(publicCode,activationCode){
 const c=String(publicCode||"").trim().toUpperCase().replace(/[^A-Z0-9]/g,"").slice(0,12),pin=String(activationCode||"").replace(/\\D/g,"").slice(0,8);
 if(!c)throw new Error("Ingresá el código de la chapita.");
 if(!/^\\d{8}$/.test(pin))throw new Error("Ingresá los 8 números del PIN.");
 const pending={public_code:c,activation_code:pin,created_at:Date.now()};sessionStorage.setItem(GOOGLE_PENDING_KEY,JSON.stringify(pending));return pending;
}
function pendingGoogleActivation(){
 try{const pending=JSON.parse(sessionStorage.getItem(GOOGLE_PENDING_KEY)||"null");if(!pending||Date.now()-Number(pending.created_at)>15*60*1000){sessionStorage.removeItem(GOOGLE_PENDING_KEY);return null}return pending}catch{sessionStorage.removeItem(GOOGLE_PENDING_KEY);return null}
}
'''
new_queue = '''function queueGoogleActivation(publicCode,activationCode="",activationMethod="pin"){
 const c=String(publicCode||"").trim().toUpperCase().replace(/[^A-Z0-9]/g,"").slice(0,12),pin=String(activationCode||"").replace(/\\D/g,"").slice(0,8),method=activationMethod==="email"?"email":"pin";
 if(!c)throw new Error("Ingresá el código de la chapita.");
 if(method==="pin"&&!/^\\d{8}$/.test(pin))throw new Error("Ingresá los 8 números del PIN.");
 const pending={public_code:c,activation_code:method==="email"?"":pin,activation_method:method,created_at:Date.now()};sessionStorage.setItem(GOOGLE_PENDING_KEY,JSON.stringify(pending));return pending;
}
function pendingGoogleActivation(){
 try{const pending=JSON.parse(sessionStorage.getItem(GOOGLE_PENDING_KEY)||"null");if(!pending||Date.now()-Number(pending.created_at)>15*60*1000){sessionStorage.removeItem(GOOGLE_PENDING_KEY);return null}pending.activation_method=pending.activation_method==="email"?"email":"pin";return pending}catch{sessionStorage.removeItem(GOOGLE_PENDING_KEY);return null}
}
'''
text = replace_once(text, old_queue, new_queue, "account pending queue")

text = replace_once(
    text,
    ' if(pending)queueGoogleActivation(pending.public_code,pending.activation_code);',
    ' if(pending)queueGoogleActivation(pending.public_code,pending.activation_code,pending.activation_method);',
    "account start google",
)

text = replace_once(
    text,
    'async function accountPost(data,requiresAuth=true){let s=requiresAuth?await validSession():null;const h={"Content-Type":"application/json","apikey":PUBLISHABLE_KEY};if(s?.access_token)h.Authorization="Bearer "+s.access_token;const r=await fetch(ACCOUNT_API,{method:"POST",headers:h,body:JSON.stringify(data)});const j=await r.json().catch(()=>({}));if(r.status===401&&requiresAuth){setSession(null);showAuth("Tu sesión venció. Volvé a ingresar.");throw new Error("Sesión vencida.")}if(!r.ok)throw new Error(j.error||"Ocurrió un error.");return j}\n',
    'async function accountPost(data,requiresAuth=true){let s=requiresAuth?await validSession():null;const h={"Content-Type":"application/json","apikey":PUBLISHABLE_KEY};if(s?.access_token)h.Authorization="Bearer "+s.access_token;const r=await fetch(ACCOUNT_API,{method:"POST",headers:h,body:JSON.stringify(data)});const j=await r.json().catch(()=>({}));if(r.status===401&&requiresAuth){setSession(null);showAuth("Tu sesión venció. Volvé a ingresar.");throw new Error("Sesión vencida.")}if(!r.ok)throw new Error(j.error||"Ocurrió un error.");return j}\nasync function emailActivationPost(data){let s=await validSession();if(!s)throw new Error("Sesión vencida.");const h={"Content-Type":"application/json","apikey":PUBLISHABLE_KEY,"Authorization":"Bearer "+s.access_token};const r=await fetch(EMAIL_ACTIVATION_API,{method:"POST",headers:h,body:JSON.stringify(data)});const j=await r.json().catch(()=>({}));if(r.status===401){setSession(null);showAuth("Tu sesión venció. Volvé a ingresar.");throw new Error("Sesión vencida.")}if(!r.ok)throw new Error(j.error||"No pudimos preparar la activación.");return j}\nasync function prepareQueuedActivation(pending){if(!pending)return null;if(pending.activation_method==="email")return await emailActivationPost({action:"prepare_activation",public_code:pending.public_code});return await accountPost({action:"prepare_activation",public_code:pending.public_code,activation_code:pending.activation_code})}\n',
    "account email helper",
)

text = replace_once(
    text,
    'try{await login(f.get("email"),f.get("password"));let fin=null;',
    'try{await login(f.get("email"),f.get("password"));const queued=pendingGoogleActivation();if(queued){const claim=await prepareQueuedActivation(queued);clearGoogleActivation();if(claim?.profile_required&&claim?.public_code){history.replaceState({},document.title,"/mi-cuenta/?completar="+encodeURIComponent(claim.public_code));showActivationProfile(claim.public_code);return}}let fin=null;',
    "account login queued activation",
)

text = replace_once(
    text,
    '  try{const claim=await accountPost({action:"prepare_activation",public_code:googlePending.public_code,activation_code:googlePending.activation_code});clearGoogleActivation();if(claim?.profile_required){history.replaceState({},document.title,"/mi-cuenta/?completar="+encodeURIComponent(googlePending.public_code));showActivationProfile(googlePending.public_code);return}}',
    '  try{const claim=await prepareQueuedActivation(googlePending);clearGoogleActivation();if(claim?.profile_required){history.replaceState({},document.title,"/mi-cuenta/?completar="+encodeURIComponent(claim.public_code||googlePending.public_code));showActivationProfile(claim.public_code||googlePending.public_code);return}}',
    "account boot queued activation",
)

path.write_text(text, encoding="utf-8")

print("Email activation frontend patch applied")

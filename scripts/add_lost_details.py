from pathlib import Path
import re


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"No encontré el bloque esperado: {label}")
    return text.replace(old, new, 1)


# ---------------------------
# Panel del responsable
# ---------------------------
account_path = Path("mi-cuenta/index.html")
account = account_path.read_text(encoding="utf-8")

account = replace_once(
    account,
    'const ACCOUNT_API=SUPABASE_URL+"/functions/v1/patas-account";',
    'const ACCOUNT_API=SUPABASE_URL+"/functions/v1/patas-account";\nconst LOST_API=SUPABASE_URL+"/functions/v1/patas-lost";',
    "LOST_API en mi-cuenta",
)

account = account.replace(
    '<button class="btn soft" onclick="showSightings(\'${esc(p.public_code)}\')">📍 Avistamientos</button>',
    '',
    1,
)

new_toggle = r'''async function lostPost(data){
 let s=await validSession();if(!s)throw new Error("Sesión vencida.");
 const h={"Content-Type":"application/json","apikey":PUBLISHABLE_KEY,"Authorization":"Bearer "+s.access_token};
 const r=await fetch(LOST_API,{method:"POST",headers:h,body:JSON.stringify(data)});const j=await r.json().catch(()=>({}));
 if(r.status===401){setSession(null);showAuth("Tu sesión venció. Volvé a ingresar.");throw new Error("Sesión vencida.")}
 if(!r.ok)throw new Error(j.error||"No pudimos cambiar el estado.");return j
}
function localDateTimeValue(d=new Date()){
 const pad=n=>String(n).padStart(2,"0");return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}
async function toggleLost(c,status){
 const p=pets.find(x=>x.public_code===c);if(!p)return;
 if(status==="normal"){
   if(!confirm(`¿${p.name} ya volvió a casa? Se quitará la alerta pública.`))return;
   try{await lostPost({public_code:c,status:"normal"});await loadDashboard();toast("Marcado nuevamente en casa ✅")}catch(err){toast(err.message)}
   return
 }
 openModal(`<div class="sheethead"><div><div class="kicker">MARCAR COMO PERDIDO</div><h2>${esc(p.name)}</h2></div><button class="x" onclick="closeModal()">×</button></div>
 <p class="muted small">Estos datos aparecerán en el perfil público para que quien encuentre a ${esc(p.name)} sepa dónde y cuándo se perdió.</p>
 <form id="lostForm">
   <div class="field"><label>¿Dónde fue visto por última vez?</label><input name="lost_location" maxlength="160" placeholder="Ej. Parque General San Martín, cerca de los Portones" required></div>
   <div class="field"><label>Fecha y hora aproximada</label><input name="lost_at" type="datetime-local" value="${localDateTimeValue()}" required></div>
   <div class="field"><label>Detalles (opcional)</label><textarea name="lost_details" maxlength="700" placeholder="Ej. Se escapó con collar azul. Es amistoso pero puede estar asustado."></textarea></div>
   <button class="btn red wide" type="submit">🚨 Activar alerta de perdido</button>
 </form>`);
 document.getElementById("lostForm").addEventListener("submit",async e=>{
   e.preventDefault();const b=e.submitter,bak=b.textContent,f=new FormData(e.currentTarget),raw=String(f.get("lost_at")||""),when=new Date(raw);
   if(Number.isNaN(when.getTime())){toast("Ingresá una fecha y hora válidas.");return}
   b.disabled=true;b.textContent="Activando alerta…";
   try{await lostPost({public_code:c,status:"perdido",lost_location:f.get("lost_location"),lost_at:when.toISOString(),lost_details:f.get("lost_details")});closeModal();await loadDashboard();toast("Alerta de perdido activada 🚨")}
   catch(err){toast(err.message)}finally{b.disabled=false;b.textContent=bak}
 });
}
async function showSightings'''

account, n = re.subn(
    r'async function toggleLost\(c,status\)\{.*?\}\nasync function showSightings',
    new_toggle,
    account,
    count=1,
    flags=re.S,
)
if n != 1:
    raise SystemExit("No pude reemplazar toggleLost")

account_path.write_text(account, encoding="utf-8")


# ---------------------------
# Perfil público
# ---------------------------
public_path = Path("index.html")
public = public_path.read_text(encoding="utf-8")

public = replace_once(
    public,
    'const API="https://cgciwutqwnssdphugupq.supabase.co/functions/v1/patas-api";',
    'const API="https://cgciwutqwnssdphugupq.supabase.co/functions/v1/patas-api";\nconst LOST_API="https://cgciwutqwnssdphugupq.supabase.co/functions/v1/patas-lost";',
    "LOST_API público",
)

public = replace_once(
    public,
    'function wa(v=""){return String(v??"").replace(/\\D/g,"")}',
    'function wa(v=""){return String(v??"").replace(/\\D/g,"")}\nfunction formatLostDateTime(v){const d=new Date(v);if(Number.isNaN(d.getTime()))return "";return new Intl.DateTimeFormat("es-AR",{dateStyle:"medium",timeStyle:"short"}).format(d)}',
    "formateador de fecha perdida",
)

public = replace_once(
    public,
    'async function getTag(c){const r=await fetch(API+"?action=tag&code="+encodeURIComponent(c));const j=await r.json();if(!r.ok)throw new Error(j.error||"No pudimos abrir esta chapita");return j}',
    'async function getTag(c){const r=await fetch(API+"?action=tag&code="+encodeURIComponent(c));const j=await r.json();if(!r.ok)throw new Error(j.error||"No pudimos abrir esta chapita");return j}\nasync function getLostInfo(c){const r=await fetch(LOST_API+"?code="+encodeURIComponent(c),{cache:"no-store"});const j=await r.json();if(!r.ok)throw new Error(j.error||"No pudimos cargar los datos de pérdida");return j}',
    "getLostInfo",
)

public = replace_once(
    public,
    ' const lost=p.status==="perdido",phone=tel(p.contact_phone),whats=wa(p.contact_whatsapp||p.contact_phone);',
    ' const lost=p.status==="perdido",phone=tel(p.contact_phone),whats=wa(p.contact_whatsapp||p.contact_phone);\n const lostWhen=p.lost_at?formatLostDateTime(p.lost_at):"";\n const lostCard=lost?`<div class="box warn"><strong>🚨 ${esc(p.name)} está perdido</strong>${p.lost_location?`<div style="margin-top:8px"><b>Última vez visto:</b> ${esc(p.lost_location)}</div>`:""}${lostWhen?`<div class="small muted" style="margin-top:4px">🕒 ${esc(lostWhen)}</div>`:""}${p.lost_details?`<div style="margin-top:9px">${esc(p.lost_details)}</div>`:""}<div class="small" style="margin-top:9px"><b>Si lo encontraste, contactá a su familia.</b></div></div>`:"";',
    "tarjeta de perdido",
)

public = replace_once(
    public,
    '   ${lost?`<div class="box warn"><strong>🚨 Está perdido</strong>Si lo encontraste, contactá a su familia o avisá dónde lo viste.</div>`:""}',
    '   ${lostCard}',
    "alerta pública vieja",
)

# Quitar del perfil público el formulario colaborativo de avistamientos.
public, n = re.subn(
    r'\n <section class="card"><h2>📍 ¿Encontraste a \$\{esc\(p\.name\)\}\?</h2>.*?\n <div class="owner">',
    '\n <div class="owner">',
    public,
    count=1,
    flags=re.S,
)
if n != 1:
    raise SystemExit("No pude quitar el formulario público de avistamientos")

# Quitar la lógica JS asociada al formulario eliminado.
public, n = re.subn(
    r'\n let cachedGeo=null;.*?\n document\.getElementById\("ownerBtn"\)',
    '\n document.getElementById("ownerBtn")',
    public,
    count=1,
    flags=re.S,
)
if n != 1:
    raise SystemExit("No pude quitar la lógica de avistamientos")

public = replace_once(
    public,
    'try{const data=await getTag(code);if(data.state==="unactivated")unactivated(code);else active(code,data.pet)}',
    'try{const data=await getTag(code);if(data.state==="unactivated")unactivated(code);else{const lostInfo=await getLostInfo(code).catch(()=>null);active(code,{...data.pet,...(lostInfo||{})})}}',
    "carga de lost info",
)

public_path.write_text(public, encoding="utf-8")

print("OK: agregado flujo de perdido con lugar, fecha/hora y detalles; avistamientos ocultos de la UI.")

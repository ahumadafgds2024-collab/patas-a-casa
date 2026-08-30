from pathlib import Path
import re, subprocess, tempfile

p=Path('mi-cuenta/index.html')
h=p.read_text(encoding='utf-8')

h=h.replace('const LOST_API=SUPABASE_URL+"/functions/v1/patas-lost";','const LOST_API=SUPABASE_URL+"/functions/v1/patas-lost";\nconst TAG_SCAN_API=SUPABASE_URL+"/functions/v1/patas-tag-scan";',1)
h=h.replace('let pets=[],deferredInstall=null,currentUser=null,flyerBlob=null,flyerObjectUrl=null,flyerFileName="";','let pets=[],deferredInstall=null,currentUser=null,flyerBlob=null,flyerObjectUrl=null,flyerFileName="",tagScanner=null,tagScanLocked=false,qrScannerLibPromise=null;',1)

needle='async function emailActivationPost(data){let s=await validSession();if(!s)throw new Error("Sesión vencida.");const h={"Content-Type":"application/json","apikey":PUBLISHABLE_KEY,"Authorization":"Bearer "+s.access_token};const r=await fetch(EMAIL_ACTIVATION_API,{method:"POST",headers:h,body:JSON.stringify(data)});const j=await r.json().catch(()=>({}));if(r.status===401){setSession(null);showAuth("Tu sesión venció. Volvé a ingresar.");throw new Error("Sesión vencida.")}if(!r.ok)throw new Error(j.error||"No pudimos preparar la activación.");return j}'
insert='''\nasync function tagScanPost(scan){let s=await validSession();if(!s)throw new Error("Sesión vencida.");const h={"Content-Type":"application/json","apikey":PUBLISHABLE_KEY,"Authorization":"Bearer "+s.access_token};const r=await fetch(TAG_SCAN_API,{method:"POST",headers:h,body:JSON.stringify({scan})});const j=await r.json().catch(()=>({}));if(r.status===401){setSession(null);showAuth("Tu sesión venció. Volvé a ingresar.");throw new Error("Sesión vencida.")}if(!r.ok)throw new Error(j.error||"No pudimos leer esa chapita.");return j}
function loadQrScannerLibrary(){
 if(window.Html5Qrcode)return Promise.resolve(window.Html5Qrcode);
 if(qrScannerLibPromise)return qrScannerLibPromise;
 const sources=["https://cdn.jsdelivr.net/npm/html5-qrcode@2.3.8/html5-qrcode.min.js","https://unpkg.com/html5-qrcode@2.3.8/html5-qrcode.min.js"];
 qrScannerLibPromise=new Promise((resolve,reject)=>{let i=0;const next=()=>{if(i>=sources.length){reject(new Error("No pudimos cargar el lector QR."));return}const s=document.createElement("script");s.src=sources[i++];s.async=true;s.onload=()=>window.Html5Qrcode?resolve(window.Html5Qrcode):next();s.onerror=()=>next();document.head.appendChild(s)};next()});
 return qrScannerLibPromise;
}
async function stopTagScanner(){const sc=tagScanner;tagScanner=null;tagScanLocked=false;if(!sc)return;try{await sc.stop()}catch{}try{sc.clear()}catch{}}
async function finishScannedTag(decodedText){
 if(tagScanLocked)return;tagScanLocked=true;
 try{
  const info=await tagScanPost(decodedText);await stopTagScanner();
  if(info.state==="already_mine"){closeModal();toast("Esta chapita ya está en tu cuenta ✅");return}
  if(info.state==="owned_by_other"){openModal(`<div class="sheethead"><div><div class="kicker">CHAPITA EN USO</div><h2>Esta chapita ya tiene responsable</h2></div><button class="x" onclick="closeModal()">×</button></div><p class="muted">No se puede agregar a otra cuenta.</p><button class="btn soft wide" onclick="closeModal()">Entendido</button>`);return}
  if(info.activation_method==="pin"){
   openPinClaim(info.public_code);return
  }
  if(info.state!=="fresh"){openModal(`<div class="sheethead"><h2>No podemos agregar esta chapita</h2><button class="x" onclick="closeModal()">×</button></div><p class="muted">La chapita ya fue activada o tiene un estado que necesita revisión.</p><button class="btn soft wide" onclick="closeModal()">Cerrar</button>`);return}
  const result=await emailActivationPost({action:"prepare_activation",public_code:info.public_code});closeModal();
  if(result?.profile_required){history.replaceState({},document.title,"/mi-cuenta/?completar="+encodeURIComponent(result.public_code||info.public_code));showActivationProfile(result.public_code||info.public_code);return}
  await loadDashboard();toast("Chapita agregada ✅")
 }catch(err){await stopTagScanner();openModal(`<div class="sheethead"><div><div class="kicker">NO PUDIMOS LEERLA</div><h2>Probá nuevamente</h2></div><button class="x" onclick="closeModal()">×</button></div><div class="status err">${esc(err.message)}</div><button class="btn primary wide" style="margin-top:12px" onclick="openQrScanner()">Volver a escanear</button><button class="btn soft wide" style="margin-top:9px" onclick="openPinClaim()">Mi chapita vino con PIN</button>`)}
}
async function openQrScanner(){
 await stopTagScanner();
 openModal(`<div class="sheethead"><div><div class="kicker">AGREGAR CHAPITA</div><h2>Escaneá el QR</h2></div><button class="x" onclick="closeModal()">×</button></div><p class="muted small">Apuntá la cámara al QR que está detrás de la chapita.</p><div id="qrReader" style="width:100%;min-height:260px;border-radius:18px;overflow:hidden;background:#111"></div><div id="qrReaderStatus" class="small muted" style="margin-top:10px">Preparando cámara…</div><button class="btn soft wide" type="button" style="margin-top:12px" onclick="openPinClaim()">¿Tu chapita vino con PIN?</button>`);
 try{await loadQrScannerLibrary();if(!document.getElementById("qrReader"))return;tagScanner=new Html5Qrcode("qrReader");tagScanLocked=false;await tagScanner.start({facingMode:"environment"},{fps:10,qrbox:{width:220,height:220},aspectRatio:1},txt=>finishScannedTag(txt),()=>{});const st=document.getElementById("qrReaderStatus");if(st)st.textContent="Buscando QR…"}
 catch(err){await stopTagScanner();const st=document.getElementById("qrReaderStatus");if(st)st.innerHTML=`<span style="color:#a93442">No pudimos abrir la cámara. Revisá el permiso de cámara o usá el PIN si tu chapita lo incluye.</span>`}
}
function openClaim(){
 openModal(`<div class="sheethead"><div><div class="kicker">NUEVA MASCOTA</div><h2>Agregar una chapita</h2></div><button class="x" onclick="closeModal()">×</button></div><p class="muted">Escaneá el QR que está detrás de la chapita. Patas a Casa detecta automáticamente si necesita PIN.</p><button class="btn primary wide" type="button" onclick="openQrScanner()">📷 Escanear QR</button><div style="height:1px;background:var(--line);margin:18px 0 14px"></div><div class="small muted" style="margin-bottom:8px;font-weight:850">CHAPITAS ANTERIORES</div><button class="btn soft wide" type="button" onclick="openPinClaim()">Ingresar PIN</button>`)
}
'''
if 'async function tagScanPost(' not in h:
    if needle not in h: raise SystemExit('No encontré emailActivationPost')
    h=h.replace(needle,needle+insert,1)

start=h.find('function openClaim(){',h.find('async function resolveTagCodeByPin'))
end=h.find('\nasync function lostPost(data){',start)
if start<0 or end<0: raise SystemExit('No encontré bloque openClaim')
old=h[start:end]
new='''function openPinClaim(knownCode=""){
 openModal(`<div class="sheethead"><div><div class="kicker">CHAPITA CON PIN</div><h2>Ingresá el PIN</h2></div><button class="x" onclick="closeModal()">×</button></div><p class="muted small">Ingresá los 8 números del PIN privado que vino con esta chapita.</p><form id="claimForm" method="post"><div class="field"><label>PIN privado</label><input name="pin" inputmode="numeric" autocomplete="one-time-code" maxlength="8" pattern="[0-9]{8}" data-pin placeholder="00000000" required><div class="small muted" style="margin-top:6px">Poné los 8 números del PIN.</div></div><button class="btn primary wide" type="submit">Continuar</button></form>`);
 document.getElementById("claimForm").addEventListener("submit",async e=>{e.preventDefault();const b=e.submitter,bak=b.textContent,f=new FormData(e.currentTarget),pin=String(f.get("pin")||"").replace(/\\D/g,"").slice(0,8);b.disabled=true;b.textContent="Verificando…";try{const c=knownCode||await resolveTagCodeByPin(pin);const result=await accountPost({action:"prepare_activation",public_code:c,activation_code:pin});closeModal();if(result.profile_required&&result.public_code){history.replaceState({},document.title,"/mi-cuenta/?completar="+encodeURIComponent(result.public_code));showActivationProfile(result.public_code);return}await loadDashboard();toast(result.already?"Esta chapita ya está en tu cuenta ✅":"Chapita agregada ✅")}catch(err){toast(err.message)}finally{if(document.body.contains(b)){b.disabled=false;b.textContent=bak}}});
}'''
h=h[:start]+new+h[end:]

old_close='function closeModal(){if(flyerObjectUrl){URL.revokeObjectURL(flyerObjectUrl);flyerObjectUrl=null}flyerBlob=null;flyerFileName="";modal.classList.add("hidden");modal.innerHTML=""}'
new_close='function closeModal(){stopTagScanner();if(flyerObjectUrl){URL.revokeObjectURL(flyerObjectUrl);flyerObjectUrl=null}flyerBlob=null;flyerFileName="";modal.classList.add("hidden");modal.innerHTML=""}'
if old_close not in h: raise SystemExit('No encontré closeModal')
h=h.replace(old_close,new_close,1)

scripts=re.findall(r'<script(?![^>]*\\bsrc=)[^>]*>(.*?)</script>',h,flags=re.S|re.I)
for i,js in enumerate(scripts,1):
    if not js.strip(): continue
    with tempfile.NamedTemporaryFile('w',suffix='.js',delete=False,encoding='utf-8') as f:
        f.write(js); name=f.name
    r=subprocess.run(['node','--check',name],capture_output=True,text=True)
    if r.returncode: raise SystemExit(f'JS inválido script {i}: {r.stderr}')
for x in ['const TAG_SCAN_API=','function openQrScanner()','function openPinClaim(','function openClaim()','html5-qrcode@2.3.8','async function tagScanPost(']:
    if x not in h: raise SystemExit('Falta '+x)
p.write_text(h,encoding='utf-8')
print('QR scanner aplicado y JS validado')

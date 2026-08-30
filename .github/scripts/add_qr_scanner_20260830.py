from pathlib import Path
import re, subprocess, tempfile

p=Path('mi-cuenta/index.html')
h=p.read_text(encoding='utf-8')

start=h.find('async function openQrScanner(){')
end=h.find('\nfunction openClaim(){',start)
if start<0 or end<0:
    raise SystemExit('No encontré openQrScanner')

new='''function qrCameraErrorText(err){
 const text=String(err?.name||"")+" "+String(err?.message||err||"");
 if(/NotAllowedError|Permission denied|Permission dismissed|denied/i.test(text))return "Patas a Casa no tiene permiso para usar la cámara. Permití el acceso a la cámara y tocá Reintentar.";
 if(/NotReadableError|Could not start video source|TrackStartError/i.test(text))return "Android no pudo iniciar la cámara. Cerrá cualquier app que pueda estar usándola y probá nuevamente.";
 if(/NotFoundError|DevicesNotFoundError/i.test(text))return "No encontramos una cámara disponible en este dispositivo.";
 if(/OverconstrainedError|ConstraintNotSatisfiedError/i.test(text))return "No pudimos seleccionar la cámara trasera automáticamente.";
 if(/cargar el lector QR/i.test(text))return "No pudimos cargar el lector QR. Revisá la conexión y probá nuevamente.";
 return "No pudimos abrir la cámara en vivo. Podés reintentar o sacar una foto del QR.";
}
async function startTagCamera(){
 const config={fps:10,qrbox:{width:220,height:220},aspectRatio:1};
 const ok=txt=>finishScannedTag(txt),miss=()=>{};
 tagScanner=new Html5Qrcode("qrReader");tagScanLocked=false;
 try{await tagScanner.start({facingMode:"environment"},config,ok,miss);return}
 catch(firstErr){
  await stopTagScanner();
  try{
   const cameras=await Html5Qrcode.getCameras();
   if(!cameras?.length)throw firstErr;
   const rear=cameras.find(c=>/back|rear|environment|trasera|posterior/i.test(String(c.label||"")))||cameras[cameras.length-1];
   tagScanner=new Html5Qrcode("qrReader");tagScanLocked=false;
   await tagScanner.start(rear.id,config,ok,miss);return
  }catch(secondErr){await stopTagScanner();throw(secondErr||firstErr)}
 }
}
async function scanQrPhoto(input){
 const file=input?.files?.[0];if(!file)return;
 const st=document.getElementById("qrReaderStatus");if(st)st.textContent="Leyendo foto…";
 try{
  await stopTagScanner();await loadQrScannerLibrary();
  if(!document.getElementById("qrReader"))return;
  tagScanner=new Html5Qrcode("qrReader");tagScanLocked=false;
  const decoded=await tagScanner.scanFile(file,false);
  await finishScannedTag(decoded)
 }catch(err){
  await stopTagScanner();
  const status=document.getElementById("qrReaderStatus");if(status)status.innerHTML=`<span style="color:#a93442">No pudimos encontrar un QR en esa foto. Acercate un poco más y probá otra vez.</span>`;
  if(input)input.value=""
 }
}
async function openQrScanner(){
 await stopTagScanner();
 openModal(`<div class="sheethead"><div><div class="kicker">AGREGAR CHAPITA</div><h2>Escaneá el QR</h2></div><button class="x" onclick="closeModal()">×</button></div><p class="muted small">Apuntá la cámara al QR que está detrás de la chapita.</p><div id="qrReader" style="width:100%;min-height:260px;border-radius:18px;overflow:hidden;background:#111"></div><div id="qrReaderStatus" class="small muted" style="margin-top:10px">Preparando cámara…</div><input id="qrPhotoInput" type="file" accept="image/*" capture="environment" hidden><div id="qrCameraFallback" class="hidden" style="margin-top:12px"><button class="btn primary wide" type="button" id="qrRetryCamera">Reintentar cámara</button><button class="btn soft wide" type="button" id="qrTakePhoto" style="margin-top:9px">📷 Sacar foto del QR</button></div><button class="btn soft wide" type="button" style="margin-top:12px" onclick="openPinClaim()">¿Tu chapita vino con PIN?</button>`);
 const photo=document.getElementById("qrPhotoInput"),take=document.getElementById("qrTakePhoto"),retry=document.getElementById("qrRetryCamera");
 if(photo)photo.addEventListener("change",()=>scanQrPhoto(photo));
 if(take)take.addEventListener("click",()=>photo?.click());
 if(retry)retry.addEventListener("click",()=>openQrScanner());
 try{
  await loadQrScannerLibrary();if(!document.getElementById("qrReader"))return;
  await startTagCamera();const st=document.getElementById("qrReaderStatus");if(st)st.textContent="Buscando QR…"
 }catch(err){
  await stopTagScanner();
  const reader=document.getElementById("qrReader");if(reader){reader.style.display="none";reader.style.minHeight="0"}
  const st=document.getElementById("qrReaderStatus");if(st)st.innerHTML=`<span style="color:#a93442">${esc(qrCameraErrorText(err))}</span>`;
  document.getElementById("qrCameraFallback")?.classList.remove("hidden")
 }
}
'''

h=h[:start]+new+h[end:]

scripts=re.findall(r'<script(?![^>]*\\bsrc=)[^>]*>(.*?)</script>',h,flags=re.S|re.I)
for i,js in enumerate(scripts,1):
    if not js.strip(): continue
    with tempfile.NamedTemporaryFile('w',suffix='.js',delete=False,encoding='utf-8') as f:
        f.write(js); name=f.name
    r=subprocess.run(['node','--check',name],capture_output=True,text=True)
    if r.returncode: raise SystemExit(f'JS inválido script {i}: {r.stderr}')

for x in ['function qrCameraErrorText(','async function startTagCamera()','async function scanQrPhoto(','Sacar foto del QR','Html5Qrcode.getCameras()']:
    if x not in h: raise SystemExit('Falta '+x)

p.write_text(h,encoding='utf-8')
print('Fallback robusto de cámara QR aplicado y JS validado')

from pathlib import Path

path = Path("mi-cuenta/index.html")
text = path.read_text(encoding="utf-8")
start_marker = "async function showSharedActivationConfirmation(pending){"
end_marker = "\n\nasync function prepareQueuedActivation(pending)"
start = text.find(start_marker)
end = text.find(end_marker, start)
if start < 0 or end < 0:
    raise SystemExit("No se encontro el bloque showSharedActivationConfirmation")

new_block = r'''async function showSharedActivationConfirmation(pending){
 if(!pending?.public_code)return loadDashboard();
 let email=getSession()?.user?.email||currentUser?.email||"";
 if(!email){try{const d=await accountPost({action:"list_my_pets"});currentUser=d.user;email=d.user?.email||""}catch{}}
 document.getElementById("accountMenuBtn")?.classList.add("hidden");
 root.innerHTML=`<section class="card hero"><div class="kicker">NUEVA CHAPITA</div><h1>Chapita detectada 🐾</h1><p class="muted">El QR identifica la chapita <b>${esc(pending.public_code)}</b>.</p></section><section class="card"><div class="status ok" style="margin-bottom:14px"><b>Código de activación correcto ✅</b></div><h2>¿Con qué cuenta querés vincular esta chapita?</h2><div class="note"><b>Hay una cuenta abierta en este teléfono:</b><br>${esc(email||"tu cuenta actual")}</div><button class="btn primary wide" id="confirmSharedActivation" type="button" style="margin-top:14px">Vincular a esta cuenta</button><button class="btn soft wide" id="switchSharedAccount" type="button" style="margin-top:9px">Usar otro correo o crear otra cuenta</button><button class="btn soft wide" id="cancelSharedActivation" type="button" style="margin-top:9px">Cancelar activación</button></section>`;
 document.getElementById("confirmSharedActivation").onclick=async e=>{const b=e.currentTarget,bak=b.textContent;b.disabled=true;b.textContent="Vinculando…";try{const result=await prepareQueuedActivation(pending);clearGoogleActivation();if(result?.profile_required&&result?.public_code){history.replaceState({},document.title,"/mi-cuenta/?completar="+encodeURIComponent(result.public_code));showActivationProfile(result.public_code);return}history.replaceState({},document.title,"/mi-cuenta/");await loadDashboard();toast(result?.already?"Esta chapita ya está en tu cuenta ✅":"Chapita vinculada ✅")}catch(err){toast(err.message);b.disabled=false;b.textContent=bak}};
 document.getElementById("switchSharedAccount").onclick=async e=>{const b=e.currentTarget;b.disabled=true;b.textContent="Cambiando de cuenta…";const s=getSession();try{if(s?.access_token)await authPost("/logout",{},s.access_token)}catch{}setSession(null);currentUser=null;pets=[];clearIosSessionBridge();history.replaceState({},document.title,"/mi-cuenta/");showAuth()};
 document.getElementById("cancelSharedActivation").onclick=async()=>{clearGoogleActivation();history.replaceState({},document.title,"/mi-cuenta/");await loadDashboard()};
}'''

if "switchSharedAccount" in text[start:end]:
    print("Account choice already present")
else:
    path.write_text(text[:start] + new_block + text[end:], encoding="utf-8")
    print("Patched shared activation account choice")

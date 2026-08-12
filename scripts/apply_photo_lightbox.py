from pathlib import Path

path = Path('index.html')
s = path.read_text(encoding='utf-8')

if 'function openPhotoViewer(' in s:
    print('Photo viewer already present.')
    raise SystemExit(0)

css_needle = '.file-btn input{display:none}\n.petname'
css_repl = '''.file-btn input{display:none}\n.avatar.has-photo{cursor:zoom-in}\n.photo-lightbox{position:fixed;z-index:9999;inset:0;background:rgba(0,0,0,.92);display:flex;align-items:center;justify-content:center;padding:18px;animation:photoFadeIn .15s ease}\n.photo-lightbox img{max-width:100%;max-height:88vh;width:auto;height:auto;object-fit:contain;border-radius:18px;box-shadow:0 20px 80px rgba(0,0,0,.45)}\n.photo-lightbox-close{position:fixed;top:max(16px,env(safe-area-inset-top));right:16px;width:46px;height:46px;border:0;border-radius:50%;background:rgba(255,255,255,.15);color:#fff;font-size:30px;line-height:1;display:grid;place-items:center;cursor:pointer;backdrop-filter:blur(8px)}\n.photo-lightbox-hint{position:fixed;bottom:max(18px,env(safe-area-inset-bottom));left:50%;transform:translateX(-50%);color:rgba(255,255,255,.78);font-size:12px;white-space:nowrap}\n@keyframes photoFadeIn{from{opacity:0}to{opacity:1}}\n.petname'''
if css_needle not in s:
    raise SystemExit('CSS insertion point not found')
s = s.replace(css_needle, css_repl, 1)

fn_needle = 'function getCurrentLocation(){'
fn_repl = '''function openPhotoViewer(src,name=""){
 const old=document.getElementById("photoLightbox");if(old)old.remove();
 const overlay=document.createElement("div");overlay.id="photoLightbox";overlay.className="photo-lightbox";
 const img=document.createElement("img");img.src=src;img.alt="Foto ampliada de "+name;
 const closeBtn=document.createElement("button");closeBtn.type="button";closeBtn.className="photo-lightbox-close";closeBtn.setAttribute("aria-label","Cerrar foto");closeBtn.textContent="×";
 const hint=document.createElement("div");hint.className="photo-lightbox-hint";hint.textContent="Tocá afuera para cerrar";
 const onKey=e=>{if(e.key==="Escape")close()};
 const close=()=>{document.removeEventListener("keydown",onKey);document.body.style.overflow="";overlay.remove()};
 closeBtn.addEventListener("click",close);overlay.addEventListener("click",e=>{if(e.target===overlay)close()});document.addEventListener("keydown",onKey);
 overlay.append(img,closeBtn,hint);document.body.appendChild(overlay);document.body.style.overflow="hidden";
}
function getCurrentLocation(){'''
if fn_needle not in s:
    raise SystemExit('Function insertion point not found')
s = s.replace(fn_needle, fn_repl, 1)

avatar_needle = '<div class="petrow"><div class="avatar">${p.photo_url?`<img src="${esc(p.photo_url)}" alt="Foto de ${esc(p.name)}">`:p.species==="Gato"?"🐱":"🐶"}</div>'
avatar_repl = '<div class="petrow"><div class="avatar ${p.photo_url?"has-photo":""}">${p.photo_url?`<img src="${esc(p.photo_url)}" alt="Foto de ${esc(p.name)}">`:p.species==="Gato"?"🐱":"🐶"}</div>'
if avatar_needle not in s:
    raise SystemExit('Profile avatar markup not found')
s = s.replace(avatar_needle, avatar_repl, 1)

bind_needle = ' <div class="owner"><button id="ownerBtn">Soy el responsable de ${esc(p.name)}</button></div>`;\n let cachedGeo=null;'
bind_repl = ''' <div class="owner"><button id="ownerBtn">Soy el responsable de ${esc(p.name)}</button></div>`;
 if(p.photo_url){
   const petPhoto=document.querySelector(".avatar.has-photo");
   if(petPhoto){
     petPhoto.setAttribute("role","button");petPhoto.setAttribute("tabindex","0");petPhoto.setAttribute("aria-label","Ver foto grande de "+p.name);
     petPhoto.addEventListener("click",()=>openPhotoViewer(p.photo_url,p.name));
     petPhoto.addEventListener("keydown",e=>{if(e.key==="Enter"||e.key===" "){e.preventDefault();openPhotoViewer(p.photo_url,p.name)}});
   }
 }
 let cachedGeo=null;'''
if bind_needle not in s:
    raise SystemExit('Photo binding insertion point not found')
s = s.replace(bind_needle, bind_repl, 1)

path.write_text(s, encoding='utf-8')
print('Photo lightbox applied.')

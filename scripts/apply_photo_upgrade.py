from pathlib import Path
import re

path = Path('index.html')
s = path.read_text(encoding='utf-8')

if 'function compressPhoto(file)' in s:
    print('Photo upgrade already applied')
    raise SystemExit(0)

s = s.replace(
'.petrow{display:flex;align-items:center;gap:15px;margin-top:16px}.avatar{width:100px;height:100px;flex:0 0 100px;border-radius:26px;background:linear-gradient(145deg,#fff1e9,#ffe1d2);display:grid;place-items:center;font-size:49px}\n',
'.petrow{display:flex;align-items:center;gap:15px;margin-top:16px}.avatar{width:100px;height:100px;flex:0 0 100px;border-radius:26px;background:linear-gradient(145deg,#fff1e9,#ffe1d2);display:grid;place-items:center;font-size:49px;overflow:hidden}.avatar img{width:100%;height:100%;object-fit:cover;display:block}\n.photo-pick{display:flex;align-items:center;gap:14px;padding:13px;border:1px solid var(--line);border-radius:18px;background:#fafaf8;margin-bottom:16px}.photo-preview{width:92px;height:92px;flex:0 0 92px;border-radius:23px;background:linear-gradient(145deg,#fff1e9,#ffe1d2);display:grid;place-items:center;font-size:40px;overflow:hidden}.photo-preview img{width:100%;height:100%;object-fit:cover;display:block}.photo-actions{display:grid;gap:7px;flex:1}.file-btn{display:inline-flex;align-items:center;justify-content:center;gap:7px;border:1px solid #deded9;background:#fff;border-radius:13px;padding:10px 12px;font-size:12px;font-weight:900;cursor:pointer}.file-btn input{display:none}\n'
)

helper = r'''
function compressPhoto(file){
 return new Promise((resolve,reject)=>{
   if(!file){resolve(null);return}
   if(!file.type.startsWith("image/")){reject(new Error("Elegí una imagen válida."));return}
   if(file.size>12*1024*1024){reject(new Error("La foto original es demasiado grande."));return}
   const reader=new FileReader();
   reader.onerror=()=>reject(new Error("No pudimos leer la foto."));
   reader.onload=()=>{
     const img=new Image();
     img.onerror=()=>reject(new Error("No pudimos procesar esa foto. Probá con JPG o PNG."));
     img.onload=()=>{
       const max=900,scale=Math.min(1,max/Math.max(img.naturalWidth||img.width,img.naturalHeight||img.height));
       const w=Math.max(1,Math.round((img.naturalWidth||img.width)*scale)),h=Math.max(1,Math.round((img.naturalHeight||img.height)*scale));
       const canvas=document.createElement("canvas");canvas.width=w;canvas.height=h;
       const ctx=canvas.getContext("2d");ctx.fillStyle="#fff";ctx.fillRect(0,0,w,h);ctx.drawImage(img,0,0,w,h);
       resolve(canvas.toDataURL("image/jpeg",.82));
     };
     img.src=String(reader.result);
   };
   reader.readAsDataURL(file);
 });
}
function bindPhotoPreview(inputId,previewId){
 const input=document.getElementById(inputId),preview=document.getElementById(previewId);if(!input||!preview)return;
 input.addEventListener("change",()=>{
   const file=input.files?.[0];if(!file)return;
   const url=URL.createObjectURL(file);preview.innerHTML=`<img src="${url}" alt="Vista previa">`;
 });
}
'''
s = s.replace('async function getTag(c)', helper + '\nasync function getTag(c)')

activation = r'''function activationForm(c,pin){
 root.innerHTML=`<section class="card hero">
   <div class="kicker">ÚLTIMO PASO</div>
   <h1>¿Quién lleva esta chapita?</h1>
   <p class="muted">Cargá lo indispensable. La foto y los datos se pueden cambiar más adelante.</p>
   <div class="stepbar"><div class="step on"></div><div class="step on"></div></div>
 </section>
 <section class="card">
   <form id="activate">
     <div class="photo-pick"><div class="photo-preview" id="activationPhotoPreview">🐾</div><div class="photo-actions"><b>Foto de tu mascota</b><span class="small muted">Ayuda muchísimo a reconocerla rápido.</span><label class="file-btn">📷 Elegir foto<input id="activationPhoto" type="file" accept="image/jpeg,image/png,image/webp,image/*"></label></div></div>
     <div class="split"><div class="field"><label>Nombre de tu mascota</label><input name="name" placeholder="Rocco" maxlength="80" required></div><div class="field"><label>Especie</label><select name="species"><option>Perro</option><option>Gato</option><option>Otra</option></select></div></div>
     <div class="split"><div class="field"><label>Tu nombre</label><input name="contact_name" placeholder="Nombre del responsable" maxlength="80" required></div><div class="field"><label>WhatsApp / teléfono</label><input name="contact_whatsapp" inputmode="tel" placeholder="+54 9 261..." maxlength="40" required></div></div>
     <div class="split"><div class="field"><label>Raza</label><input name="breed" placeholder="Opcional" maxlength="80"></div><div class="field"><label>Edad</label><input name="age_text" placeholder="Ej. 4 años" maxlength="40"></div></div>
     <div class="split"><div class="field"><label>Sexo</label><select name="sex"><option value="">Sin informar</option><option>Macho</option><option>Hembra</option></select></div><div class="field"><label>Tamaño</label><select name="size"><option value="">Sin informar</option><option>Pequeño</option><option>Mediano</option><option>Grande</option></select></div></div>
     <div class="field"><label>Color / señas</label><input name="color" placeholder="Ej. Dorado, mancha blanca en el pecho" maxlength="80"></div>
     <details class="optional"><summary>❤️ Agregar salud y cuidados (opcional)</summary>
       <div class="field"><label>Enfermedades</label><textarea name="diseases" placeholder="Ej. Epilepsia"></textarea></div>
       <div class="field"><label>Medicamentos</label><textarea name="medications" placeholder="Nombre y dosis"></textarea></div>
       <div class="field"><label>Frecuencia</label><input name="medication_schedule" placeholder="Ej. Cada 12 horas"></div>
       <div class="field"><label>Alergias</label><textarea name="allergies"></textarea></div>
       <div class="field"><label>Cuidados especiales</label><textarea name="special_care"></textarea></div>
       <div class="field"><label>Veterinario / dato útil</label><textarea name="vet_info" placeholder="Opcional"></textarea></div>
     </details>
     <label class="check"><input name="public_health" type="checkbox" checked><div><b>Mostrar datos importantes de salud</b><div class="small muted">Sirve para que quien lo encuentre pueda cuidarlo correctamente.</div></div></label>
     <button class="btn primary" id="activateBtn" type="submit">Activar chapita</button>
   </form>
 </section>`;
 bindPhotoPreview("activationPhoto","activationPhotoPreview");
 document.getElementById("activate").addEventListener("submit",async e=>{
   e.preventDefault();const f=new FormData(e.currentTarget),o=Object.fromEntries(f.entries()),b=document.getElementById("activateBtn"),photo=document.getElementById("activationPhoto").files?.[0];
   o.action="activate";o.public_code=c;o.activation_code=pin;o.contact_phone=o.contact_whatsapp;o.public_health=f.get("public_health")==="on";o.public_contact=true;o.status="normal";
   b.disabled=true;
   try{if(photo){b.textContent="Preparando foto…";o.photo_data=await compressPhoto(photo)}b.textContent="Activando…";await post(o);toast("Chapita activada ✅");setTimeout(()=>location.href="?tag="+encodeURIComponent(c),500)}
   catch(err){toast(err.message);b.disabled=false;b.textContent="Activar chapita"}
 });
}

'''
s, n = re.subn(r'function activationForm\(c,pin\)\{.*?\n\}\n\n(?=function active\(c,p\)\{)', activation, s, flags=re.S)
assert n == 1, f'activation replacement count={n}'

old_health = 'const health=p.public_health&&(p.diseases||p.medications||p.allergies||p.special_care)?`<section class="card"><h2>❤️ Salud y cuidados</h2>${p.diseases?`<div class="box warn"><strong>Enfermedades</strong>${esc(p.diseases)}</div>`:""}${p.medications?`<div class="box"><strong>Medicación</strong>${esc(p.medications)}${p.medication_schedule?" · "+esc(p.medication_schedule):""}</div>`:""}${p.allergies?`<div class="box"><strong>Alergias</strong>${esc(p.allergies)}</div>`:""}${p.special_care?`<div class="box"><strong>Cuidados especiales</strong>${esc(p.special_care)}</div>`:""}</section>`:"";'
new_health = 'const health=p.public_health&&(p.diseases||p.medications||p.allergies||p.special_care||p.vet_info)?`<section class="card"><h2>❤️ Salud y cuidados</h2>${p.diseases?`<div class="box warn"><strong>Enfermedades</strong>${esc(p.diseases)}</div>`:""}${p.medications?`<div class="box"><strong>Medicación</strong>${esc(p.medications)}${p.medication_schedule?" · "+esc(p.medication_schedule):""}</div>`:""}${p.allergies?`<div class="box"><strong>Alergias</strong>${esc(p.allergies)}</div>`:""}${p.special_care?`<div class="box"><strong>Cuidados especiales</strong>${esc(p.special_care)}</div>`:""}${p.vet_info?`<div class="box"><strong>Veterinario / dato útil</strong>${esc(p.vet_info)}</div>`:""}</section>`:"";'
assert old_health in s
s = s.replace(old_health, new_health)

old_petrow = '<div class="petrow"><div class="avatar">${p.species==="Gato"?"🐱":"🐶"}</div><div><div class="petname">${esc(p.name)}</div><div class="meta">${esc(p.breed||p.species)}${p.sex?" · "+esc(p.sex):""}${p.age_text?" · "+esc(p.age_text):""}</div><div class="chips">${p.color?`<span class="chip">${esc(p.color)}</span>`:""}</div></div></div>'
new_petrow = '<div class="petrow"><div class="avatar">${p.photo_url?`<img src="${esc(p.photo_url)}" alt="Foto de ${esc(p.name)}">`:p.species==="Gato"?"🐱":"🐶"}</div><div><div class="petname">${esc(p.name)}</div><div class="meta">${esc(p.breed||p.species)}${p.sex?" · "+esc(p.sex):""}${p.age_text?" · "+esc(p.age_text):""}</div><div class="chips">${p.size?`<span class="chip">${esc(p.size)}</span>`:""}${p.color?`<span class="chip">${esc(p.color)}</span>`:""}</div></div></div>'
assert old_petrow in s
s = s.replace(old_petrow, new_petrow)

owner = r'''function ownerEdit(c,p){
 root.innerHTML=`<section class="card hero"><div class="kicker">RESPONSABLE</div><h1>Editá el perfil.</h1><p class="muted">Usá el PIN privado para cambiar la foto, los datos o marcar a tu mascota como perdida.</p></section>
 <section class="card"><form id="ownerForm">
 <div class="field"><label>PIN privado</label><input class="pin" name="activation_code" type="password" required></div>
 <div class="photo-pick"><div class="photo-preview" id="ownerPhotoPreview">${p.photo_url?`<img src="${esc(p.photo_url)}" alt="Foto actual">`:p.species==="Gato"?"🐱":"🐶"}</div><div class="photo-actions"><b>Foto de ${esc(p.name)}</b><span class="small muted">Podés reemplazarla cuando quieras.</span><label class="file-btn">📷 Cambiar foto<input id="ownerPhoto" type="file" accept="image/jpeg,image/png,image/webp,image/*"></label>${p.photo_url?`<label class="small"><input id="removePhoto" type="checkbox"> Quitar foto actual</label>`:""}</div></div>
 <div class="split"><div class="field"><label>Nombre</label><input name="name" value="${esc(p.name)}" required></div><div class="field"><label>Estado</label><select name="status"><option value="normal" ${p.status!=="perdido"?"selected":""}>Normal</option><option value="perdido" ${p.status==="perdido"?"selected":""}>🚨 Perdido</option></select></div></div>
 <div class="split"><div class="field"><label>Especie</label><select name="species"><option ${p.species==="Perro"?"selected":""}>Perro</option><option ${p.species==="Gato"?"selected":""}>Gato</option><option ${p.species!=="Perro"&&p.species!=="Gato"?"selected":""}>Otra</option></select></div><div class="field"><label>Raza</label><input name="breed" value="${esc(p.breed||"")}"></div></div>
 <div class="split"><div class="field"><label>Sexo</label><select name="sex"><option value="" ${!p.sex?"selected":""}>Sin informar</option><option ${p.sex==="Macho"?"selected":""}>Macho</option><option ${p.sex==="Hembra"?"selected":""}>Hembra</option></select></div><div class="field"><label>Edad</label><input name="age_text" value="${esc(p.age_text||"")}" placeholder="Ej. 4 años"></div></div>
 <div class="split"><div class="field"><label>Tamaño</label><select name="size"><option value="" ${!p.size?"selected":""}>Sin informar</option><option ${p.size==="Pequeño"?"selected":""}>Pequeño</option><option ${p.size==="Mediano"?"selected":""}>Mediano</option><option ${p.size==="Grande"?"selected":""}>Grande</option></select></div><div class="field"><label>Color / señas</label><input name="color" value="${esc(p.color||"")}"></div></div>
 <div class="split"><div class="field"><label>Responsable</label><input name="contact_name" value="${esc(p.contact_name||"")}"></div><div class="field"><label>WhatsApp / teléfono</label><input name="contact_whatsapp" inputmode="tel" value="${esc(p.contact_whatsapp||p.contact_phone||"")}"></div></div>
 <details class="optional" open><summary>❤️ Salud y cuidados</summary>
 <div class="field"><label>Enfermedades</label><textarea name="diseases">${esc(p.diseases||"")}</textarea></div><div class="field"><label>Medicamentos</label><textarea name="medications">${esc(p.medications||"")}</textarea></div><div class="field"><label>Frecuencia</label><input name="medication_schedule" value="${esc(p.medication_schedule||"")}"></div><div class="field"><label>Alergias</label><textarea name="allergies">${esc(p.allergies||"")}</textarea></div><div class="field"><label>Cuidados especiales</label><textarea name="special_care">${esc(p.special_care||"")}</textarea></div><div class="field"><label>Veterinario / dato útil</label><textarea name="vet_info">${esc(p.vet_info||"")}</textarea></div></details>
 <label class="check"><input name="public_health" type="checkbox" ${p.public_health?"checked":""}><div><b>Mostrar salud importante</b><div class="small muted">Sólo se muestra si está marcado.</div></div></label>
 <button id="saveOwner" class="btn primary" type="submit">Guardar cambios</button></form></section>`;
 bindPhotoPreview("ownerPhoto","ownerPhotoPreview");
 document.getElementById("ownerForm").addEventListener("submit",async e=>{
   e.preventDefault();const f=new FormData(e.currentTarget),o=Object.fromEntries(f.entries()),b=document.getElementById("saveOwner"),photo=document.getElementById("ownerPhoto").files?.[0];
   Object.assign(o,{action:"update_pet",public_code:c,contact_phone:o.contact_whatsapp,public_health:f.get("public_health")==="on",public_contact:true,remove_photo:Boolean(document.getElementById("removePhoto")?.checked)});
   b.disabled=true;
   try{if(photo){b.textContent="Preparando foto…";o.photo_data=await compressPhoto(photo);o.remove_photo=false}b.textContent="Guardando…";await post(o);toast("Cambios guardados ✅");setTimeout(()=>location.href="?tag="+encodeURIComponent(c),500)}
   catch(err){toast(err.message);b.disabled=false;b.textContent="Guardar cambios"}
 });
}

'''
s, n = re.subn(r'function ownerEdit\(c,p\)\{.*?\n\}\n\n(?=async function boot\(\))', owner, s, flags=re.S)
assert n == 1, f'owner replacement count={n}'

path.write_text(s, encoding='utf-8')
print('Photo upgrade applied')

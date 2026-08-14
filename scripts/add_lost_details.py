from pathlib import Path
import runpy

p = Path("index.html")
s = p.read_text(encoding="utf-8")

old_intro = '<h1>Editá el perfil.</h1><p class="muted">Usá el PIN privado para cambiar la foto, los datos o marcar a tu mascota como perdida.</p>'
new_intro = '<h1>Editá el perfil.</h1><p class="muted">Usá el PIN privado para cambiar la foto y los datos de tu mascota.</p>'
if old_intro in s:
    s = s.replace(old_intro, new_intro, 1)

old_status = ''' <div class="split"><div class="field"><label>Nombre</label><input name="name" value="${esc(p.name)}" required></div><div class="field"><label>Estado</label><select name="status"><option value="normal" ${p.status!=="perdido"?"selected":""}>Normal</option><option value="perdido" ${p.status==="perdido"?"selected":""}>🚨 Perdido</option></select></div></div>'''
new_status = ''' <div class="field"><label>Nombre</label><input name="name" value="${esc(p.name)}" required></div>
 <div class="note" style="margin-bottom:14px">Para marcar a ${esc(p.name)} como perdido y cargar dónde y cuándo se perdió, usá <a href="/mi-cuenta/" style="font-weight:900;color:#171719">Mi cuenta</a>.</div>'''
if old_status in s:
    s = s.replace(old_status, new_status, 1)

old_assign = 'Object.assign(o,{action:"update_pet",public_code:c,contact_phone:o.contact_whatsapp,public_health:f.get("public_health")==="on",public_contact:true,remove_photo:Boolean(document.getElementById("removePhoto")?.checked)});'
new_assign = 'Object.assign(o,{action:"update_pet",public_code:c,status:p.status,contact_phone:o.contact_whatsapp,public_health:f.get("public_health")==="on",public_contact:true,remove_photo:Boolean(document.getElementById("removePhoto")?.checked)});'
if old_assign in s:
    s = s.replace(old_assign, new_assign, 1)

p.write_text(s, encoding="utf-8")
print("OK: el estado perdido se administra solamente desde Mi cuenta.")

# Apply the separate guarded auth patch. It aborts if the current account UI
# does not exactly match the source we inspected, so unrelated UI is not touched.
runpy.run_path("scripts/apply_verified_email_signup.py", run_name="__main__")

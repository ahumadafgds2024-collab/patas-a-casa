from pathlib import Path

path = Path('mi-cuenta/index.html')
s = path.read_text(encoding='utf-8')

old_css = '.loading{text-align:center;padding:35px;color:var(--muted)}.toast{position:fixed;z-index:80;left:50%;bottom:max(22px,env(safe-area-inset-bottom));transform:translateX(-50%);background:#171719;color:#fff;padding:12px 15px;border-radius:15px;box-shadow:0 14px 40px rgba(0,0,0,.22);font-size:13px;max-width:90%}'
new_css = '.loading{text-align:center;padding:35px;color:var(--muted)}.toast{position:fixed;z-index:80;left:50%;bottom:max(22px,env(safe-area-inset-bottom));transform:translateX(-50%);background:#171719;color:#fff;padding:12px 15px;border-radius:15px;box-shadow:0 14px 40px rgba(0,0,0,.22);font-size:13px;max-width:90%}.pet-photo-btn{appearance:none;border:0;padding:0;cursor:zoom-in;color:inherit}.pet-photo-btn:focus-visible{outline:3px solid rgba(255,106,54,.38);outline-offset:3px}'
if old_css not in s:
    raise SystemExit('No encontré el bloque CSS esperado; no se aplicó ningún cambio')
s = s.replace(old_css, new_css, 1)

old_pet = ' const lost=p.status==="perdido";return `<article class="pet" data-code="${esc(p.public_code)}"><div class="pethead"><div class="avatar">${p.photo_url?`<img src="${esc(p.photo_url)}" alt="Foto de ${esc(p.name)}">`:p.species==="Gato"?"🐱":"🐶"}</div><div><div class="petname">${esc(p.name)}</div>'
new_pet = ' const lost=p.status==="perdido";const avatar=p.photo_url?`<button type="button" class="avatar pet-photo-btn" onclick="openPetPhoto(\'${esc(p.public_code)}\')" aria-label="Agrandar foto de ${esc(p.name)}"><img src="${esc(p.photo_url)}" alt="Foto de ${esc(p.name)}"></button>`:`<div class="avatar">${p.species==="Gato"?"🐱":"🐶"}</div>`;return `<article class="pet" data-code="${esc(p.public_code)}"><div class="pethead">${avatar}<div><div class="petname">${esc(p.name)}</div>'
if old_pet not in s:
    raise SystemExit('No encontré petCard en el formato esperado; no se aplicó ningún cambio')
s = s.replace(old_pet, new_pet, 1)

marker = 'async function loadDashboard(){'
fn = '''function openPetPhoto(c){
 const p=pets.find(x=>x.public_code===c);if(!p?.photo_url)return;
 openModal(`<div class="sheethead"><div><div class="kicker">FOTO</div><h2>${esc(p.name)}</h2></div><button class="x" onclick="closeModal()">×</button></div><div style="background:#171719;border-radius:20px;padding:8px;text-align:center"><img src="${esc(p.photo_url)}" alt="Foto ampliada de ${esc(p.name)}" style="display:block;width:100%;max-height:72dvh;object-fit:contain;border-radius:14px;margin:auto"></div><p class="small muted" style="text-align:center;margin:10px 0 0">Tocá afuera o la × para cerrar.</p>`);
}
'''
if fn.strip() not in s:
    if marker not in s:
        raise SystemExit('No encontré el punto seguro para agregar openPetPhoto')
    s = s.replace(marker, fn + marker, 1)

path.write_text(s, encoding='utf-8')
print('OK: foto ampliable agregada en Mi cuenta')

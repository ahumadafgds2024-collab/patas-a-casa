from pathlib import Path
import re
import subprocess
import tempfile

path = Path('mi-cuenta/index.html')
text = path.read_text(encoding='utf-8')

old_open = 'function openModal(content,closable=true){modal.innerHTML=`<div class="sheet">${content}</div>`;modal.classList.remove("hidden");if(closable)modal.addEventListener("click",e=>{if(e.target===modal)closeModal()},{once:true})}'
old_close = 'function closeModal(){if(flyerObjectUrl){URL.revokeObjectURL(flyerObjectUrl);flyerObjectUrl=null}flyerBlob=null;flyerFileName="";modal.classList.add("hidden");modal.innerHTML=""}'
new_open = 'function openModal(content,closable=true){modal.innerHTML=`<div class="sheet" role="dialog" aria-modal="true">${content}</div>`;modal.classList.remove("hidden");modal.onclick=closable?e=>{if(e.target===modal)closeModal()}:null}'
new_close = 'function closeModal(){if(flyerObjectUrl){URL.revokeObjectURL(flyerObjectUrl);flyerObjectUrl=null}flyerBlob=null;flyerFileName="";modal.onclick=null;modal.classList.add("hidden");modal.innerHTML=""}'

if new_open in text and new_close in text:
    print('El modal de la guia iPhone ya estaba corregido.')
elif old_open in text and old_close in text:
    text = text.replace(old_open, new_open, 1).replace(old_close, new_close, 1)
else:
    raise SystemExit('No encontre las funciones openModal/closeModal esperadas.')

required = [
    'role="dialog" aria-modal="true"',
    'modal.onclick=closable?',
    'modal.onclick=null',
    'IOS_INSTALL_GUIDE=[',
    '/mi-cuenta/ios-guia/paso-4.jpg',
]
for value in required:
    if value not in text:
        raise SystemExit('Falta una garantia requerida: ' + value)

for forbidden in [
    'modal.addEventListener("click",e=>{if(e.target===modal)closeModal()},{once:true})',
]:
    if forbidden in text:
        raise SystemExit('Quedo el cierre viejo del modal: ' + forbidden)

scripts = re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', text, flags=re.S | re.I)
for i, js in enumerate(scripts, 1):
    if not js.strip():
        continue
    with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as f:
        f.write(js)
        tmp = f.name
    result = subprocess.run(['node', '--check', tmp], capture_output=True, text=True)
    if result.returncode:
        raise SystemExit(f'JavaScript invalido en script {i}: {result.stderr}')

path.write_text(text, encoding='utf-8')
print('Modal de guia iPhone corregido y validado.')

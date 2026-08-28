from pathlib import Path
p=Path('mi-cuenta/index.html')
s=p.read_text(encoding='utf-8')
old1='if(isiOS()){openModal(`<div class="sheethead"><h2>Agregar al inicio</h2><button class="x" onclick="closeModal()">×</button></div><div class="install-steps"><div class="step"><b>1.</b> Abrí esta página en Safari.</div><div class="step"><b>2.</b> Tocá <b>Compartir</b> (el cuadrado con flecha hacia arriba).</div><div class="step"><b>3.</b> Elegí <b>Agregar a Inicio</b> y confirmá.</div></div><p class="small muted">Después vas a abrir Patas a Casa desde el ícono como una app.</p>`);return}'
new1='if(isiOS()){openModal(`<div class="sheethead"><h2>Agregar al inicio</h2><button class="x" onclick="closeModal()">×</button></div><p class="muted small">Podés hacerlo desde Safari o Chrome. No hace falta cambiar de navegador.</p><div class="install-steps"><div class="step"><b>1.</b> Tocá <b>Compartir</b>.</div><div class="step"><b>2.</b> Buscá <b>Agregar a pantalla de inicio</b>.</div><div class="step"><b>3.</b> Tocá <b>Agregar</b>.</div></div><p class="small muted">Después abrí Patas a Casa desde el nuevo ícono 🐾.</p>`);return}'
if old1 not in s: raise SystemExit('No encontré modal iOS esperado')
s=s.replace(old1,new1,1)
old2='<h2>En iPhone</h2><div class="install-steps"><div class="step"><b>1.</b> Asegurate de estar en <b>Safari</b>.</div><div class="step"><b>2.</b> Tocá <b>Compartir</b> (el cuadrado con la flecha hacia arriba).</div><div class="step"><b>3.</b> Elegí <b>Agregar a pantalla de inicio</b> y confirmá.</div><div class="step"><b>4.</b> Abrí <b>Patas a Casa</b> desde el nuevo ícono 🐾.</div></div>'
new2='<h2>En iPhone</h2><p class="muted small">Funciona desde Safari o Chrome. No hace falta cambiar de navegador.</p><div class="install-steps"><div class="step"><b>1.</b> Tocá <b>Compartir</b>.</div><div class="step"><b>2.</b> Buscá <b>Agregar a pantalla de inicio</b>.</div><div class="step"><b>3.</b> Tocá <b>Agregar</b>.</div><div class="step"><b>4.</b> Abrí <b>Patas a Casa</b> desde el nuevo ícono 🐾.</div></div>'
if old2 not in s: raise SystemExit('No encontré pantalla final iOS esperada')
s=s.replace(old2,new2,1)
p.write_text(s,encoding='utf-8')
print('OK: iPhone ya no depende de Safari')

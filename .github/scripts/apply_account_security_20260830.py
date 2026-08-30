from pathlib import Path
import re
import subprocess
import tempfile


def validate_inline_js(html, label):
    scripts = re.findall(r'<script(?![^>]*\\bsrc=)[^>]*>(.*?)</script>', html, flags=re.S | re.I)
    for i, js in enumerate(scripts, 1):
        if not js.strip():
            continue
        with tempfile.NamedTemporaryFile('w', suffix='.js', encoding='utf-8', delete=False) as f:
            f.write(js)
            name = f.name
        result = subprocess.run(['node', '--check', name], capture_output=True, text=True)
        if result.returncode != 0:
            raise SystemExit(f'JavaScript inválido en {label}, script {i}:\n{result.stderr}')

# Revisión puntual del flujo nuevo sin tocar la lógica de activación.
account_path = Path('mi-cuenta/index.html')
account = account_path.read_text(encoding='utf-8')
home = Path('index.html').read_text(encoding='utf-8')

# La pantalla de alta de mascota no debe hablar de PIN/código ni repetir que la chapita fue verificada.
account = account.replace('<div class="kicker">CHAPITA VERIFICADA</div><h1>Creá el perfil de tu mascota.</h1><p class="muted">La chapita ya está validada. Cargá ahora los datos de quien la va a llevar.</p>', '<div class="kicker">ÚLTIMO PASO</div><h1>Creá el perfil de tu mascota.</h1><p class="muted">Cargá los datos de tu mascota para terminar de configurar la chapita.</p>', 1)
account = account.replace('<section class="card"><div class="note" style="margin-bottom:14px"><b>Chapita ${esc(c)} verificada ✅</b><br>No necesitás volver a ingresar el código ni el PIN.</div>\n <form id="activationProfileForm" method="post">', '<section class="card"><form id="activationProfileForm" method="post">', 1)

# Auditoría de textos/estados que ya no deben aparecer en el recorrido nuevo.
for stale in [
    'No necesitás volver a ingresar el código ni el PIN.',
    'La chapita ya está validada. Cargá ahora los datos de quien la va a llevar.',
    '<div class="kicker">CHAPITA VERIFICADA</div>',
]:
    if stale in account:
        raise SystemExit('Quedó texto heredado en Mi cuenta: ' + stale)

for stale in ['Etiqueta ya activada (Modo Demo)', 'Activación de prueba:']:
    if stale in home:
        raise SystemExit('Quedó texto de prueba en la activación pública: ' + stale)

# Mantener las correcciones anteriores como invariantes.
for required in [
    'forEach(el=>el.remove());return',
    'function openPasswordSettings()',
    'function openDeleteAccount()',
    'async function updateAccountPassword(',
]:
    if required not in account:
        raise SystemExit('Falta comportamiento esperado en Mi cuenta: ' + required)
for required in ['const activationIsiOS=', 'Activá tu chapita.']:
    if required not in home:
        raise SystemExit('Falta comportamiento esperado en activación pública: ' + required)

validate_inline_js(account, 'mi-cuenta/index.html')
validate_inline_js(home, 'index.html')
account_path.write_text(account, encoding='utf-8')
print('Limpieza de copy + auditoría del flujo de activación OK')

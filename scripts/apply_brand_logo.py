from pathlib import Path
import re

FILES = [
    Path('index.html'),
    Path('mi-cuenta/index.html'),
    Path('mi-cuenta/perdidas/index.html'),
    Path('mi-cuenta/confirmar/index.html'),
    Path('mi-cuenta/recuperar/index.html'),
    Path('privacidad.html'),
    Path('terminos.html'),
]

STYLE = '''<style id="pac-brand-logo-v1">
.logo{
  background-image:url('/mi-cuenta/icons/icon-192.png')!important;
  background-repeat:no-repeat!important;
  background-position:center -4px!important;
  background-size:78px 78px!important;
  background-color:transparent!important;
  box-shadow:none!important;
  color:transparent!important;
  font-size:0!important;
  overflow:hidden!important;
  border-radius:14px!important;
}
.logo::before{display:none!important;content:none!important}
</style>'''

for path in FILES:
    if not path.exists():
        continue
    text = path.read_text(encoding='utf-8')
    original = text

    # Remove the old paw emoji from logo containers; CSS supplies the official mark.
    text = re.sub(r'(<div\s+class=["\']logo["\'][^>]*>)\s*🐾\s*(</div>)', r'\1\2', text)

    if 'class="logo"' in text or "class='logo'" in text:
        if 'id="pac-brand-logo-v1"' not in text:
            text = text.replace('</head>', STYLE + '</head>', 1)

    if text != original:
        path.write_text(text, encoding='utf-8')
        print('updated', path)

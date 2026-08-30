from pathlib import Path
import re, subprocess, tempfile

p=Path('mi-cuenta/index.html')
h=p.read_text(encoding='utf-8')

pattern=r'function openClaim\(\)\{.*?\n\}\n\nasync function prepareQueuedActivation'
replacement='function openClaim(){openPinClaim()}\n\nasync function prepareQueuedActivation'
h2,n=re.subn(pattern,replacement,h,count=1,flags=re.S)
if n!=1:
    raise SystemExit('No encontré el bloque openClaim para volver a PIN')

scripts=re.findall(r'<script(?![^>]*\\bsrc=)[^>]*>(.*?)</script>',h2,re.S|re.I)
for i,js in enumerate(scripts,1):
    if not js.strip():
        continue
    with tempfile.NamedTemporaryFile('w',suffix='.js',encoding='utf-8',delete=False) as f:
        f.write(js)
        name=f.name
    r=subprocess.run(['node','--check',name],capture_output=True,text=True)
    if r.returncode:
        raise SystemExit(f'JS inválido script {i}: {r.stderr}')

if 'function openClaim(){openPinClaim()}' not in h2:
    raise SystemExit('No quedó activo el flujo PIN')

p.write_text(h2,encoding='utf-8')
print('Agregar chapita volvió al PIN y JS validado')

from pathlib import Path

p = Path('tag.html')
s = p.read_text(encoding='utf-8')
old = 'if(activationMode==="shared"){location.replace("/mi-cuenta/shared-activate.html?tag="+encodeURIComponent(c));return}'
new = 'if(activationMode==="shared"){const base=/vercel\\.app$/i.test(location.hostname)?"https://patasacasa.com.ar":"";location.replace(base+"/mi-cuenta/shared-activate.html?tag="+encodeURIComponent(c));return}'
count = s.count(old)
if count != 1:
    raise SystemExit(f'Esperaba 1 coincidencia y encontré {count}')
s = s.replace(old, new, 1)
if 'patasacasa.com.ar' not in s or 'activationMode==="shared"' not in s:
    raise SystemExit('Sanity check falló')
p.write_text(s, encoding='utf-8')
print('OK: shared desde Vercel redirige al dominio nuevo; PIN legacy no se toca')

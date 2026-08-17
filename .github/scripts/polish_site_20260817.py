from pathlib import Path
import re


def replace_once(text, old, new, label):
    if old not in text:
        raise SystemExit(f"No encontré: {label}")
    return text.replace(old, new, 1)


# ---------- PERFIL / PORTADA PÚBLICA ----------
p = Path("index.html")
s = p.read_text(encoding="utf-8")

if 'name="description"' not in s:
    s = replace_once(
        s,
        '<meta name="theme-color" content="#171719">',
        '<meta name="theme-color" content="#171719">\n'
        '<meta name="description" content="Patas a Casa: identificación inteligente para mascotas con perfil digital, contacto rápido y modo perdido.">\n'
        '<link rel="icon" type="image/png" href="/mi-cuenta/icons/icon-192.png">',
        "metadatos públicos",
    )

if "button:focus-visible,a:focus-visible" not in s:
    s = replace_once(
        s,
        ".btn:disabled{opacity:.55}",
        ".btn:disabled{opacity:.55}\n"
        "button:focus-visible,a:focus-visible{outline:3px solid rgba(255,106,54,.38);outline-offset:3px}",
        "focus visible público",
    )

old_header = '<header class="header"><div class="brand"><div class="logo">🐾</div><span>Patas a Casa</span></div><div style="display:flex;align-items:center;gap:7px"><a class="demo" style="text-decoration:none;color:#333" href="/mi-cuenta/">Mi cuenta</a><span class="demo">PRUEBA</span></div></header>'
new_header = '<header class="header"><div class="brand"><div class="logo">🐾</div><span>Patas a Casa</span></div><a class="demo" style="text-decoration:none;color:#333" href="/mi-cuenta/">Mi cuenta</a></header>'
s = replace_once(s, old_header, new_header, "etiqueta PRUEBA")

home_pattern = re.compile(
    r'function home\(\)\{\n root\.innerHTML=`<section class="card hero">.*?</section>`;\n\}',
    re.S,
)
m = home_pattern.search(s)
if not m:
    raise SystemExit("No encontré home() público")
new_home = '''function home(){
 document.title="Patas a Casa";
 root.innerHTML=`<section class="card hero"><div class="kicker">IDENTIFICACIÓN INTELIGENTE</div><h1>Una forma simple de volver a casa.</h1><p class="muted">Cada chapita Patas a Casa conecta a la mascota con un perfil actualizado y formas rápidas de contactar a su familia.</p><div class="note"><b>¿Encontraste una mascota?</b><br>Escaneá el QR de su chapita. No necesitás descargar una app ni crear una cuenta.</div><a class="btn dark" style="margin-top:12px" href="/mi-cuenta/">👤 Entrar a Mi cuenta</a><p class="small muted" style="text-align:center;margin:12px 4px 0">Si tu chapita es nueva, escaneá su QR para activarla.</p></section>`;
}'''
s = s[: m.start()] + new_home + s[m.end() :]

if 'document.title="Activar chapita · Patas a Casa";' not in s:
    s = replace_once(
        s,
        'function unactivated(c){\n root.innerHTML=',
        'function unactivated(c){\n document.title="Activar chapita · Patas a Casa";\n root.innerHTML=',
        "título activación",
    )

if "document.title=(p?.name?" not in s:
    s = replace_once(
        s,
        'function active(c,p){\n const lost=',
        'function active(c,p){\n document.title=(p?.name?`${p.name} · `:"")+"Patas a Casa";\n const lost=',
        "título perfil mascota",
    )

s = replace_once(
    s,
    ' const lost=p.status==="perdido",phone=tel(p.contact_phone),whats=wa(p.contact_whatsapp||p.contact_phone);',
    ' const lost=p.status==="perdido",allowContact=p.public_contact!==false,phone=allowContact?tel(p.contact_phone):"",whats=allowContact?wa(p.contact_whatsapp||p.contact_phone):"";',
    "control visual de contacto público",
)

contact_re = re.compile(
    r'<section class="card"><h2>Contactá a su familia</h2><div class="actions">\$\{phone\?.*?</div></section>',
    re.S,
)
cm = contact_re.search(s)
if not cm:
    raise SystemExit("No encontré tarjeta de contacto pública")
contact = cm.group(0)
contact = contact.replace(
    "</div></section>",
    '</div>${allowContact&&p.alt_contact?`<div class="box" style="margin-top:10px"><strong>Segundo contacto de emergencia</strong>${esc(p.alt_contact)}</div>`:""}${!phone&&!whats&&!(allowContact&&p.alt_contact)?`<div class="note" style="margin-top:10px">Los datos de contacto no están publicados. Podés enviar un aviso desde el formulario de abajo.</div>`:""}</section>',
    1,
)
s = s[: cm.start()] + contact + s[cm.end() :]

# Priorizar el contacto por encima de salud/cuidados sin eliminar información.
order_re = re.compile(
    r'\n \$\{health\}\n (?P<contact><section class="card"><h2>Contactá a su familia</h2>.*?</section>)\n (?P<found><section class="card"><h2>📍)',
    re.S,
)
om = order_re.search(s)
if not om:
    raise SystemExit("No encontré orden salud/contacto")
s = (
    s[: om.start()]
    + "\n "
    + om.group("contact")
    + "\n ${health}\n "
    + om.group("found")
    + s[om.end() :]
)

p.write_text(s, encoding="utf-8")


# ---------- MI CUENTA ----------
p = Path("mi-cuenta/index.html")
s = p.read_text(encoding="utf-8")

if 'name="description"' not in s:
    s = replace_once(
        s,
        '<meta name="theme-color" content="#171719">',
        '<meta name="theme-color" content="#171719">\n'
        '<meta name="description" content="Panel privado de Patas a Casa para administrar mascotas, chapitas, modo perdido, flyers y avistamientos.">\n'
        '<link rel="icon" type="image/png" href="/mi-cuenta/icons/icon-192.png">',
        "metadatos Mi cuenta",
    )

if "button:focus-visible,a:focus-visible" not in s:
    s = replace_once(
        s,
        ".btn:disabled{opacity:.55;cursor:wait}",
        ".btn:disabled{opacity:.55;cursor:wait}\n"
        "button:focus-visible,a:focus-visible{outline:3px solid rgba(255,106,54,.38);outline-offset:3px}",
        "focus visible Mi cuenta",
    )

old_actions = '''<button class="btn soft" onclick="editPet('${esc(p.public_code)}')">✏️ Editar perfil</button><a class="btn dark" href="/?tag=${encodeURIComponent(p.public_code)}" target="_blank">👁 Ver perfil público</a>'''
new_actions = '''<button class="btn soft" onclick="editPet('${esc(p.public_code)}')">✏️ Editar perfil</button><button class="btn soft" onclick="showSightings('${esc(p.public_code)}')">📍 Avistamientos</button><a class="btn dark" href="/?tag=${encodeURIComponent(p.public_code)}" target="_blank" rel="noopener">👁 Ver perfil público</a>'''
s = replace_once(s, old_actions, new_actions, "restaurar Avistamientos")

p.write_text(s, encoding="utf-8")

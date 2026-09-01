from pathlib import Path

PATCHES = {
    Path("mi-cuenta/index.html"): [
        (
            'const GOOGLE_REDIRECT_URL="https://patas-a-casa.vercel.app/mi-cuenta/?google=1";',
            'const GOOGLE_REDIRECT_URL=location.origin+"/mi-cuenta/?google=1";',
        ),
    ],
    Path("mi-cuenta/recuperar/index.html"): [
        (
            'const REDIRECT_URL="https://patas-a-casa.vercel.app/mi-cuenta/recuperar/";',
            'const REDIRECT_URL=location.origin+"/mi-cuenta/recuperar/";',
        ),
    ],
    Path("gestion-chapitas.html"): [
        (
            "const APP='https://patas-a-casa.vercel.app';",
            "const APP=location.origin;",
        ),
    ],
}

for path, replacements in PATCHES.items():
    text = path.read_text(encoding="utf-8")
    original = text
    for old, new in replacements:
        count = text.count(old)
        if count == 0:
            if new in text:
                continue
            raise SystemExit(f"No encontré el texto esperado en {path}: {old}")
        if count != 1:
            raise SystemExit(f"Esperaba 1 coincidencia en {path} y encontré {count}: {old}")
        text = text.replace(old, new, 1)
    if text != original:
        path.write_text(text, encoding="utf-8")

# Verificaciones de seguridad: los tres puntos sensibles deben ser dinámicos.
account = Path("mi-cuenta/index.html").read_text(encoding="utf-8")
recovery = Path("mi-cuenta/recuperar/index.html").read_text(encoding="utf-8")
management = Path("gestion-chapitas.html").read_text(encoding="utf-8")

assert 'const GOOGLE_REDIRECT_URL=location.origin+"/mi-cuenta/?google=1";' in account
assert 'const REDIRECT_URL=location.origin+"/mi-cuenta/recuperar/";' in recovery
assert "const APP=location.origin;" in management

print("Migración dual-origin aplicada correctamente.")

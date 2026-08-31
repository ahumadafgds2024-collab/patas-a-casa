# GitHub Actions — política y clasificación

## Objetivo

Que la carpeta `.github/workflows/` contenga automatizaciones permanentes y reconocibles. Los workflows creados para aplicar un cambio puntual no deben quedar indefinidamente mezclados con CI/monitorización.

## Clasificación actual

### Mantener como CI / monitorización

- `hosting-check.yml` — smoke test de la producción Vercel: comprueba HTTP 200 y presencia del nombre de la aplicación.

### Requiere decisión

- `pages.yml` — despliegue secundario a GitHub Pages. La ejecución más reciente falla en `Setup Pages`. Conservar sólo si GitHub Pages tiene una función intencional de backup o hosting secundario.

### Candidatos a archivo/retiro después de verificar consolidación

- `add-google-password-prompt-20260830.yml`
- `add-lost-details.yml`
- `add-owner-flyer.yml`
- `agrandar-logo-panel.yml`
- `aplicar-colores-marca-panel.yml`
- `apply-account-security-20260830.yml`
- `apply-brand-logo.yml`
- `apply-legal-privacy.yml`
- `apply-photo-lightbox.yml`
- `apply-photo-upgrade.yml`
- `check-admin-qr-simple.yml`
- `finish-owner-panel.yml`
- `fix-admin-qr.yml`
- `fix-google-pending-android-20260830.yml`
- `polish-user-site-20260817.yml`
- `pulir-panel-responsable-ui.yml`

La inclusión en esta lista **no significa que sea seguro borrarlos todavía**. Significa que sus nombres y/o comportamiento indican automatizaciones ligadas a cambios puntuales, y deben revisarse una por una.

## Patrón a evitar

Un workflow permanente no debería seguir este ciclo:

```text
checkout
→ ejecutar script que parchea HTML
→ git add
→ git commit
→ git push a main
```

Este patrón mezcla compilación/validación con edición del código fuente y puede generar despliegues encadenados.

## Patrón recomendado

```text
pull request
→ validaciones automáticas
→ preview
→ revisión
→ merge único a main
→ smoke test de producción
```

## Qué debe vivir en un workflow permanente

Sí:
- smoke tests;
- validaciones sintácticas;
- checks de enlaces/rutas;
- tests de regresión;
- despliegue explícito si la plataforma realmente lo necesita.

No:
- scripts que existieron sólo para un rediseño puntual;
- correcciones de un día específico ya incorporadas;
- bots que reescriben `index.html` y vuelven a empujar a `main`;
- archivos con nombres de una incidencia que ya quedó cerrada.

## Convención futura

Los workflows permanentes deberían usar nombres por responsabilidad, no por parche:

- `ci.yml`
- `smoke-production.yml`
- `security-check.yml`
- `deploy-pages.yml` (sólo si GitHub Pages se conserva)

Los scripts auxiliares reutilizables deberían vivir bajo `tools/` o `scripts/` y tener documentación de entrada/salida. Los scripts de migración de una sola vez deben eliminarse después de quedar representado el estado final en el código y en Git.
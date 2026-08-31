# Arquitectura de Patas a Casa

## Objetivo

Este documento define qué componente hace qué y cuál es su fuente de verdad. Su función es evitar duplicados, cambios en el lugar equivocado y dependencias invisibles.

## Mapa de alto nivel

```text
QR físico
  ↓
Vercel / index.html
  ├─ perfil público
  ├─ activación por PIN
  └─ acceso/autenticación
        ↓
Supabase Edge Functions
        ↓
PostgreSQL + Supabase Auth
```

La cuenta del responsable vive bajo `mi-cuenta/`. La gestión interna vive en `gestion-chapitas.html`. La comunidad de mascotas perdidas combina la interfaz `mi-cuenta/perdidas/` con funciones de Supabase.

## Frontend

### `index.html`

Responsabilidades actuales:
- lectura del código de chapita desde URL;
- perfil público;
- flujo de activación;
- autenticación inicial;
- comunicación con `patas-api`, `patas-register-v2` y `patas-lost`.

Es actualmente un archivo monolítico con HTML, CSS y JavaScript embebidos. **No dividirlo durante una limpieza de archivos**: hacerlo requiere una refactorización separada y pruebas de regresión porque es el punto de entrada de las chapitas físicas.

### `mi-cuenta/`

- `index.html`: panel del responsable.
- `confirmar/`: confirmación de cuenta.
- `recuperar/`: recuperación de acceso.
- `perdidas/`: comunidad de mascotas perdidas.
- `manifest.webmanifest`, `sw.js`, `icons/`: PWA/acceso desde inicio.

### Administración

- `gestion-chapitas.html`: panel privado para localizar, bloquear, desbloquear y resetear chapitas.
- `admin.html`: herramienta administrativa auxiliar. Debe mantenerse separada del panel de usuarios.

## Hosting y rutas

Vercel sirve el frontend estático. `vercel.json` mantiene compatibilidad de rutas QR:

- `/m/:code` → `/?tag=:code`
- `/t/:code` → `/?tag=:code`
- `/S/:code` → `/?tag=:code`
- `/gestion-chapitas` → `/gestion-chapitas.html`

Estas rutas son **contratos de compatibilidad** y no deben renombrarse sin validar previamente las chapitas impresas.

## Supabase

Proyecto productivo: `cgciwutqwnssdphugupq`.

### Tablas públicas existentes

- `tags`: identidad física/digital de cada chapita.
- `pets`: perfil de mascota y datos del responsable.
- `pending_owner_claims`: vinculaciones pendientes durante activación.
- `short_links`: enlaces cortos asociados a chapitas.
- `sightings`: avisos/localizaciones reportadas.
- `admin_tag_events`: auditoría de operaciones administrativas.
- `app_admin_config`: configuración protegida del panel administrativo.

Todas tienen RLS habilitado. Actualmente las tablas no conceden privilegios directos a `anon` ni `authenticated`; el acceso productivo se concentra en funciones de backend con `service_role` y en RPCs controlados.

### Edge Functions desplegadas

Supabase contiene 18 deployments de Edge Functions, pero no las 18 representan lógica productiva actual.

#### Productivas y versionadas en GitHub — 5

- `patas-api`
- `patas-account`
- `patas-register-v2`
- `patas-admin-tags`
- `patas-lost-community`

#### Productivas con drift — 3

Contienen lógica real en producción pero todavía no están presentes bajo `supabase/functions/`:

- `patas-lost`
- `patas-account-security`
- `patas-admin-shortio`

Éste es el drift productivo que debe resolverse primero.

#### Retiradas / compatibilidad — 10

Sus deployments siguen existiendo, pero el código vivo responde deliberadamente HTTP `410` y no ejecuta lógica productiva:

- `patas-demo`
- `publish-patas-web`
- `patas-web`
- `publish-patas-static`
- `xhtml-test`
- `patas-admin`
- `patas-register-v2-test`
- `patas-short`
- `patas-email-activation`
- `patas-tag-scan`

El inventario detallado, versiones y criterio de retiro están documentados en [`EDGE-FUNCTIONS.md`](EDGE-FUNCTIONS.md).

## Fuentes de verdad

| Componente | Fuente de verdad deseada |
|---|---|
| Frontend | GitHub `main` |
| Rutas/headers | `vercel.json` |
| Edge Functions | `supabase/functions/` |
| Esquema de DB | `supabase/migrations/` |
| Configuración sensible | variables/secretos de plataforma, nunca GitHub |
| Historial operativo | Git + logs de Vercel/Supabase |

## Deuda estructural identificada

1. Tres Edge Functions productivas todavía viven sólo en Supabase y deben versionarse exactamente.
2. El esquema vivo de base de datos no puede reconstruirse únicamente con las dos migraciones actuales.
3. Existen muchos scripts/workflows de cambios puntuales que dificultan distinguir automatización permanente de parches históricos.
4. Los archivos principales de frontend son grandes y monolíticos; conviene modularizarlos más adelante, pero no como parte de una limpieza de riesgo cero.

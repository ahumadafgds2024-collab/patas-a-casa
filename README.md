# Patas a Casa

Aplicación web para identificación de mascotas mediante chapitas QR, activación por PIN, perfil público, cuenta del responsable, gestión interna y comunidad de mascotas perdidas.

## Estado del proyecto

- **Producción web:** Vercel (`patas-a-casa.vercel.app`)
- **Backend y datos:** Supabase
- **Código fuente:** este repositorio
- **Rama productiva:** `main`
- **Política de seguridad:** no modificar `main` con parches experimentales; todo cambio estructural debe pasar por una rama y una verificación previa.

## Estructura actual

```text
/
├── index.html                  # Perfil público + activación
├── mi-cuenta/                  # Cuenta, confirmación, recuperación y perdidas
├── gestion-chapitas.html       # Panel privado de gestión
├── admin.html                  # Herramienta administrativa auxiliar
├── privacidad.html
├── terminos.html
├── vercel.json                 # Rutas y headers de Vercel
├── supabase/
│   ├── functions/              # Edge Functions versionadas
│   └── migrations/             # Cambios de base de datos versionados
├── scripts/                    # Scripts históricos de modificación; NO runtime
├── .github/
│   ├── scripts/                # Automatizaciones históricas
│   └── workflows/              # GitHub Actions
└── docs/                       # Arquitectura, seguridad y operación
```

> **Importante:** los directorios `scripts/` y `.github/scripts/` no forman parte de la aplicación en ejecución. Son herramientas históricas y no deben convertirse en una segunda fuente de verdad del código productivo.

## Documentación operativa

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md): mapa técnico y fuentes de verdad.
- [`docs/DATABASE.md`](docs/DATABASE.md): tablas, relaciones, datos sensibles, RLS e índices.
- [`docs/EDGE-FUNCTIONS.md`](docs/EDGE-FUNCTIONS.md): inventario exacto de funciones productivas, drift y endpoints retirados.
- [`docs/SECURITY.md`](docs/SECURITY.md): modelo de seguridad y hallazgos de auditoría.
- [`docs/OPERATIONS.md`](docs/OPERATIONS.md): proceso seguro para cambios, despliegues y rollback.
- [`docs/AUDIT-2026-08-31.md`](docs/AUDIT-2026-08-31.md): auditoría y prioridades de saneamiento.
- [`.github/WORKFLOWS.md`](.github/WORKFLOWS.md): clasificación y política de GitHub Actions.

## Regla de oro

Antes de eliminar, mover o reemplazar una ruta, Edge Function, workflow, RPC o tabla:

1. comprobar si producción la utiliza;
2. verificar logs y referencias;
3. conservar una copia versionada;
4. probar en preview;
5. recién después modificar `main`.

La prioridad del proyecto es mantener compatibles las chapitas ya entregadas: **QR, código público y PIN no deben cambiar por una reorganización interna**.

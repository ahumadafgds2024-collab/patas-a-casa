# Gestión comercial de Patas a Casa

Panel privado en `/ventas/`. Sitio estático, sin cambios en la portada ni en los perfiles públicos.

Desde esta carpeta: `pnpm install --frozen-lockfile`, `pnpm build`.
El resultado se genera en `ventas/` y se publica con el repositorio en Vercel.
`pnpm test` verifica las reglas del backend.

## Acceso y datos

- Supabase Auth con sesión separada `pac_sales_auth_v1`.
- API: Edge Function `patas-sales` en el proyecto existente.
- Tablas `sales_workspace` y `sales_invites`: RLS y permisos sin acceso directo de anon/authenticated. La API valida sesión con Auth y permisos actuales en cada petición.
- Comparación de versión para evitar pérdida de actualizaciones concurrentes. Pagos y comisiones con identificadores de idempotencia.
- Invitaciones: 32 bytes aleatorios, solo hash almacenado, 7 días y un solo uso. No se envían mensajes automáticamente ni se restablecen contraseñas existentes.
- Propietario fijado por migración a partir de una cuenta confirmada existente, nunca por primer visitante.
- Edge Function usa `verify_jwt=false` porque valida con `auth.getUser`; consulta/activación de invitaciones requieren el token aleatorio.
- Recuperación de contraseña: `/mi-cuenta/recuperar/`.
- Sin enlace desde menús públicos. HTML y cabeceras indican `noindex`. La privacidad se aplica en la API.
- Respaldo JSON contiene registros, nunca contraseñas ni enlaces de activación.

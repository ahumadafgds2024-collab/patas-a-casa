# Seguridad

## Principios

1. El navegador sólo puede conocer claves publicables.
2. `service_role` permanece exclusivamente en backend/variables seguras.
3. CORS no reemplaza autenticación ni autorización.
4. Los datos privados de una mascota deben filtrarse en backend; RLS protege filas, no columnas.
5. Toda operación administrativa debe quedar autenticada y ser auditable.

## Estado verificado — 31 de agosto de 2026

### Base de datos

Las siete tablas del esquema `public` tienen RLS habilitado. No existen grants directos para los roles `anon` o `authenticated`; las ACL actuales están limitadas a `postgres` y `service_role`.

Esto significa que la política `pets_public_read_active` **no expone actualmente la tabla `pets` directamente por Data API**. Sin embargo, esa política permite seleccionar la fila completa de una mascota activa si en el futuro se concede `SELECT`, por lo que constituye una configuración latente que debe revisarse antes de habilitar acceso directo a tablas.

`pets` contiene, entre otros, datos de contacto y salud. Para cualquier futura API pública se recomienda una función o vista explícita que devuelva sólo los campos autorizados según `public_contact` y `public_health`.

### RPC `find_tag_by_activation_pin`

El Security Advisor marca esta función porque es `SECURITY DEFINER` y el rol `authenticated` puede ejecutarla.

Mitigaciones ya existentes:
- exige `auth.uid()` válido;
- normaliza el PIN y exige 8 dígitos;
- compara contra un hash mediante `crypt`;
- ignora chapitas bloqueadas;
- sólo devuelve `public_code`.

Riesgo residual: cualquier usuario autenticado puede invocarla directamente. Antes de cambiar permisos hay que verificar qué flujo depende de ella. Como mejora, debe evaluarse concentrar la búsqueda de PIN detrás de una Edge Function con controles de abuso/rate limiting y quitar el RPC del contrato directo del cliente si no es necesario.

### Panel de gestión

`gestion-chapitas.html` no contiene la clave administrativa. La clave se introduce en la sesión de la pestaña y se envía a `patas-admin-tags`.

`patas-admin-tags`:
- conserva `service_role` en variables del servidor;
- restringe el origen esperado;
- valida una clave administrativa mediante RPC;
- limita tamaño de cuerpo y tiempos de fetch;
- genera `request_id` para trazabilidad.

El origen/CORS es defensa complementaria; la autorización real depende de la clave administrativa y los RPC protegidos.

### Supabase Auth

El Security Advisor informa que **Leaked Password Protection está deshabilitado**. Activarlo es una mejora recomendada, pero debe hacerse desde la configuración de Auth y probar el alta/cambio de contraseña antes de considerarlo cerrado.

## Pendientes de seguridad priorizados

### P1 — revisar antes de ampliar acceso

- Diseñar un contrato público explícito para `pets` que no pueda revelar campos privados por error.
- Confirmar uso de `find_tag_by_activation_pin` y reducir su superficie directa si es posible.
- Versionar todas las Edge Functions realmente productivas para poder auditar cambios.

### P2 — endurecimiento

- Activar protección contra contraseñas filtradas en Supabase Auth.
- Evaluar Content-Security-Policy. Actualmente el frontend usa gran cantidad de CSS/JS inline; agregar una CSP estricta sin refactor previo podría romper producción.
- Evaluar HSTS cuando todos los dominios y redirecciones HTTPS estén confirmados.

## Regla para cambios de seguridad

Nunca "arreglar" un warning cambiando permisos o borrando una función sin comprobar primero el flujo real. Para este proyecto, disponibilidad y compatibilidad de chapitas existentes tienen la misma prioridad que el endurecimiento de seguridad.

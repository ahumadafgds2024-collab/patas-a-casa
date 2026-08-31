# Inventario de Supabase Edge Functions

Fecha de verificación: 31 de agosto de 2026.

## Cómo leer este documento

- **Productiva / versionada:** contiene lógica real y ya existe en GitHub.
- **Productiva / drift:** contiene lógica real en Supabase pero falta en GitHub.
- **Retirada / compatibilidad:** la función sigue desplegada, pero responde HTTP `410`; no contiene lógica productiva actual.

Que una función retirada siga `ACTIVE` en Supabase no significa que esté en uso: `ACTIVE` indica que existe un deployment disponible. Antes de eliminarla se deben comprobar referencias y compatibilidad.

## Resumen

| Estado | Cantidad |
|---|---:|
| Productivas y versionadas | 5 |
| Productivas con drift | 3 |
| Retiradas / compatibilidad | 10 |
| **Total desplegadas** | **18** |

Por lo tanto, el problema real de código productivo no versionado queda acotado a **3 funciones**, no a 13.

## Productivas y versionadas

| Función | Rol |
|---|---|
| `patas-api` | API del perfil/chapita |
| `patas-account` | operaciones de cuenta |
| `patas-register-v2` | registro/activación |
| `patas-admin-tags` | gestión privada de chapitas |
| `patas-lost-community` | comunidad de mascotas perdidas |

## Productivas con drift — prioridad P1

### `patas-lost`

- Supabase: versión 2.
- `verify_jwt`: `false`.
- Estado real: lógica productiva.
- Funciones: lectura pública del estado perdido y actualización autenticada del estado de la mascota.
- Protecciones observadas: validación de usuario para escritura, tamaño máximo de body, timeouts, `request_id`, logging estructurado.
- Acción: copiar exactamente la versión viva a `supabase/functions/patas-lost/` y luego comparar con el frontend antes de cualquier redeploy.

### `patas-account-security`

- Supabase: versión 2.
- `verify_jwt`: `true`.
- Estado real: lógica productiva.
- Funciones: estado de métodos de acceso, creación de contraseña de respaldo y eliminación completa de cuenta.
- Usa `service_role` sólo del lado servidor y vuelve a validar al usuario mediante Supabase Auth.
- Acción: versionar exactamente la versión viva; por su capacidad de eliminar cuenta/datos, tratar cambios futuros como seguridad crítica.

### `patas-admin-shortio`

- Supabase: versión 3.
- `verify_jwt`: `false`; implementa autorización administrativa propia.
- Estado real: lógica productiva administrativa.
- Funciones: genera lotes de chapitas, crea enlaces Short.io, verifica redirects y realiza rollback si un lote queda incompleto.
- Acción: versionar exactamente la versión viva; no modificar hasta preservar el rollback y la validación de enlaces físicos.

## Retiradas / compatibilidad

Estas funciones están desplegadas pero su código actual devuelve deliberadamente HTTP `410` (`Endpoint retirado`, `Endpoint deshabilitado` o equivalente):

| Función | Versión viva | JWT | Nota |
|---|---:|---:|---|
| `patas-demo` | 2 | no | endpoint retirado |
| `publish-patas-web` | 2 | no | endpoint retirado |
| `patas-web` | 2 | no | endpoint retirado |
| `publish-patas-static` | 2 | no | endpoint retirado |
| `xhtml-test` | 2 | no | endpoint retirado |
| `patas-admin` | 6 | no | reemplazado explícitamente por generador Short.io |
| `patas-register-v2-test` | 2 | no | endpoint retirado |
| `patas-short` | 5 | no | endpoint deshabilitado |
| `patas-email-activation` | 2 | sí | endpoint retirado |
| `patas-tag-scan` | 2 | sí | endpoint retirado |

## Política para retirar definitivamente un stub 410

No borrarlo sólo porque ya no tenga lógica. Primero:

1. buscar referencias en frontend, scripts y documentación;
2. verificar logs de llamadas;
3. confirmar que ninguna app/chapita antigua depende específicamente del `410` para degradar de forma controlada;
4. guardar el código/version/metadata en Git;
5. retirar en un cambio separado;
6. verificar que las rutas productivas continúen funcionando.

## Objetivo final

El repositorio debería poder responder, sin entrar al dashboard de Supabase:

- qué funciones existen;
- cuáles están en producción;
- cuáles están retiradas;
- qué versión corresponde al código de Git;
- qué función puede desplegarse de nuevo si hay que reconstruir el sistema.

La siguiente reducción de drift debe enfocarse únicamente en `patas-lost`, `patas-account-security` y `patas-admin-shortio`.
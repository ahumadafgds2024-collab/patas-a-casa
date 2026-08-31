# Mapa de base de datos productiva

Fecha de verificación: 31 de agosto de 2026.

## Objetivo

Documentar el esquema vivo sin exponer registros de usuarios. Este archivo describe responsabilidades, relaciones y superficies sensibles; no contiene datos personales.

## Tablas

### `tags`

Representa la identidad física de cada chapita.

Campos clave:
- `id` UUID, PK;
- `public_code` único;
- `activation_hash` — hash del PIN de activación, nunca el PIN en claro;
- `activated_at`;
- `blocked_at`;
- `pet_id` → `pets.id`.

Índices relevantes:
- `tags_public_code_key` único;
- `tags_pet_id_idx`.

**Contrato crítico:** `public_code` forma parte de las URLs físicas y no debe regenerarse por una limpieza interna.

### `pets`

Perfil central de la mascota y preferencias de publicación del responsable.

Grupos de campos:
- identidad: `name`, `species`, `breed`, `sex`, `age_text`, `size`, `color`, `photo_url`;
- estado: `status`, `is_active`, `lost_location`, `lost_at`, `lost_details`;
- salud: `diseases`, `medications`, `medication_schedule`, `allergies`, `special_care`, `vet_info`;
- contacto: `contact_name`, `contact_phone`, `contact_whatsapp`, `alt_contact`;
- privacidad: `public_health`, `public_contact`;
- propiedad: `owner_id`;
- enlace físico: `public_code` único.

Campos especialmente sensibles:
- salud;
- teléfonos/contacto;
- datos veterinarios;
- información de pérdida/localización.

`public_health` y `public_contact` deben respetarse siempre desde el backend al construir respuestas públicas.

Índices relevantes:
- `pets_public_code_key` único;
- `pets_owner_id_idx`.

Nota: `owner_id` no posee una foreign key declarada hacia `auth.users`. El backend/Auth es responsable de mantener esa asociación coherente. No agregar una FK automáticamente sin revisar primero el flujo de eliminación de cuentas.

### `pending_owner_claims`

Estado transitorio de una activación/vinculación de chapita con un usuario.

Relaciones:
- `tag_id` → `tags.id`;
- `pet_id` → `pets.id`.

Controla:
- `auth_user_id`;
- `email`;
- `public_code`;
- `expires_at`;
- `consumed_at`.

Índices parciales únicos impiden más de una vinculación abierta por chapita y por usuario.

### `sightings`

Avisos de personas que vieron una mascota.

Relación:
- `pet_public_code` → `pets.public_code`.

Puede contener:
- mensaje;
- teléfono del hallador;
- zona;
- latitud/longitud;
- consentimientos de ubicación y contacto.

Por contener ubicación y teléfono, debe tratarse como dato privado salvo el flujo expresamente autorizado.

### `short_links`

Respaldo/registro de enlaces físicos cortos, actualmente utilizado por el generador Short.io.

Campos clave:
- `code` único;
- `target_url`;
- `provider`;
- `domain`;
- `short_url` único cuando existe;
- `external_id`;
- `public_code`.

Sirve también para rollback y trazabilidad de lotes físicos.

### `admin_tag_events`

Auditoría de acciones administrativas sobre chapitas.

Registra el estado previo necesario para investigar/resetear operaciones:
- código público;
- acción;
- mascota/propietario previos;
- email/nombre previos;
- fecha previa de activación;
- timestamp del evento.

No debe exponerse al cliente público.

### `app_admin_config`

Configuración privada de administración.

Incluye `key_hash` para validar la credencial administrativa. No debe entregarse al frontend ni concederse a roles públicos.

## Relaciones principales

```text
pending_owner_claims ──tag_id──> tags
pending_owner_claims ──pet_id──> pets

tags ──pet_id──> pets

sightings ──pet_public_code──> pets.public_code
```

`pets.owner_id` referencia conceptualmente al usuario de Supabase Auth, pero actualmente sin constraint FK declarado.

## RLS y privilegios

Estado verificado:
- las 7 tablas del esquema `public` tienen RLS habilitado;
- `anon` y `authenticated` no tienen grants directos de tabla;
- el acceso operativo actual se concentra en Edge Functions/RPCs con controles específicos.

Esto es importante: una policy RLS por sí sola no concede acceso. Si en el futuro se agrega `SELECT` a `anon`/`authenticated`, se debe reauditar inmediatamente qué columnas podrían quedar disponibles.

## Índices

La estructura tiene índices para los caminos críticos:
- búsqueda de chapita por `public_code`;
- mascota por `owner_id`;
- vínculo `tags.pet_id`;
- avisos por mascota y fecha;
- links cortos y código público;
- claims abiertos y expiración.

El Performance Advisor señaló `pending_owner_claims_pet_idx` como índice no utilizado. **No eliminarlo automáticamente**: el volumen actual es pequeño y la métrica de uso todavía no prueba que sea innecesario en flujos excepcionales.

## Deuda de reconstrucción

El esquema vivo contiene estas 7 tablas, relaciones, índices, policies y RPCs, pero el repositorio sólo posee 2 migraciones. Por lo tanto hoy `supabase/migrations/` no es suficiente para reconstruir producción desde cero.

La solución profesional es crear un **baseline controlado del esquema actual**, sin ejecutar cambios sobre producción, y a partir de allí registrar cada modificación futura como migración incremental.

## Reglas para cambios futuros

1. DDL mediante migraciones versionadas, no SQL manual sin registro.
2. No renombrar `public_code` ni cambiar su semántica sin plan de compatibilidad física.
3. No habilitar grants directos a tablas sin reauditar RLS y columnas sensibles.
4. Cambios en `pets` deben probar perfil público + panel privado + modo perdido.
5. Cambios en `tags` deben probar disponible + activa + bloqueada + reset.
6. Cambios en `pending_owner_claims` deben probar expiración y reintentos.
7. Cambios en `short_links` deben preservar rollback de lotes y redirecciones impresas.
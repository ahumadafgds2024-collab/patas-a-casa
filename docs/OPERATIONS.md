# Operación, cambios y despliegues

## Objetivo

Que cualquier problema pueda localizarse rápido y que un cambio pequeño no genere una cadena de parches, workflows temporales y despliegues innecesarios en producción.

## Flujo obligatorio de cambios

```text
main estable
   ↓
rama de trabajo
   ↓
cambio único y acotado
   ↓
preview / pruebas
   ↓
revisión de logs y funciones afectadas
   ↓
merge a main
   ↓
verificación de producción
```

### 1. No trabajar directamente sobre `main`

Todo cambio funcional, visual, de seguridad o infraestructura debe comenzar desde el último `main` estable.

Nomenclatura recomendada:
- `feat/...` nueva función;
- `fix/...` corrección;
- `chore/...` orden/mantenimiento;
- `security/...` endurecimiento;
- `docs/...` documentación.

### 2. Una intención por cambio

Evitar secuencias del tipo:

`preparar script` → `ejecutar workflow` → `corregir workflow` → `retirar script` → `retirar workflow`.

Cada push a `main` genera un despliegue productivo de Vercel. Para cambios de código, preparar todo en una rama y fusionar una sola vez.

### 3. Separar runtime de herramientas

- Runtime web: HTML, JS/CSS y `vercel.json`.
- Runtime backend: `supabase/functions/` y esquema DB.
- Herramientas: `scripts/`, `.github/scripts/`.
- Automatización permanente: `.github/workflows/`.
- Documentación: `docs/`.

Un script de parche no debe convertirse en la única explicación de cómo quedó producción. El resultado final debe existir directamente en el código versionado.

## Checklist antes de merge

### Frontend

- abrir `/?tag=<código-de-prueba>`;
- verificar perfil público;
- verificar nombre/foto/datos visibles;
- verificar WhatsApp/contacto si corresponde;
- probar activación con PIN en un registro de prueba;
- probar inicio de sesión y `mi-cuenta`;
- probar viewport móvil;
- revisar consola del navegador.

### Backend

- revisar logs de las Edge Functions tocadas;
- confirmar códigos HTTP esperados;
- verificar que no se impriman secretos ni datos sensibles en logs;
- comprobar Auth si el cambio toca login/registro;
- ejecutar Security Advisor después de cambios de DB/RLS/RPC;
- ejecutar Performance Advisor si hubo cambios de índices/consultas.

### Chapitas

Nunca aprobar un cambio sin comprobar:
- URL QR existente;
- `public_code` existente;
- PIN existente;
- chapita activa;
- chapita disponible;
- chapita bloqueada, si el cambio toca administración.

## Rollback

Vercel conserva deployments anteriores y permite volver a un deployment estable. Git conserva cada versión del frontend.

Para Supabase, el rollback debe diseñarse por migración/función; no asumir que volver el frontend revierte base de datos o Edge Functions.

Por eso cualquier cambio que modifique simultáneamente frontend + Edge Function + DB debe documentar:
- orden de despliegue;
- compatibilidad hacia atrás;
- cómo volver a la versión anterior.

## Logs y trazabilidad

### Vercel

Usar para:
- estado de deployment;
- errores runtime;
- commit exacto desplegado.

### Supabase

Usar para:
- Edge Function logs;
- Auth logs;
- Postgres/API logs;
- Security/Performance Advisors.

Las funciones nuevas deberían incluir `request_id` o identificador equivalente para seguir una operación de punta a punta.

## Política para componentes obsoletos

No borrar sólo porque el nombre diga `test`, `demo` o `publish`.

Proceso:
1. buscar referencias en GitHub;
2. revisar logs recientes;
3. obtener y versionar el código vivo;
4. marcarlo como `active`, `legacy` o `candidate-for-removal`;
5. probar producción sin depender de él;
6. recién entonces retirar.

## Criterio de finalización

Un cambio está terminado cuando:
- el código final está versionado;
- no quedaron scripts temporales activos;
- no quedaron workflows temporales necesarios para entender el resultado;
- preview y producción pasaron los chequeos relevantes;
- la documentación se actualizó si cambió la arquitectura.

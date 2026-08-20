# Generador Short.io 21x21

- No modifica ni elimina enlaces TinyURL existentes.
- Nuevos lotes usan un subdominio gratuito `*.s.gy` de Short.io.
- El backend calcula el largo máximo del alias para mantener `HTTPS://DOMINIO/ALIAS` dentro de 25 caracteres alfanuméricos.
- El cliente fuerza QR Version 1, corrección L, y rechaza cualquier resultado distinto de 21x21 módulos.
- El backend verifica cada redirección antes de devolver el lote.
- Cada enlace físico se respalda en `public.short_links` con proveedor, dominio, URL corta, ID externo y código público de la chapita.
- Si un lote falla, se eliminan las chapitas nuevas y se intenta borrar también los enlaces Short.io creados durante ese lote.

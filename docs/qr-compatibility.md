# Compatibilidad de QR de chapitas

La corrección usa `https://pac.s.gy/ALIAS` completo, con esquema y dominio en
minúsculas y la ruta intacta. Mantiene Short.io, alias aleatorios de 8 caracteres
para pac.s.gy, destino y activación PAC2011. No migra enlaces existentes.

## Elección del formato

Resultados reproducibles con `npm ci --ignore-scripts` y `npm run test:qr-options`
(qrcode 1.5.1, corrección L):

| Contenido | Modo | Versión / módulos | Decisión |
|---|---|---|---|
| `HTTPS://PAC.S.GY/ABCDEFGH` | Alfanumérico | 1 / 21×21 | Esquema que causa el problema reportado |
| `pac.s.gy/ABCDEFGH` | Byte | 1 / 21×21 | Sin esquema; reconocimiento depende del lector |
| `PAC.S.GY/ABCDEFGH` | Alfanumérico | 1 / 21×21 | También depende de reconocimiento sin esquema |
| `https://pac.s.gy/ABCDEFGH` | Byte | 2 / 25×25 | **Elegido: URL HTTPS convencional** |
| `https://pac.s.gy/ABCDEFGH` | Mixto automático | 2 / 25×25 | No ahorra una versión |
| `https://PAC.S.GY/ABC` | Mixto automático | 1 / 21×21 | Posible, pero reduce alias a 3 caracteres |
| `https://PAC.S.GY/ABCD` | Mixto automático | 2 / 25×25 | 4 caracteres ya no entran |
| `http://PAC.S.GY/ABCDE` | Mixto automático | 1 / 21×21 | Cambia HTTPS por HTTP; descartado |
| `https://pac.s.gy/A` | Byte | 2 / 25×25 | Incluso 1 carácter excede V1-L en byte |
| `https://p.s.gy/AB` | Byte | 1 / 21×21 | Requeriría cambiar el dominio; descartado |

V1-L admite 17 bytes; el prefijo `https://pac.s.gy/` ya ocupa 17.
V2-L admite 32 bytes; el enlace actual de 8 caracteres ocupa 25. El cambio
mínimo elegido es sumar cuatro módulos por lado, conservando HTTPS, dominio y
espacio de alias. Tres caracteres del alfabeto actual ofrecen solamente 32³
combinaciones frente a 32⁸. No se puede declarar imposible todo QR HTTPS de
21×21: sí se puede con compromisos que aquí no convienen.

Se fuerza un solo segmento byte. El cliente normaliza con URL, nunca convierte
la ruta a mayúsculas, y prefiere `short_url` para tolerar respuestas del backend
anterior. El backend verifica por HTTP exactamente `qr_payload` antes de entregar
el lote. Las validaciones, CSV, nombres PNG y LEEME del ZIP dicen V2-L / 25×25.

## Verificación

`npm test` ejecuta el script real de admin y el handler real de la función con
red simulada. Decodifica los PNG y los trazados de ambos SVG con jsQR, comprueba
el límite de 32 bytes, conserva mayúsculas/minúsculas de alias y prueba el lote,
colisiones de alias y reversión por destino incorrecto. No crea chapitas reales.

El 30/09/2026 (Argentina) se decodificó la foto proporcionada:
`HTTPS://PAC.S.GY/ETSU95TB`. Tanto esa URL como
`https://pac.s.gy/ETSU95TB` respondieron 302 de Short.io hacia
`https://www.patasacasa.com.ar/?tag=26C2CAB9`; siguiendo la redirección se obtuvo
200 en `/tag.html?tag=26C2CAB9`. La variante HTTP también redirigió al mismo
destino, pero no se adopta. Un texto sin esquema no constituye una URL absoluta:
que una barra de navegador le agregue HTTPS no demuestra compatibilidad del lector.

Estas pruebas no reemplazan una prueba con la cámara del Samsung afectado y
otros teléfonos. No se afirma compatibilidad universal comprobada ni se ha
validado físicamente el grabado. Se mantienen los dibujos de 15 y 21,5 mm:
los módulos pasan a medir 0,6 y 0,86 mm. Los SVG siguen sin fondo ni margen
incluido; el soporte debe aportar cuatro módulos blancos alrededor del patrón.
Verificar también ese margen cerca de los bordes curvos de la chapita. Los PNG
sí incluyen margen blanco de cuatro módulos.

## Publicación y chapitas existentes

1. Publicar primero el nuevo `admin.html`: funciona con el backend anterior y
   corrige la URL antes de codificarla. Una pestaña vieja debe recargarse.
2. Desplegar `supabase/functions/patas-admin-shortio/index.ts` en el proyecto
   correspondiente. No requiere migraciones ni nuevas claves.
3. Generar un lote de prueba desde el panel y escanear PNG y muestra grabada
   con el Samsung afectado antes de fabricar un lote grande.

Los QR físicos existentes conservan sus bytes: ningún cambio en Short.io puede
corregir la clasificación de un lector que ni siquiera abre la URL. Para esas
unidades, regrabar/reemplazar el QR con la misma URL y ruta, sin crear otro
enlace, otra chapita lógica ni cambiar su activación.

Referencias: [capacidad y versiones de DENSO WAVE](https://www.qrcode.com/en/about/version.html),
[modos y segmentos de node-qrcode](https://github.com/soldair/node-qrcode),
[sensibilidad a mayúsculas en Short.io](https://blog.short.io/case-sensitive/).

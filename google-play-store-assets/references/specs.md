# Google Play — especificaciones de recursos gráficos (referencia completa)

Fuentes oficiales (revisadas en noviembre de 2026):
- Google Play Console Help — *Agregar recursos de vista previa para mostrar tu app*: https://support.google.com/googleplay/android-developer/answer/9866151
- Android Developers — *Google Play icon design specifications*: https://developer.android.com/distribute/google-play/resources/icon-design-specifications

Los **requisitos** son obligatorios: si no se cumplen, la ficha puede ser rechazada, eliminada o suspendida. Las **recomendaciones** no afectan la publicación, pero ignorarlas puede limitar la promoción. Todo el contenido debe cumplir además las Políticas del Programa para Desarrolladores.

---

## Ícono de la app

**Requisitos**
- PNG de 32 bits (con alfa).
- 512 × 512 px.
- 1024 KB como máximo.
- Debe cumplir las especificaciones de diseño de íconos de Google Play.
- Sin insignias ni texto que sugieran ranking, precio o categoría de Play, ni que engañen a los usuarios.

**Especificaciones de diseño**
- Espacio de color sRGB.
- Cuadrado completo. **No** redondees las esquinas ni apliques una máscara: Google Play aplica la máscara dinámicamente, con un radio igual al 30 % del tamaño del ícono.
- **Sin sombra paralela** en el recurso final: Play la agrega al subir el ícono. Las sombras y la iluminación sí pueden ir *dentro* del arte.
- Por defecto, arte a sangre (de borde a borde) con fondo opaco del color de marca. Un fondo transparente muestra el color de la UI de Play, así que evítalo.
- Para logos o arte libre, ubica los elementos en la retícula de keylines en vez de forzarlos a sangre. Un ícono en modo heredado se escala al 75 % (≈ 384 px).
- No fuerces transformaciones drásticas de la marca para llevarla a sangre, y no reduzcas un arte ilustrado a sangre a las keylines.
- No uses texto ni gráficos que indiquen ranking, ofertas o incentivos de instalación, ni que muestren la participación en programas de Play.

**Uso:** ficha de Play Store, resultados de búsqueda y listas de éxitos. Es obligatorio para publicar y es distinto del ícono del launcher.

---

## Gráfico de funciones (feature graphic)

**Requisitos**
- JPEG o PNG de 24 bits (sin alfa).
- 1024 × 500 px.

**Uso:** portada del video de vista previa (excepto en los videos espaciales de XR), colecciones de apps en formato grande (incluidos anuncios) y grupos grandes de juegos recomendados.

**Recomendaciones**
- Muestra la experiencia: la propuesta de valor central, el contexto relevante o elementos de la historia.
- No repitas tu arte de marca de forma que parezca el ícono. Los elementos de marca deben *extender* el ícono.
- Evita los detalles demasiado sutiles, porque muchas pantallas de teléfono no los muestran.
- Mantén el punto focal y las imágenes clave **centrados**. Logos, nombre, eslogan principal y UI clave deben quedar fuera de las zonas de recorte, y los elementos de fondo, en los bordes.
- Usa colores vivos. Evita el blanco puro, el negro y el gris oscuro, que se funden con el fondo de Play.
- Coordina los colores y el tema con el ícono y la app.
- Sin logos ni marcas de terceros sin permiso, sin imágenes de dispositivos y sin íconos ni insignias de Google Play u otras tiendas.
- Localiza los gráficos y el texto de marca.
- Agrega o quita a tiempo el contenido de temporada.
- Texto alternativo de 140 caracteres como máximo, sin "foto de" ni "imagen de".

---

## Screenshots

**Cantidad:** hasta 8 por tipo de dispositivo (teléfonos, tablets de 7" y 10", Chromebooks, Android TV, Wear OS, Android Automotive OS y Android XR). Para publicar se necesitan **al menos 2** en total.

**Requisitos técnicos generales**
- JPEG o PNG de 24 bits (sin alfa).
- Lado mínimo de 320 px y máximo de 3840 px.
- El lado largo no puede superar el doble del lado corto.

**Por tipo de dispositivo**

| Dispositivo | Reglas |
|---|---|
| Chromebook y tablets (pantallas grandes) | Mín. 4. Lados de 1080 a 7680 px. 16:9 horizontal o 9:16 vertical. Excluye el texto que no sea parte de la experiencia central de la app. |
| Wear OS (apps) | Mín. 1 que refleje la versión actual. Solo la UI de la app: sin marcos de dispositivo, texto extra, gráficos ni fondos. 1:1, mín. 384 × 384. Se recomienda mostrar Tiles. Sin fondos transparentes ni máscaras. |
| Wear OS (watch faces) | Mín. 1 de la versión actual. Si es personalizable, muestra más de una opción. Solo la experiencia de la esfera, con las mismas restricciones. 1:1, mín. 384 × 384. |
| Android TV | Al menos 1 screenshot de TV es obligatorio para publicar, además del banner de TV. Solo se ven en dispositivos TV. (La guía no fija una medida; usa 1920 × 1080.) |
| Android Automotive OS | Obligatorio fuera de las categorías "vehículo estacionado"; opcional (pero recomendado) dentro de ellas. UI genérica del sistema, no la de fabricantes. Captura con la imagen genérica del sistema y los perfiles de emulador *Automotive (1024p landscape)* y *Automotive Portrait*. Si los incluyes: mín. 2 verticales de 800 × 1280 y 2 horizontales de 1024 × 768. |
| Android XR | De 4 a 8. 8:5. Máx. 8 MB cada uno. Recomendado 3840 × 2400 (mín. 1920 × 1200). PNG o JPEG. |

**Elegibilidad para los formatos de recomendación y promoción** (obligatorio para aparecer en ellos)
- **Apps:** al menos 4 screenshots con una resolución mínima de 1080 px. Horizontal: mín. 1920 × 1080 (16:9). Vertical: mín. 1080 × 1920 (9:16).
- **Juegos:** al menos 3 horizontales (mín. 1920 × 1080) o 3 verticales (mín. 1080 × 1920), que muestren la experiencia de juego real.

**Recomendaciones de contenido**
- Muestra la experiencia real de la app o el juego, centrada en las funciones y el contenido principales.
- Se permiten screenshots estilizados que dividen la UI entre varias imágenes. Prioriza la UI en las 3 primeras.
- Agrega leyendas solo si hacen falta. No pueden superar el 20 % de la imagen. Sin claims de ranking, premios, precio o promociones, y sin llamadas a la acción. Evita la letra chica y los fondos recargados.
- Limpia la barra de estado: oculta el operador y las notificaciones, y muestra la señal, la batería y el Wi-Fi llenos.
- Imágenes de alta calidad y en la relación correcta: nada borroso, distorsionado, pixelado, estirado ni comprimido (salvo intención), y con la rotación correcta.
- Sin logos ni marcas de terceros sin permiso, sin imágenes de dispositivos y sin íconos ni insignias de tiendas.
- Localiza el texto superpuesto y el de marca. La UI de un juego no requiere localización por mercado, pero las leyendas agregadas sí.
- Texto alternativo de 140 caracteres como máximo, sin "foto de" ni "imagen de".

---

## Video de vista previa

- Es opcional pero recomendado, sobre todo para juegos: los juegos necesitan video para aparecer en algunas secciones de Play.
- Se agrega como URL de YouTube de un solo video: ni playlist ni canal, y sin parámetros como marcas de tiempo.
- **Requisitos:** anuncios desactivados (sin monetización ni reclamos de monetización); si tiene contenido con copyright, usa otro video; privacidad pública u oculta (no privada); sin restricción de edad; insertable.
- **Recomendaciones:**
  - Fija expectativas reales y muestra el uso real, con las funciones clave en los primeros 10 s.
  - Al menos el 80 % del video debe ser experiencia de usuario. Limita las pantallas de título, los logos y las cinemáticas.
  - Que sea corto: solo los primeros 30 s se reproducen automáticamente (en silencio).
  - No muestres personas tocando el dispositivo, salvo que el uso principal sea fuera de él.
  - Producción de calidad.
  - Vertical u horizontal, según lo que mejor le quede a la app, y sin barras negras en los videos verticales.
  - Texto superpuesto para verlo sin sonido, con las mismas reglas de contenido (los premios de Google Play pueden mostrarse con la fórmula "lo mejor de"), más subtítulos.
  - Localiza el audio, la UI y las descripciones.
- **Uso:** aparece antes de los screenshots, y se reproduce al tocar el gráfico de funciones. También puede aparecer en la página principal y en la búsqueda.

## Videos de Android XR

- **Espacial (opcional):** URL de YouTube con video de 360°, 180° o 3D, público u oculto, sin restricción de edad y sin anuncios. La miniatura de YouTube se usa como portada. Solo se ve en visores XR.
- **No espacial (opcional):** mismas reglas. Se ve en visores XR y en la sección XR de la ficha en teléfonos y tablets. Si existe, reemplaza al video normal en los visores XR.
- Se pueden agregar hasta 2 videos XR adicionales.

## Banner de TV

- Obligatorio para publicar una app de Android TV. Es el "ícono" de la app en TV.
- JPEG o PNG de 24 bits (sin alfa).
- 1280 × 720 px.
- Solo se ve en dispositivos Android TV.

## Descripción breve

- 80 caracteres como máximo.
- Resume el propósito principal en lenguaje simple y destaca qué la hace única. Evita la jerga.
- No repitas los mensajes de los screenshots, del gráfico de funciones ni del video.
- Mantenla vigente y evita las frases de tiempo limitado.
- Sin claims de ranking, premios, precio ni promociones ("el mejor", "N.º 1", "nuevo", "descuento", "gratis"), sin llamadas a la acción y sin relleno de palabras clave.
- Localízala por idioma y mercado.
- **Formato:**
  - Punto final solo si hay varias oraciones.
  - Se permiten letras, puntos, comas, "&" y espacios, además de los caracteres propios del idioma (¿, ¡, æ, Ø).
  - Se prohíben los caracteres especiales, los saltos de línea, los emojis, los emoticones, la puntuación repetida y los símbolos ★/☆.
  - Se permiten © ® ™ cuando corresponda.
  - Nada de mayúsculas sostenidas para enfatizar: las siglas sí pueden ir en mayúsculas, y el nombre de la app solo si así aparece en Google Play.

## Localización

Localiza los gráficos y el texto de marca, el audio y la UI del video, las leyendas de los screenshots y el texto superpuesto, para cada idioma y mercado.

## Marketing y licencias

Al publicar, le otorgas a Google una licencia para usar los recursos de la ficha (ícono, screenshots, videos, etc.) con fines promocionales (sección 6 del Acuerdo de Distribución para Desarrolladores). Puedes desmarcar "Marketing externo" en la configuración de la tienda para limitar la promoción fuera de Play.

---

## Medidas recomendadas por esta skill (dentro de los rangos oficiales)

| Recurso | Medida de salida | Por qué |
|---|---|---|
| Ícono | 512 × 512, PNG RGBA opaco | Exacta |
| Gráfico de funciones | 1024 × 500, PNG RGB | Exacta |
| Teléfono | 1440 × 2560 (9:16) | ≥ 1080 para promoción, ≤ 3840, relación ≤ 2:1 |
| Tablet 7"/10" y Chromebook | 2560 × 1440 (16:9) | Entre 1080 y 7680, 16:9 |
| Wear OS | 456 × 456 o la captura nativa 1:1 | ≥ 384, 1:1 |
| TV | 1920 × 1080 | 16:9 estándar de TV |
| Banner de TV | 1280 × 720 | Exacta |
| Automotive | 800 × 1280 y 1024 × 768 | Exactas |
| XR | 3840 × 2400 (8:5) | Recomendada, ≤ 8 MB |

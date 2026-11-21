# Agent Skills — recursos gráficos para tiendas de apps

Skills para agentes de código (Claude Code, Codex, Antigravity y otros que lean `SKILL.md`). Leen la marca directamente del código del proyecto (colores, fuentes, logo, textos y pantallas) y generan los recursos gráficos de cada tienda en las medidas oficiales.

| Skill | Tienda | Qué genera |
|---|---|---|
| [`google-play-store-assets`](google-play-store-assets/SKILL.md) | Google Play | Ícono 512×512, gráfico de funciones 1024×500, screenshots (teléfono, tablet, Chromebook, Wear OS, TV, Automotive, XR), banner de TV, descripción breve y textos alternativos |
| [`app-store-image-prompts`](app-store-image-prompts/SKILL.md) | Apple App Store | Ícono 1024×1024, cabecera 3840×1646, búsqueda 3840×2560, universal 5244×2950, screenshots de iPhone, iPad y Mac |

Las dos comparten el formato de `brand.json`, así que generar una tienda después de la otra mantiene la misma identidad.

## Uso

Dentro del proyecto, pídele al agente cosas como:

```
hazme el ícono de Play
hazme el feature graphic
hazme los screenshots de teléfono y tablet
hazme la cabecera del App Store
hazme el kit completo de Google Play
```

El agente:
1. extrae la marca del repo;
2. detecta los dispositivos soportados;
3. genera el arte con el motor disponible: su herramienta de imágenes, una API (`OPENAI_API_KEY`, `GEMINI_API_KEY`, `REPLICATE_API_TOKEN`) o arte hecho con código;
4. captura las pantallas reales (`adb`, `simctl` o Playwright);
5. compone cada archivo en píxeles exactos;
6. lo valida.

## Instalación

Copia la carpeta de cada skill (con su `SKILL.md`, `scripts/`, `templates/` y `references/`) al directorio de skills de tu agente. Por ejemplo, en Claude Code:

```bash
# Para todos tus proyectos
cp -r google-play-store-assets app-store-image-prompts ~/.claude/skills/
# o solo para un proyecto
cp -r google-play-store-assets app-store-image-prompts <proyecto>/.claude/skills/
```

Para Codex, Antigravity u otros agentes, usa la carpeta de skills que indique su documentación.

## Requisitos

- Node 18+ y Playwright (`npm i -D playwright && npx playwright install chromium`) para componer.
- Python 3 y Pillow (`pip install pillow`) para el validador de Google Play.
- Opcional: Android SDK (`adb`, emuladores) o Xcode (`xcrun simctl`) para las capturas reales.

## Fuentes de las especificaciones

- Google Play: [Agregar recursos de vista previa](https://support.google.com/googleplay/android-developer/answer/9866151) · [Icon design specifications](https://developer.android.com/distribute/google-play/resources/icon-design-specifications)
- Apple: [Creative assets specifications](https://developer.apple.com/help/app-store-connect/reference/app-information/creative-assets-specifications) · [Screenshot specifications](https://developer.apple.com/help/app-store-connect/reference/screenshot-specifications) · [HIG: App icons](https://developer.apple.com/design/human-interface-guidelines/app-icons)

Especificaciones revisadas en noviembre de 2026. Las tiendas las cambian: verifícalas antes de publicar.

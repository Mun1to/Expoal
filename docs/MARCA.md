# Marca de Expoal

Identidad visual del producto. Si tocas colores o iconos, actualiza también este documento.

## Logotipo

Un **triángulo de play azul** encajado dentro de una **flecha de descarga negra**. Cuenta el
producto de un vistazo: coges un vídeo (play) y te lo llevas a tu disco (flecha abajo).

| Archivo | Para qué |
|---|---|
| `assets/brand/logo-original.png` | Original tal cual lo entregó Munir (2000x2000, transparente). No tocar: es la fuente. |
| `assets/logo.png` | Maestro de trabajo (1024 px, transparente). De aquí salen todos los iconos. |
| `assets/logo-512.png` | Logo suelto sin lienzo, para usar sobre fondos claros. |
| `assets/expoal.ico` | Icono de Windows multi-resolución (16 a 256 px): `.exe`, instalador y carpeta. |
| `assets/icon-256.png` | Icono con lienzo para el README y el favicon. |
| `src/expoal/web/logo.png` · `site/assets/logo.png` | Logo suelto (transparente) para las cabeceras de la app y de la web. |

Los iconos **se generan, no se editan a mano**:

```bash
uv run python scripts/make_brand.py
```

Cuándo lleva lienzo y cuándo no:

- **Sin lienzo (logo suelto)** dentro de la app y de la web, donde el fondo lo controlamos
  nosotros. Es lo que mejor se ve: el play azul destaca y el negro hace de contorno.
- **Con lienzo blanco redondeado** cuando el logo sale a un fondo que no controlamos: icono del
  `.exe`, del instalador, de la carpeta y favicon. Ahí el lienzo es imprescindible, porque el logo
  es negro y se perdería sobre una barra de tareas oscura.

## Colores

| Color | Hex | Uso |
|---|---|---|
| Azul Expoal | `#0069FF` | Color principal. Sale del propio logo (extraído del píxel azul dominante). Botones, focos, enlaces activos. |
| Azul claro | `#3B87FF` | Estado *hover* en tema oscuro. |
| Azul profundo | `#0060EB` / `#0050C8` | Principal y *hover* en tema claro (más oscuro para que contraste sobre blanco). |
| Ámbar | `#E8B84B` | Acento secundario: avisos, insignias, destacados. |
| Azul noche | `#0B0F1F` | Fondo del tema oscuro y de la web. Hermana con el negro del logo. |
| Texto | `#E9EDF8` (oscuro) / `#101A3D` (claro) | Texto principal. |

La paleta vive en un único sitio por superficie: las variables CSS de `src/expoal/web/styles.css`
(la app, con sus dos temas) y las de `site/index.html` (la web, siempre oscura).

## Tono

- **Nombre del producto:** Expoal. **Lema:** «Del link a tu disco».
- Trato directo y sin humo: «Pega un enlace y el vídeo cae en tu disco».
- Se presume de lo que de verdad importa al usuario: **100% local**, open source, gratis.
- Interfaz en español; README, commits y notas de versión en inglés.
- Nada de rayas largas ni flechas tipográficas en los textos de cara al público.

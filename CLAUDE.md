# CLAUDE.md — Gigathon Abismo

> Este archivo lo lee Claude Code automáticamente en cada sesión dentro del repo.
> Mantenlo conciso. La especificación detallada vive en el Claude Project (Project Knowledge).

## Qué es esto

Submission para Gigathon 2026 Python III etapa. Simulador en terminal de una expedición
submarina: el submarino *Abismo* busca al buque desaparecido *Atalaya* en una fosa abisal.

## Reglas duras (no negociables)

- **Python 3.11**, solo biblioteca estándar. Cero `pip install`.
- **Máx. 10 archivos, ≤200 kB total.**
- **Sin Internet.**
- **Texto plano en terminal.** Sin ANSI, sin emojis.
- **Strings de usuario en español.** Código y comentarios en inglés.
- Punto de entrada: `python main.py`.

## Estructura de archivos

```
main.py        # Entry point + restart loop
game.py        # Turn loop, end-condition evaluation
entities.py    # Submarine, World, element classes
events.py      # Random events pool + dispatcher
ui.py          # Input validation, prompts, turn formatting
report.py      # Final report builder
config.json    # All tunable constants and tables
README.md      # Spanish run instructions
```

## Reglas de implementación

- Datos en `config.json`, lógica en `.py`. No hard-codear números en la lógica.
- Validación de entrada en `ui.py`. Re-prompt + default tras 3 intentos.
- Sin tracebacks visibles al usuario en flujo normal.
- Type hints en funciones públicas.
- `snake_case` funciones/variables, `PascalCase` clases, `UPPER_CASE` constantes.

## Cómo trabajar

1. Lee la sección relevante del Project Knowledge antes de implementar.
2. Implementa un archivo a la vez en el orden de `03-progress.md`.
3. Ejecuta `python main.py` o un test puntual tras cada cambio.
4. Si encuentras una decisión de diseño no cubierta por el spec: **para y pregunta** al
   usuario. No improvises mecánicas nuevas.
5. Tras cada archivo terminado: commit con mensaje claro
   (ej. `feat: implement entities.py`).

## Estado actual

Ver `Project Knowledge / 03-progress.md` para el checklist en vivo.

## Anti-patrones

- Añadir features no especificadas → **no**, pregunta primero.
- Importar librerías externas → **no**, solo stdlib.
- Mensajes en inglés al usuario → **no**, todo en español.
- Variables globales → **no**, excepto constantes cargadas de config.
- Print de tracebacks al usuario → **no**, manejar con mensaje claro.
Estamos construyendo una entrega para Gigathon 2026. Consulta siempre 01-spec.md antes de proponer cambios. Si una decisión no está cubierta por la spec, pregunta antes de improvisar. Strings de usuario en español, código en inglés. Solo stdlib de Python 3.11. zero comentarios en el codigo a menos que se hayan pedido explicitamente, y en ese caso, hacerlos basicos sin el toque obvio de IA

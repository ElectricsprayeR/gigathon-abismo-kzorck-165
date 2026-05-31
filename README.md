# ABISMO — Mision de Rescate

## Descripcion

*Abismo* es un simulador de expedicion submarina en terminal. El jugador pilota el
submarino *Abismo* con la mision de localizar al buque desaparecido *Atalaya* en el
fondo de una fosa abisal. Cada turno consume recursos escasos; la supervivencia depende
de tomar decisiones precisas en un entorno hostil y poco conocido.

## Requisitos

- Python 3.11
- Sin dependencias externas (solo biblioteca estandar)

## Ejecucion

```
python main.py
```

## Como jugar

### Parametros iniciales

Al comenzar la partida el juego solicita:

- **Nombre del capitan** — identificador que aparece en el informe final.
- **Semilla aleatoria** — numero entero que fija la disposicion del mundo; la misma
  semilla reproduce siempre el mismo escenario.
- **Dificultad** — `facil`, `normal` o `dificil`. Afecta el oxigeno inicial, el limite
  de turnos, la frecuencia de eventos y la zona de busqueda del *Atalaya*.

### Acciones disponibles

En cada turno el jugador elige una accion:

| Accion    | Efecto |
|-----------|--------|
| `N`       | Mover el submarino hacia el norte (sube en el eje vertical). |
| `S`       | Mover el submarino hacia el sur (desciende en el eje vertical). |
| `E`       | Mover el submarino hacia el este. |
| `O`       | Mover el submarino hacia el oeste. |
| `escanear`| Revela los elementos presentes en un radio de 10 unidades. Consume 5 de bateria. |
| `esperar` | El submarino permanece quieto y repara el casco (+5). Consume 2 de bateria y 2 de oxigeno. |
| `salir`   | Abandona la mision de forma voluntaria (cuenta como fracaso). |

### Recursos a gestionar

- **Oxigeno** — se consume cada turno; a mayor profundidad, el consumo aumenta. Llegar a
  cero es mortal.
- **Bateria** — necesaria para maniobrar y usar el sonar. Sin bateria el submarino queda
  inoperativo.
- **Casco** — integridad estructural del submarino. Ciertos elementos y eventos lo danan.
  Si llega a cero la mision termina.

## Mecanicas

### Elementos del mundo

El fondo oceanico esta poblado por elementos de distintos tipos, cada uno con efectos
propios al entrar en contacto con el submarino: fuentes hidrotermales, restos de
naufragios, corrientes abisales, calamares gigantes, cuevas submarinas y bolsas de
presion, entre otros.

### Eventos aleatorios

Durante la expedicion pueden ocurrir eventos impredecibles que alteran el estado del
submarino o del entorno. Su frecuencia varia segun la dificultad elegida.

### Condiciones de finalizacion

La mision puede terminar de las siguientes formas:

- **Victoria completa** — el *Atalaya* es localizado y el submarino regresa a la base con
  todos los recursos en positivo.
- **Fracaso por agotamiento de oxigeno** — el nivel de oxigeno llega a cero.
- **Fracaso por perdida de integridad del casco** — el casco queda completamente danado.
- **Fracaso por turnos agotados** — se supera el limite de turnos sin completar la mision.
- **Salida voluntaria** — el capitan abandona la mision.

En algunos casos, haber localizado el *Atalaya* antes de perder puede alterar la
calificacion del resultado final.

## Estructura del proyecto

```
main.py       Punto de entrada y bucle de reinicio entre partidas.
game.py       Bucle de turnos, aplicacion de acciones y evaluacion de fin de mision.
entities.py   Clases Submarine, World y Element; representacion del estado del juego.
events.py     Catalogo de eventos aleatorios y logica de disparo.
ui.py         Validacion de entrada, prompts iniciales y formateo de cada turno.
report.py     Construccion e impresion del informe final de mision.
config.json   Constantes configurables: recursos, dificultades, elementos y eventos.
README.md     Este archivo.
```

## Notas

- Toda la interfaz es texto plano; no se requiere soporte de colores ni caracteres
  especiales en la terminal.
- El juego no guarda partidas en curso; si el proceso se interrumpe la sesion se pierde.
- Ante una entrada invalida reiterada el juego aplica el valor por defecto indicado en
  cada prompt.

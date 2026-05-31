# ABISMO — Simulador de expedicion submarina

El submarino *Abismo* desciende a la fosa abisal para localizar al buque desaparecido *Atalaya*.
Cada turno gasta recursos; la profundidad acelera el consumo de oxigeno y los eventos
aleatorios ponen a prueba al capitan. Localiza el Atalaya y regresa a la base para ganar.

## Requisitos

- Python 3.11
- Sin dependencias externas (solo biblioteca estandar)
- Sin conexion a Internet

## Ejecucion

```
python main.py
```

## Acciones disponibles

| Accion   | Efecto                                      |
|----------|---------------------------------------------|
| N        | Mover norte (+y, subir)  [-1 bateria]       |
| S        | Mover sur   (-y, bajar)  [-1 bateria]       |
| E        | Mover este  (+x)         [-1 bateria]       |
| O        | Mover oeste (-x)         [-1 bateria]       |
| escanear | Revelar elementos en radio 10  [-5 bateria] |
| esperar  | Reparar casco +5  [-2 bateria, -2 oxigeno]  |
| salir    | Abandonar la mision                         |

## Condiciones de finalizacion

| Codigo       | Descripcion                                                    |
|--------------|----------------------------------------------------------------|
| WIN_FULL     | Atalaya localizado y regreso a la base con recursos positivos  |
| WIN_PARTIAL  | Atalaya localizado pero no se logro regresar a la base         |
| LOSE_HULL    | El casco llego a cero: implosion                               |
| LOSE_OXY     | El oxigeno llego a cero: asfixia                               |
| LOSE_BOUNDS  | Cinco salidas del area de operaciones                          |
| LOSE_STEPS   | Limite de turnos agotado sin completar objetivos               |
| QUIT         | Mision abandonada voluntariamente                              |

## Notas

- Solo stdlib de Python 3.11; cero `pip install`.
- Sin acceso a Internet en tiempo de ejecucion.
- Toda la configuracion de la partida se encuentra en `config.json`.

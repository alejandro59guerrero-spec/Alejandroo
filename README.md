# Football Brain · Apuestas en vivo

Análisis de mi historial real de Ecuabet, validación de patrones en partidos terminados
y app para registrar apuestas simples, sincronizada entre PC y celular.

## App

https://claude.ai/artifact/EauH887JCpSi3r6ZDTTCHz

Se abre con la misma cuenta de claude.ai en la PC y en el celular. Los datos viven en la
base de datos del artifact. Código en `app/index.html`.

- **Registrar**: con marcador, minuto, roja, mercado y cuota calcula la probabilidad, la
  cuota mínima y el valor esperado, y da un veredicto: Entrar, Cuota justa o No entrar.
  Opcional: cuotas prepartido 1X2 (para Ganador) y promedios de goles a favor y en contra
  de cada equipo, como los de scores24 (para Más de goles y Ambos marcan).
  Pide confirmación extra si es un anti-patrón o si saltaste tus límites del día.
- **Panel**: curva de banca, caída máxima, racha, acierto por patrón con progreso hacia
  30 apuestas, disciplina (con regla contra sin regla), cortes por liga, mercado y minuto,
  ajustes y exportación a CSV.
- **Patrones**: fichas claras con cuándo entrar, cuándo no, de cada 10 veces cuántas salió,
  cuota mínima y mejores ligas.
- **Mapa**: qué pasó en partidos reales según minuto, goles y diferencia; fiabilidad del
  modelo y tabla "Tus ligas" (tu historial y tasas base de cada liga).
- **Historial**: los 45 tickets del PDF con marcador al apostar y probabilidad del modelo.

## Análisis

```
python -m fb.cli reporte          # reports/analisis_v2.md, patterns/modelo.json, patterns/datos_app.json
python -m fb.cli inyectar-app     # mete los datos en app/index.html antes de publicar
python -m unittest discover -s tests
```

Solo usa Python estándar (3.10+).

- `data/backtest/partidos.csv`: partidos terminados con cada gol y roja al minuto y su fuente.
  `origen=historial` son los partidos donde aposté y no cuentan para validar patrones.
- `data/tickets.csv` y `data/legs.csv`: el historial del PDF con el marcador reconstruido.
- `patterns/patrones.json`: fuente única de reglas. La leen Python y la app.
- `fb/`: modelo de Poisson en vivo, backtest, mapa, descubrimiento de patrones, Sofascore.

## Escáner en vivo (en la PC)

```
python -m fb.cli en-vivo --servir 8765          # tus ligas, escanea cada 60 s
python -m fb.cli en-vivo --servir 8765 --todas  # todas las ligas
```

Lee los partidos en juego de Sofascore, calcula minuto, marcador y rojas, y lista las apuestas
que encajan con P1, P2, P3, P5 o P6 con su probabilidad y cuota mínima. En verde, 75% o más.
La página se abre en la PC (`http://localhost:8765/en_vivo.html`) y en el celular conectado a la
misma WiFi (la dirección se imprime al arrancar). Las ligas de "tus ligas" están en
`patterns/ligas.json`.

## Sofascore (datos completos: tiros, xG, presión)

Desde la nube de Claude está bloqueado hasta habilitar `api.sofascore.com` en Network access.
En la PC funciona directo:

```
python -m fb.cli sofascore-probar
python -m fb.cli buscar --fecha 2026-09-27 --equipo Criciuma
python -m fb.cli descargar --torneo <id> --temporada <id> --paginas 10
```

Los datos quedan en `data/sofascore/*.csv`, que DuckDB lee con `read_csv_auto`.

## Reglas duras

Solo apuestas simples. Stake plano del 5% de la banca con tope de $1. Entrar solo si la cuota
supera la cuota mínima. Ningún patrón está probado todavía con muestra grande.

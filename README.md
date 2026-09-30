# Football Brain · Apuestas en vivo

Análisis de mi historial real de Ecuabet y app para registrar apuestas simples nuevas,
sincronizada entre PC y celular.

## App

https://claude.ai/artifact/EauH887JCpSi3r6ZDTTCHz

Se abre con la misma cuenta de claude.ai en el navegador de la PC y del celular. Los datos
viven en la base de datos del artifact, así que lo que registras en un dispositivo aparece
en el otro. El código fuente está en `app/index.html`.

Pestañas:
- **Registrar**: marcador, minuto, roja, ritmo, mercado, cuota y stake. Detecta el patrón en vivo
  y avisa si caes en un anti-patrón o si el stake supera el stake plano.
- **Panel**: banca, neto, ROI, acierto, racha y acierto por patrón.
- **Apuestas**: lista con botones para cerrar como ganada, perdida, nula o cash-out.
- **Patrones**: regla exacta, tasa histórica, intervalo de confianza y límite de cada patrón.
- **Historial**: los 45 tickets del PDF con el marcador al minuto de cada pata.

## Análisis

```
python3 analysis/validar_patrones.py
```

Solo usa Python estándar. Lee `data/tickets.csv` y `data/legs.csv`, y escribe
`reports/analisis_patrones.md` y `data/legs_enriquecido.csv`.

- `data/tickets.csv`: 45 tickets del 19 al 29/09/2026 tal como salen del PDF.
- `data/legs.csv`: 78 patas. Incluye el marcador al minuto de apostar reconstruido con fuentes web,
  la roja previa, la confianza y el enlace a la fuente.

## Reglas duras

Solo apuestas simples. Stake plano del 5% de la banca con tope de $1. Ningún patrón está probado
todavía: todos tienen menos de 10 casos. Se validan con las apuestas nuevas que registre la app.

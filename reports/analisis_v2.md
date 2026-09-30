# Football Brain · Análisis v2

Generado el 2026-09-30 05:47 con `python -m fb.cli reporte`.

## 1. De dónde salen los datos

- Partidos terminados con todos los goles al minuto: 92.
- De ellos, 57 son partidos ajenos a tus apuestas. Solo esos validan patrones.
- Los otros son los partidos donde apostaste. Sirven para el modelo, no para darte la razón.
- Fuente: crónicas y fichas de prensa encontradas por búsqueda web, una por partido, con enlace en el CSV.
- Cada partido se verificó: la lista de goles debe sumar exactamente el marcador final.

## 2. El modelo en vivo

Estima cuántos goles faltan según el minuto, la liga y si hubo roja. Con eso calcula la probabilidad de cada mercado y la cuota mínima para que la apuesta valga la pena.

- Validación cruzada en 460 predicciones de 'llega al menos un gol más'.
- Brier score 0.203 contra 0.235 de adivinar siempre la media. Menor es mejor.

| Probabilidad del modelo | Casos | Media predicha | Ocurrió |
|---|---|---|---|
| 20% a 40% | 94 | 33% | 36% |
| 40% a 60% | 113 | 51% | 53% |
| 60% a 80% | 158 | 70% | 69% |
| 80% a 100% | 95 | 86% | 87% |

- Roja: 16 goles observados tras la roja contra 21.9 esperados.
- Tras la roja marcó el equipo con uno más 16 veces y el de 10 0 veces.
- Goles por partido en la muestra: 2.63 en 92 partidos.
- Límite: el modelo no conoce la fuerza de cada equipo. En apuestas a ganador subestima al favorito.
  La app pide la cuota prepartido del favorito para corregirlo.

## 3. Patrones

| Código | Patrón | Backtest | Tu historial | Cuota mínima | Semáforo |
|---|---|---|---|---|---|
| P1 | Over con partido abierto | 25/33 (76%) | 6/7 | 1.37 | ambar |
| P2 | Ganador al equipo que ya gana | 42/50 (84%) | 5/5 | 1.23 | verde |
| P3 | Roja: apostar a goles | 4/4 (100%) | 7/9 | 1.33 | rojo |
| P4 | Roja: ganador al que tiene uno más | 2/3 (67%) | 3/7 | 1.75 | rojo |
| A1 | Ganador con el partido empatado | 20/30 (67%) | 6/14 | — | ambar |
| A2 | Over que pide 2 goles con 0:0 | 8/17 (47%) | 1/4 | 2.10 | rojo |
| A3 | Córners | sin datos | — | — | rojo |

Semáforo: rojo con menos de 30 casos en total; ámbar si el intervalo toca el break-even de tus cuotas; verde si el límite inferior lo supera.

### P1 · Over con partido abierto

El partido ya tiene goles y solo te falta uno para ganar.

**Entra solo si:**
- Apuestas a Más de X goles
- Ya hay 2 goles o más en el marcador
- Te falta 1 solo gol para ganar la línea
- Vas en el minuto 75 o antes

**No entres si:**
- El partido va 0:0 o 1:0
- Te faltan 2 goles o más
- Ya pasó el minuto 75

**En partidos ajenos:** se cumplió 25 de 33 veces (76%), intervalo 95% de 59% a 87%. El modelo esperaba 71%. De cada 10 veces, unas 8 salen bien.
**Cuota mínima para entrar:** 1.37. Con una cuota menor pierdes dinero a la larga aunque aciertes seguido.
**Ligas donde mejor funcionó** (tasa ajustada por tamaño de muestra): Países Bajos Eredivisie 3/3, Brasil Serie B 7/8, Bolivia Primera 2/2, Inglaterra Premier League 1/1.
**En tus apuestas:** 6 de 7, cuota media 1.48, neto +1.88 unidades.

### P2 · Ganador al equipo que ya gana

Apuestas a que gana el equipo que ya va arriba en el marcador.

**Entra solo si:**
- Apuestas Ganador (1x2)
- Tu equipo va ganando por 1 gol o más
- Mejor si la ventaja es de 2 goles o si ya pasó el minuto 60

**No entres si:**
- El partido está empatado
- La cuota es menor a la cuota mínima de la tabla
- El rival acaba de descontar y empuja

**En partidos ajenos:** se cumplió 42 de 50 veces (84%), intervalo 95% de 71% a 92%. El modelo esperaba 76%. De cada 10 veces, unas 8 salen bien.
**Cuota mínima para entrar:** 1.23. Con una cuota menor pierdes dinero a la larga aunque aciertes seguido.
**Ligas donde mejor funcionó** (tasa ajustada por tamaño de muestra): Perú Liga 1 7/7, Bolivia Primera 2/2, Paraguay Primera 1/1, Inglaterra Premier League 1/1.
**En tus apuestas:** 5 de 5, cuota media 1.51, neto +2.57 unidades.

### P3 · Roja: apostar a goles

Tras una expulsión el partido se abre. Se apuesta a que llegan más goles.

**Entra solo si:**
- Hubo una roja antes de apostar
- Apuestas Más de goles o Ambos marcan
- Te falta 1 solo gol para ganar

**No entres si:**
- Te faltan 2 goles o más
- Quedan menos de 15 minutos

**En partidos ajenos:** se cumplió 4 de 4 veces (100%), intervalo 95% de 51% a 100%. El modelo esperaba 72%. De cada 10 veces, unas 10 salen bien.
**Cuota mínima para entrar:** 1.33. Con una cuota menor pierdes dinero a la larga aunque aciertes seguido.
**Ligas donde mejor funcionó** (tasa ajustada por tamaño de muestra): Colombia Primera A 1/1, Perú Liga 1 1/1, Paraguay Primera 1/1, Brasil Serie A 1/1.
**En tus apuestas:** 7 de 9, cuota media 1.65, neto +2.32 unidades.

### P4 · Roja: ganador al que tiene uno más

El rival se quedó con 10 y el partido sigue empatado.

**Entra solo si:**
- El rival de tu equipo tiene una roja
- El partido está empatado
- Tu equipo domina y llega

**No entres si:**
- Pasó el minuto 70 y sigue 0:0
- La cuota es menor a la cuota mínima de la tabla

**En partidos ajenos:** se cumplió 2 de 3 veces (67%), intervalo 95% de 21% a 94%. El modelo esperaba 59%. De cada 10 veces, unas 7 salen bien.
**Cuota mínima para entrar:** 1.75. Con una cuota menor pierdes dinero a la larga aunque aciertes seguido.
**Ligas donde mejor funcionó** (tasa ajustada por tamaño de muestra): Colombia Primera A 1/1, Paraguay Primera 1/1, Brasil Serie A 0/1.
**En tus apuestas:** 3 de 7, cuota media 2.19, neto -0.13 unidades.

### A1 · Ganador con el partido empatado

Apostar a un ganador cuando el marcador está igualado.

**No entres si:**
- El marcador está empatado: usa Doble oportunidad o espera el gol

**En partidos ajenos:** se cumplió 20 de 30 veces (67%), intervalo 95% de 49% a 81%. El modelo esperaba 58%. De cada 10 veces, unas 7 salen bien.
**Ligas donde mejor funcionó** (tasa ajustada por tamaño de muestra): Brasil Serie A 3/4, Perú Liga 1 3/4, Países Bajos Eredivisie 2/3, Argentina Liga Profesional 2/3.
**En tus apuestas:** 6 de 14, cuota media 2.00, neto -2.19 unidades.

### A2 · Over que pide 2 goles con 0:0

Con 0:0 suele llegar un gol, pero dos ya es otra cosa.

**No entres si:**
- El partido va 0:0 y tu línea necesita 2 goles o más (Más de 1.5 o mayor)
- Si quieres entrar con 0:0, la línea debe pedir 1 solo gol (Más de 0.5) y la cuota superar la mínima

**En partidos ajenos:** se cumplió 8 de 17 veces (47%), intervalo 95% de 26% a 69%. El modelo esperaba 41%. De cada 10 veces, unas 5 salen bien.
**Cuota mínima para entrar:** 2.10. Con una cuota menor pierdes dinero a la larga aunque aciertes seguido.
**Ligas donde mejor funcionó** (tasa ajustada por tamaño de muestra): Brasil Serie A 3/3, Argentina Liga Profesional 1/1, Colombia Primera A 3/5, Brasil Serie B 1/4.
**En tus apuestas:** 1 de 4, cuota media 1.68, neto -2.15 unidades.

### A3 · Córners

Más de córners sin datos de córners al minuto.

**No entres si:**
- No hay forma de medir el ritmo de córners en vivo con tus datos actuales

**En partidos ajenos:** sin datos para medirlo.

## 4. Mapa de probabilidades

Frecuencia real en partidos ajenos según minuto, goles y diferencia en el marcador.

| Minuto | Goles | Diferencia | Partidos | Llega 1 gol más | Llegan 2 más | Líder gana / Empate sigue | Modelo 1 gol más |
|---|---|---|---|---|---|---|---|
| 30' | 0 | 0 | 35 | 94% | 66% | 23% | 85% |
| 30' | 1 | 1 | 15 | 73% | 60% | 67% | 85% |
| 45' | 0 | 0 | 17 | 88% | 47% | 12% | 75% |
| 45' | 1 | 1 | 23 | 70% | 48% | 74% | 74% |
| 45' | 2 | 0 | 7 | 71% | 57% | 71% | 77% |
| 45' | 2 | 2+ | 4 | 75% | 25% | 100% | 79% |
| 60' | 0 | 0 | 13 | 85% | 38% | 15% | 60% |
| 60' | 1 | 1 | 13 | 38% | 31% | 92% | 60% |
| 60' | 2 | 0 | 8 | 62% | 38% | 75% | 61% |
| 60' | 2 | 2+ | 12 | 67% | 17% | 83% | 61% |
| 60' | 3+ | 1 | 4 | 50% | 0% | 100% | 66% |
| 60' | 3+ | 2+ | 6 | 67% | 17% | 100% | 65% |
| 70' | 0 | 0 | 8 | 75% | 25% | 25% | 48% |
| 70' | 1 | 1 | 16 | 38% | 25% | 94% | 49% |
| 70' | 2 | 0 | 5 | 40% | 20% | 80% | 47% |
| 70' | 2 | 2+ | 11 | 64% | 18% | 91% | 49% |
| 70' | 3+ | 1 | 7 | 57% | 0% | 71% | 52% |
| 70' | 3+ | 2+ | 8 | 25% | 12% | 100% | 52% |
| 80' | 1 | 1 | 16 | 19% | 6% | 94% | 33% |
| 80' | 2 | 0 | 6 | 50% | 0% | 50% | 32% |
| 80' | 2 | 2+ | 10 | 50% | 0% | 100% | 32% |
| 80' | 3+ | 1 | 8 | 50% | 0% | 62% | 35% |
| 80' | 3+ | 2+ | 11 | 27% | 9% | 100% | 35% |

## 5. Búsqueda de patrones nuevos

Se probaron situaciones en la mitad más antigua de los partidos y se revisaron en la más reciente. Ninguna superó la corrección por pruebas múltiples con 57 partidos. Hace falta la muestra grande de Sofascore para confirmar patrones nuevos.

## 6. Tus apuestas contra el modelo

La cuota que tomaste implica una probabilidad. Si el modelo base de la liga da más, había valor; si da menos, pagaste por algo que el modelo no ve, por ejemplo la fuerza del favorito.

| Partido | Apuesta | Min | Marcador | Cuota | Prob. implícita | Modelo | Cuota mínima | Resultado |
|---|---|---|---|---|---|---|---|---|
| Almirante Brown vs Acassuso | Más de 1.5 | 77' | 0:1 | 1.75 | 57% | 40% | 2.50 | Perdió |
| Antoniano vs Ciudad de Lucena | Más de 2.5 | 67' | 0:2 | 1.63 | 61% | 46% | 2.16 | Ganó |
| Atenas vs Plaza Colonia | Atenas | 46' | 0:0 | 1.84 | 54% | 55% | 1.83 | Perdió |
| Austria vs Kosovo | Más de 3 | 46' | 2:0 | 1.47 | 68% | 41% | 2.43 | Ganó |
| Bolívar vs Blooming | Más de 1.5 | 66' | 0:0 | 1.85 | 54% | 13% | 7.47 | Ganó |
| Bournemouth vs Liverpool | Más de 1.5 | 23' | 0:0 | 1.40 | 71% | 69% | 1.45 | Perdió |
| CD Génesis vs Olancho FC | Olancho FC | 59' | 0:0 | 2.22 | 45% | 44% | 2.27 | Perdió |
| CS Fola Esch vs FC Juvenil Canach | CS Fola Esch | 46' | 0:0 | 1.90 | 53% | 36% | 2.81 | Ganó |
| Camacha vs Florgrade | Camacha se clasifica | 32' | 0:0 | 1.63 | 61% | 55% | 1.82 | Perdió |
| Carlos Mannucci vs Universidad San Martín | Más de 4.5 | 45' | 3:0 | 1.63 | 61% | 43% | 2.31 | Ganó |
| Casarano vs Monopoli | Casarano gana + Más de 1.5 | 8' | 0:0 | 1.85 | 54% | 31% | 3.22 | Perdió |
| Cavalry FC vs FC Supra du Québec | Más de 3.5 | 35' | 2:0 | 1.45 | 69% | 55% | 1.82 | Ganó |
| Chequia vs Inglaterra | Inglaterra gana + Más de 1.5 | 46' | 0:0 | 1.77 | 56% | 24% | 4.09 | Ganó |
| Club Aurora vs Universitario de Vinto | Club Aurora | 73' | 3:2 | 1.61 | 62% | 81% | 1.24 | Ganó |
| Comerciantes FC vs Sport Huancayo Reserva | Sport Huancayo Reserva | 14' | 0:0 | 3.00 | 33% | 72% | 1.38 | Ganó |
| Criciúma vs Avaí | Más de 2 | 65' | 2:0 | 1.90 | 53% | 55% | 1.83 | Ganó |
| DC United vs Charlotte FC | Más de 2 | 46' | 0:1 | 1.19 | 84% | 43% | 2.33 | Ganó |
| Deportivo Pasto vs Once Caldas | Más de 1.5 | 39' | 0:0 | 2.05 | 49% | 34% | 2.98 | Perdió |
| Deportivo San Pedro vs Cobán Imperial | Cobán Imperial | 51' | 0:0 | 2.30 | 43% | 26% | 3.89 | Perdió |
| EVV Echt vs Halsteren | Más de 5.5 | 52' | 2:1 | 1.47 | 68% | 7% | 13.55 | Perdió |
| Escocia vs Suiza | Más de 2 | 46' | 0:1 | 1.42 | 70% | 30% | 3.37 | Ganó |
| Eslovenia vs Macedonia del Norte | Eslovenia | 50' | 0:0 | 1.63 | 61% | 34% | 2.95 | Ganó |
| España vs Croacia | Más de 4.5 | 50' | 2:1 | 1.72 | 58% | 37% | 2.72 | Ganó |
| Estrela Calheta vs Cinfães | Sí | 41' | 1:0 | 1.47 | 68% | 53% | 1.90 | Ganó |
| FC Fredericia vs Vejle | Más de 3.5 | 69' | 1:2 | 1.45 | 69% | 54% | 1.86 | Ganó |
| Fortaleza vs Atlético Junior | Más de 2.5 | 24' | 0:1 | 1.55 | 65% | 44% | 2.29 | Ganó |
| Frosinone vs Como | Frosinone | 69' | 2:0 | 1.34 | 75% | 97% | 1.03 | Ganó |
| General Caballero JLM vs 3 de Noviembre | 3 de Noviembre | 24' | 0:1 | 1.88 | 53% | 59% | 1.70 | Ganó |
| Gerasdorf Stammersdorf vs Mauer | Mauer | 23' | 0:0 | 1.41 | 71% | 30% | 3.34 | Ganó |
| Groene Ster vs AFC Amsterdam | Más de 5.5 | 60' | 0:4 | 2.10 | 48% | 26% | 3.82 | Ganó |
| Grorud vs Moss | Más de 2.5 | 66' | 1:1 | 1.47 | 68% | 56% | 1.80 | Perdió |
| Grêmio Prudente vs União São João | União São João | 77' | 0:0 | 2.75 | 36% | 26% | 3.82 | Perdió |
| Grêmio vs Palmeiras | Más de 1.5 | 26' | 0:0 | 1.42 | 70% | 62% | 1.61 | Perdió |
| Karpaty vs Veres | Más de 1.5 | 81' | 1:0 | 2.20 | 45% | 26% | 3.90 | Ganó |
| Levanger vs Grorud | Ambos marcan + Más de 2.5 | 32' | 0:1 | 1.40 | 71% | 50% | 2.00 | Perdió |
| Lexington SC vs Orange County SC | Más de 5.5 | 69' | 5:0 | 1.45 | 69% | 56% | 1.80 | Ganó |
| Molde vs Aalesunds | Aalesunds | 46' | 0:2 | 1.40 | 71% | 88% | 1.13 | Ganó |
| O Elvas vs UD Leiria | UD Leiria | 74' | 0:0 | 2.10 | 48% | 30% | 3.28 | Ganó |
| Odense Boldklub vs FC Midtjylland | Más de 1.5 | 69' | 0:1 | 1.40 | 71% | 44% | 2.30 | Ganó |
| Once Caldas vs Bucaramanga | Bucaramanga | 30' | 0:2 | 1.34 | 75% | 85% | 1.17 | Ganó |
| Pioneros de Cancún vs Tapachula Soconusco | Más de 3.5 | 65' | 3:0 | 1.28 | 78% | 61% | 1.65 | Ganó |
| River Plate vs Huracán | Sí | 49' | 0:1 | 1.40 | 71% | 56% | 1.79 | Ganó |
| Rochdale vs Liverpool Sub-21 | Rochdale | 52' | 1:1 | 1.64 | 61% | 53% | 1.90 | Perdió |
| San Jose Earthquakes vs LAFC | Sí | 46' | 0:1 | 1.27 | 79% | 63% | 1.60 | Ganó |
| Santa Clara vs SC Braga | Más de 0.5 | 55' | 0:0 | 1.45 | 69% | 66% | 1.53 | Perdió |
| Sparta Rotterdam vs Heerenveen | Más de 2.5 | 41' | 0:1 | 1.47 | 68% | 52% | 1.94 | Ganó |
| Tacoma Defiance vs Portland Timbers II | Tacoma gana + Más de 1.5 | 25' | 0:0 | 1.85 | 54% | 26% | 3.84 | Perdió |
| Twente vs PSV | Más de 3.5 | 81' | 1:2 | 1.63 | 61% | 34% | 2.99 | Ganó |
| Vasco da Gama vs Coritiba | Más de 2.5 | 46' | 2:0 | 1.17 | 85% | 77% | 1.31 | Ganó |
| Waterside Karori vs Fencibles United (F) | Waterside Karori | 21' | 0:0 | 1.68 | 60% | 40% | 2.47 | Perdió |
| Wehen Wiesbaden vs Duisburg | Más de 4.5 | 42' | 0:3 | 1.68 | 60% | 52% | 1.93 | Ganó |

### Reconstrucciones a revisar

La cuota tomada y el modelo difieren más de 35 puntos. O el marcador reconstruido está mal, o el mercado sabía algo que la base de la liga no refleja.

- Escocia vs Suiza: Más de 2 a 1.42 con 0:1 al 46'. Implícita 70%, modelo 30%.
- Bolívar vs Blooming: Más de 1.5 a 1.85 con 0:0 al 66'. Implícita 54%, modelo 13%.
- Comerciantes FC vs Sport Huancayo Reserva: Sport Huancayo Reserva a 3.00 con 0:0 al 14'. Implícita 33%, modelo 72%.
- Gerasdorf Stammersdorf vs Mauer: Mauer a 1.41 con 0:0 al 23'. Implícita 71%, modelo 30%.
- EVV Echt vs Halsteren: Más de 5.5 a 1.47 con 2:1 al 52'. Implícita 68%, modelo 7%.
- DC United vs Charlotte FC: Más de 2 a 1.19 con 0:1 al 46'. Implícita 84%, modelo 43%.

## 7. Límites

- La muestra de partidos ajenos es chica. Los intervalos son anchos y ninguna regla nueva queda confirmada.
- La búsqueda web da goles y rojas al minuto. Tiros, xG y presión al minuto llegan con Sofascore (`python -m fb.cli sofascore-probar`).
- No existe historial de cuotas en vivo. El ROI solo se mide con tus apuestas registradas en la app.

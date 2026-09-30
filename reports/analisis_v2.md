# Football Brain · Análisis v2

Generado el 2026-09-30 11:53 con `python -m fb.cli reporte`.

## 1. De dónde salen los datos

- Partidos terminados con todos los goles al minuto: 110.
- De ellos, 75 son partidos ajenos a tus apuestas. Solo esos validan patrones.
- Los otros son los partidos donde apostaste. Sirven para el modelo, no para darte la razón.
- Fuente: crónicas y fichas de prensa encontradas por búsqueda web, una por partido, con enlace en el CSV.
- Cada partido se verificó: la lista de goles debe sumar exactamente el marcador final.

## 2. El modelo en vivo

Estima cuántos goles faltan según el minuto, la liga y si hubo roja. Con eso calcula la probabilidad de cada mercado y la cuota mínima para que la apuesta valga la pena.

- Validación cruzada en 550 predicciones de 'llega al menos un gol más'.
- Brier score 0.196 contra 0.229 de adivinar siempre la media. Menor es mejor.

| Probabilidad del modelo | Casos | Media predicha | Ocurrió |
|---|---|---|---|
| 20% a 40% | 111 | 34% | 37% |
| 40% a 60% | 136 | 52% | 54% |
| 60% a 80% | 182 | 71% | 73% |
| 80% a 100% | 121 | 86% | 88% |

- Roja: 19 goles observados tras la roja contra 27.9 esperados.
- Tras la roja marcó el equipo con uno más 18 veces y el de 10 1 veces.
- Goles por partido en la muestra: 2.78 en 110 partidos.
- Límite: el modelo no conoce la fuerza de cada equipo. En apuestas a ganador subestima al favorito.
  La app pide la cuota prepartido del favorito para corregirlo.

### ¿Sirven los promedios por equipo (tipo scores24)?

Se probó el modelo con goles a favor y en contra de cada equipo, calculados con sus otros partidos de la muestra, sin mirar el partido que se predice. Menor Brier es mejor.

| Predicción | Solo liga | Con equipos |
|---|---|---|
| Ganador final (1X2) | 0.360 | 0.412 |
| Llega al menos un gol más | 0.148 | 0.149 |

Solo 9 partidos tienen dos o más partidos de cada equipo en la muestra, así que es una señal débil. Para goles no ayudó. Para ganador empeoró: con 2 o 3 partidos por equipo el promedio es puro ruido. Para ganador la cuota prepartido resume mucho mejor la fuerza de los equipos.

Uso recomendado en la app: los promedios de la temporada completa (10 partidos o más) sirven para los mercados de goles. Para ganador usa la cuota prepartido.

## 3. Patrones

| Código | Patrón | Backtest | Tu historial | Cuota mínima | Semáforo |
|---|---|---|---|---|---|
| P1 | Over con partido abierto | 38/49 (78%) | 7/8 | 1.32 | ambar |
| P2 | Ganador al equipo que ya gana | 58/68 (85%) | 5/5 | 1.20 | verde |
| P3 | Roja: apostar a goles | 5/6 (83%) | 7/8 | 1.43 | rojo |
| P4 | Roja: ganador al que tiene uno más | 3/4 (75%) | 3/8 | 1.60 | rojo |
| P5 | Primer gol tras el descanso con 0:0 | 15/17 (88%) | 0/1 | 1.24 | rojo |
| P6 | Ganador con ventaja de 2 desde el 60' | 30/32 (94%) | 1/1 | 1.12 | ambar |
| A1 | Ganador con el partido empatado | 25/35 (71%) | 6/14 | — | evitar |
| A2 | Over que pide 2 goles con 0:0 | 7/17 (41%) | 0/3 | 2.33 | evitar |
| A3 | Córners | sin datos | — | — | evitar |

Semáforo: rojo con menos de 30 casos en total; ámbar si el intervalo toca el break-even de tus cuotas (o si aún no hay 5 apuestas tuyas para saber qué cuota tomas); verde si el límite inferior lo supera. Los anti-patrones (A) no llevan color: se evitan.

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

**En partidos ajenos:** se cumplió 38 de 49 veces (78%), intervalo 95% de 64% a 87%. El modelo esperaba 73%. De cada 10 veces, unas 8 salen bien.
**Cuota mínima para entrar:** 1.32. Con una cuota menor pierdes dinero a la larga aunque aciertes seguido.
**Ligas donde mejor funcionó** (tasa ajustada por tamaño de muestra): Países Bajos Eredivisie 3/3, Bolivia Primera 3/3, Perú Liga 1 12/14, Inglaterra Premier League 1/1.
**En tus apuestas:** 7 de 8, cuota media 1.44, neto +2.07 unidades.

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

**En partidos ajenos:** se cumplió 58 de 68 veces (85%), intervalo 95% de 75% a 92%. El modelo esperaba 75%. De cada 10 veces, unas 9 salen bien.
**Cuota mínima para entrar:** 1.20. Con una cuota menor pierdes dinero a la larga aunque aciertes seguido.
**Ligas donde mejor funcionó** (tasa ajustada por tamaño de muestra): Bolivia Primera 3/3, Países Bajos Eerste Divisie 3/3, Perú Liga 1 15/17, Paraguay Primera 1/1.
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

**En partidos ajenos:** se cumplió 5 de 6 veces (83%), intervalo 95% de 44% a 97%. El modelo esperaba 67%. De cada 10 veces, unas 8 salen bien.
**Cuota mínima para entrar:** 1.43. Con una cuota menor pierdes dinero a la larga aunque aciertes seguido.
**Ligas donde mejor funcionó** (tasa ajustada por tamaño de muestra): Perú Liga 1 2/2, Paraguay Primera 1/1, Brasil Serie A 1/1, Colombia Primera A 1/2.
**En tus apuestas:** 7 de 8, cuota media 1.67, neto +3.32 unidades.

### P4 · Roja: ganador al que tiene uno más

El rival se quedó con 10 y el partido sigue empatado.

**Entra solo si:**
- El rival de tu equipo tiene una roja
- El partido está empatado
- Tu equipo domina y llega

**No entres si:**
- Pasó el minuto 70 y sigue 0:0
- La cuota es menor a la cuota mínima de la tabla

**En partidos ajenos:** se cumplió 3 de 4 veces (75%), intervalo 95% de 30% a 95%. El modelo esperaba 56%. De cada 10 veces, unas 8 salen bien.
**Cuota mínima para entrar:** 1.60. Con una cuota menor pierdes dinero a la larga aunque aciertes seguido.
**Ligas donde mejor funcionó** (tasa ajustada por tamaño de muestra): Colombia Primera A 1/1, Paraguay Primera 1/1, Perú Liga 1 1/1, Brasil Serie A 0/1.
**En tus apuestas:** 3 de 8, cuota media 2.20, neto -1.13 unidades.

### P5 · Primer gol tras el descanso con 0:0

El partido llega 0:0 al segundo tiempo. Se apuesta a que cae al menos un gol.

**Entra solo si:**
- El marcador es 0:0
- Estás entre el minuto 45 y el 60
- Apuestas Más de 0.5 goles (te falta 1 solo gol)

**No entres si:**
- Tu línea pide 2 goles o más (eso es A2)
- Ya pasó el minuto 60
- La cuota es menor a la cuota mínima de la tabla

**En partidos ajenos:** se cumplió 15 de 17 veces (88%), intervalo 95% de 66% a 97%. El modelo esperaba 75%. De cada 10 veces, unas 9 salen bien.
**Cuota mínima para entrar:** 1.24. Con una cuota menor pierdes dinero a la larga aunque aciertes seguido.
**Ligas donde mejor funcionó** (tasa ajustada por tamaño de muestra): Brasil Serie A 3/3, Países Bajos Eredivisie 2/2, Perú Liga 1 2/2, Argentina Liga Profesional 1/1.
**En tus apuestas:** 0 de 1, cuota media 1.45, neto -1.00 unidades.

### P6 · Ganador con ventaja de 2 desde el 60'

Un equipo gana por 2 goles o más con 30 minutos o menos por jugar.

**Entra solo si:**
- Apuestas Ganador (1x2) al que va arriba
- La ventaja es de 2 goles o más
- Ya pasó el minuto 60

**No entres si:**
- La ventaja es de 1 gol
- La cuota es menor a la cuota mínima: suele pagar muy poco

**En partidos ajenos:** se cumplió 30 de 32 veces (94%), intervalo 95% de 80% a 98%. El modelo esperaba 97%. De cada 10 veces, unas 9 salen bien.
**Cuota mínima para entrar:** 1.12. Con una cuota menor pierdes dinero a la larga aunque aciertes seguido.
**Ligas donde mejor funcionó** (tasa ajustada por tamaño de muestra): Perú Liga 1 7/7, Colombia Primera A 6/6, Brasil Serie A 4/4, Países Bajos Eredivisie 2/2.
**En tus apuestas:** 1 de 1, cuota media 1.34, neto +0.34 unidades.

### A1 · Ganador con el partido empatado

Apostar a un ganador cuando el marcador está igualado.

**No entres si:**
- El marcador está empatado: usa Doble oportunidad o espera el gol

**En partidos ajenos:** se cumplió 25 de 35 veces (71%), intervalo 95% de 55% a 84%. El modelo esperaba 58%. De cada 10 veces, unas 7 salen bien.
**Ligas donde mejor funcionó** (tasa ajustada por tamaño de muestra): Perú Liga 1 6/7, Países Bajos Eerste Divisie 1/1, Brasil Serie A 3/4, Países Bajos Eredivisie 2/3.
**En tus apuestas:** 6 de 14, cuota media 2.00, neto -2.19 unidades.

### A2 · Over que pide 2 goles con 0:0

Con 0:0 suele llegar un gol, pero dos ya es otra cosa.

**No entres si:**
- El partido va 0:0 y tu línea necesita 2 goles o más (Más de 1.5 o mayor)
- Si quieres entrar con 0:0, la línea debe pedir 1 solo gol (Más de 0.5) y la cuota superar la mínima

**En partidos ajenos:** se cumplió 7 de 17 veces (41%), intervalo 95% de 22% a 64%. El modelo esperaba 41%. De cada 10 veces, unas 4 salen bien.
**Cuota mínima para entrar:** 2.33. Con una cuota menor pierdes dinero a la larga aunque aciertes seguido.
**Ligas donde mejor funcionó** (tasa ajustada por tamaño de muestra): Brasil Serie A 3/3, Colombia Primera A 3/5, Argentina Liga Profesional 1/1, Países Bajos Eredivisie 0/2.
**En tus apuestas:** 0 de 3, cuota media 1.62, neto -3.00 unidades.

### A3 · Córners

Más de córners sin datos de córners al minuto.

**No entres si:**
- No hay forma de medir el ritmo de córners en vivo con tus datos actuales

**En partidos ajenos:** sin datos para medirlo.

## Tus ligas

Tu historial es por pata (incluye las de combinadas), con neto a stake 1 como si cada pata fuera simple. Las tasas base salen de partidos terminados verificados gol a gol (tasas con 4 partidos o más). Aparecen las ligas con muestra o con 3 patas tuyas o más.

Referencia de toda la muestra (110 partidos): 2.78 goles por partido, Más de 2.5 en 56%, Ambos marcan en 44%, hubo gol desde el 75' en 48% de los partidos y el 55% de los goles fue en el 2T.

| Liga | Tus patas | Neto | Partidos | Goles/partido | Más de 2.5 | Ambos marcan | Gol desde 75' | Factor modelo |
|---|---|---|---|---|---|---|---|---|
| Brasil Serie B | 1/1 | +0.90 | 18 | 2.33 | 56% (34%–75%) | 28% | 28% | 0.90 |
| Perú Liga 1 | — | — | 18 | 3.11 | 72% (49%–88%) | 56% | 56% | 1.07 |
| Colombia Primera A | 3/4 | +0.57 | 16 | 2.19 | 44% (23%–67%) | 25% | 44% | 0.88 |
| Brasil Serie A | 1/2 | -0.83 | 9 | 2.67 | 56% (27%–81%) | 56% | 44% | 0.98 |
| Países Bajos Eredivisie | 2/2 | +1.10 | 9 | 2.89 | 56% (27%–81%) | 33% | 44% | 1.02 |
| Argentina Liga Profesional | 1/1 | +0.40 | 5 | 3.60 | 100% (57%–100%) | 100% | 80% | 1.09 |
| Países Bajos Eerste Divisie | 1/1 | +0.63 | 4 | 3.25 | 50% (15%–85%) | 50% | 50% | 1.04 |
| Bolivia Primera | — | — | 4 | 5.50 | 100% (51%–100%) | 50% | 100% | 1.24 |
| UEFA Nations League | 7/8 | +3.27 | 3 | — | — | — | — | 0.97 |
| MLS | 2/3 | -0.54 | 1 | — | — | — | — | 1.01 |

Cómo leerla: el factor del modelo es la liga contra la media, ya contraído hacia 1 porque las muestras son chicas. Una liga con 16 partidos y 44% de Más de 2.5 tiene un intervalo de unos 25 puntos. Sirve para ordenar ligas, no para creer que una liga es 'de goles' con 5 partidos.

## 4. Mapa de probabilidades

Frecuencia real en partidos ajenos según minuto, goles y diferencia en el marcador.

| Minuto | Goles | Diferencia | Partidos | Llega 1 gol más | Llegan 2 más | Líder gana / Empate sigue | Modelo 1 gol más |
|---|---|---|---|---|---|---|---|
| 30' | 0 | 0 | 42 | 95% | 69% | 21% | 86% |
| 30' | 1 | 1 | 21 | 81% | 57% | 76% | 87% |
| 30' | 2 | 0 | 6 | 100% | 50% | 0% | 89% |
| 45' | 0 | 0 | 17 | 88% | 41% | 12% | 76% |
| 45' | 1 | 1 | 30 | 77% | 57% | 73% | 75% |
| 45' | 2 | 0 | 10 | 80% | 60% | 50% | 76% |
| 45' | 2 | 2+ | 9 | 67% | 33% | 100% | 78% |
| 45' | 3+ | 1 | 4 | 50% | 25% | 100% | 80% |
| 45' | 3+ | 2+ | 5 | 100% | 40% | 100% | 82% |
| 60' | 0 | 0 | 14 | 86% | 36% | 14% | 61% |
| 60' | 1 | 1 | 17 | 53% | 41% | 88% | 62% |
| 60' | 2 | 0 | 9 | 67% | 33% | 67% | 62% |
| 60' | 2 | 2+ | 16 | 62% | 25% | 88% | 62% |
| 60' | 3+ | 1 | 10 | 60% | 10% | 90% | 66% |
| 60' | 3+ | 2+ | 8 | 75% | 12% | 100% | 67% |
| 70' | 0 | 0 | 8 | 75% | 25% | 25% | 49% |
| 70' | 1 | 1 | 18 | 39% | 22% | 94% | 50% |
| 70' | 2 | 0 | 7 | 57% | 14% | 57% | 50% |
| 70' | 2 | 2+ | 13 | 54% | 15% | 92% | 50% |
| 70' | 3+ | 1 | 13 | 62% | 8% | 77% | 53% |
| 70' | 3+ | 2+ | 14 | 43% | 21% | 100% | 53% |
| 80' | 1 | 1 | 18 | 22% | 6% | 94% | 34% |
| 80' | 2 | 0 | 8 | 62% | 0% | 38% | 34% |
| 80' | 2 | 2+ | 12 | 42% | 0% | 100% | 32% |
| 80' | 3+ | 1 | 13 | 54% | 8% | 69% | 36% |
| 80' | 3+ | 2+ | 18 | 39% | 11% | 100% | 36% |

## 5. Búsqueda de patrones nuevos

- Minuto 30, 0+ goles, diferencia None: 34/38 en validación.
- Minuto 80, 0+ goles, diferencia 2: 13/13 en validación.
- Minuto 80, 1+ goles, diferencia 2: 13/13 en validación.
- Minuto 80, 2+ goles, diferencia 2: 13/13 en validación.
- Minuto 30, 0+ goles, diferencia 0: 22/24 en validación.
- Minuto 70, 0+ goles, diferencia 2: 11/11 en validación.
- Minuto 70, 1+ goles, diferencia 2: 11/11 en validación.
- Minuto 70, 2+ goles, diferencia 2: 11/11 en validación.

## 6. Tus apuestas contra el modelo

La cuota que tomaste implica una probabilidad. Si el modelo base de la liga da más, había valor; si da menos, pagaste por algo que el modelo no ve, por ejemplo la fuerza del favorito.

| Partido | Apuesta | Min | Marcador | Cuota | Prob. implícita | Modelo | Cuota mínima | Resultado |
|---|---|---|---|---|---|---|---|---|
| Almirante Brown vs Acassuso | Más de 1.5 | 77' | 0:1 | 1.75 | 57% | 41% | 2.43 | Perdió |
| Antoniano vs Ciudad de Lucena | Más de 2.5 | 67' | 0:2 | 1.63 | 61% | 45% | 2.22 | Ganó |
| Atenas vs Plaza Colonia | Atenas | 46' | 0:0 | 1.84 | 54% | 52% | 1.94 | Perdió |
| Austria vs Kosovo | Más de 3 | 46' | 2:0 | 1.47 | 68% | 42% | 2.39 | Ganó |
| Bolívar vs Blooming | Más de 1.5 | 66' | 1:0 | 1.85 | 54% | 46% | 2.17 | Ganó |
| Bournemouth vs Liverpool | Más de 1.5 | 23' | 0:0 | 1.40 | 71% | 71% | 1.42 | Perdió |
| CD Génesis vs Olancho FC | Olancho FC | 59' | 0:0 | 2.22 | 45% | 42% | 2.39 | Perdió |
| CS Fola Esch vs FC Juvenil Canach | CS Fola Esch | 46' | 0:0 | 1.90 | 53% | 36% | 2.79 | Ganó |
| Camacha vs Florgrade | Camacha se clasifica | 32' | 0:0 | 1.63 | 61% | 55% | 1.81 | Perdió |
| Carlos Mannucci vs Universidad San Martín | Más de 4.5 | 45' | 3:0 | 1.63 | 61% | 45% | 2.24 | Ganó |
| Casarano vs Monopoli | Casarano gana + Más de 1.5 | 8' | 0:0 | 1.85 | 54% | 32% | 3.09 | Perdió |
| Cavalry FC vs FC Supra du Québec | Más de 3.5 | 35' | 2:0 | 1.45 | 69% | 57% | 1.74 | Ganó |
| Chequia vs Inglaterra | Inglaterra gana + Más de 1.5 | 46' | 0:0 | 1.77 | 56% | 22% | 4.60 | Ganó |
| Club Aurora vs Universitario de Vinto | Club Aurora | 73' | 3:2 | 1.61 | 62% | 80% | 1.24 | Ganó |
| Comerciantes FC vs Sport Huancayo Reserva | Sport Huancayo Reserva | 14' | 0:0 | 3.00 | 33% | 70% | 1.44 | Ganó |
| Criciúma vs Avaí | Más de 2 | 65' | 2:0 | 1.90 | 53% | 55% | 1.81 | Ganó |
| DC United vs Charlotte FC | Más de 2 | 46' | 1:1 | 1.19 | 84% | 77% | 1.29 | Ganó |
| Deportivo Pasto vs Once Caldas | Más de 1.5 | 39' | 0:0 | 2.05 | 49% | 31% | 3.20 | Perdió |
| Deportivo San Pedro vs Cobán Imperial | Cobán Imperial | 51' | 0:0 | 2.30 | 43% | 50% | 2.00 | Perdió |
| Escocia vs Suiza | Más de 2 | 46' | 0:1 | 1.42 | 70% | 28% | 3.63 | Ganó |
| Eslovenia vs Macedonia del Norte | Eslovenia | 50' | 0:0 | 1.63 | 61% | 34% | 2.93 | Ganó |
| España vs Croacia | Más de 4.5 | 50' | 2:1 | 1.72 | 58% | 38% | 2.66 | Ganó |
| Estrela Calheta vs Cinfães | Sí | 41' | 1:0 | 1.47 | 68% | 54% | 1.86 | Ganó |
| FC Fredericia vs Vejle | Más de 3.5 | 69' | 1:2 | 1.45 | 69% | 55% | 1.82 | Ganó |
| Fortaleza vs Atlético Junior | Más de 2.5 | 24' | 0:1 | 1.55 | 65% | 42% | 2.41 | Ganó |
| Frosinone vs Como | Frosinone | 69' | 2:0 | 1.34 | 75% | 97% | 1.03 | Ganó |
| General Caballero JLM vs 3 de Noviembre | 3 de Noviembre | 24' | 0:1 | 1.88 | 53% | 58% | 1.72 | Ganó |
| Gerasdorf Stammersdorf vs Mauer | Mauer | 23' | 0:0 | 1.41 | 71% | 30% | 3.31 | Ganó |
| Groene Ster vs AFC Amsterdam | Más de 5.5 | 60' | 0:4 | 2.10 | 48% | 28% | 3.62 | Ganó |
| Grorud vs Moss | Más de 2.5 | 66' | 1:1 | 1.47 | 68% | 57% | 1.76 | Perdió |
| Grêmio Prudente vs União São João | União São João | 77' | 0:0 | 2.75 | 36% | 25% | 4.03 | Perdió |
| Grêmio vs Palmeiras | Más de 1.5 | 26' | 0:0 | 1.42 | 70% | 64% | 1.57 | Perdió |
| Karpaty vs Veres | Más de 1.5 | 81' | 1:0 | 2.20 | 45% | 25% | 4.02 | Ganó |
| Levanger vs Grorud | Ambos marcan + Más de 2.5 | 32' | 0:1 | 1.40 | 71% | 53% | 1.90 | Perdió |
| Lexington SC vs Orange County SC | Más de 5.5 | 69' | 5:0 | 1.45 | 69% | 57% | 1.76 | Ganó |
| Molde vs Aalesunds | Aalesunds | 46' | 0:2 | 1.40 | 71% | 88% | 1.14 | Ganó |
| O Elvas vs UD Leiria | UD Leiria | 74' | 0:0 | 2.10 | 48% | 29% | 3.46 | Ganó |
| Odense Boldklub vs FC Midtjylland | Más de 1.5 | 69' | 0:1 | 1.40 | 71% | 43% | 2.35 | Ganó |
| Once Caldas vs Bucaramanga | Bucaramanga | 30' | 0:2 | 1.34 | 75% | 85% | 1.18 | Ganó |
| Pioneros de Cancún vs Tapachula Soconusco | Más de 3.5 | 65' | 3:0 | 1.28 | 78% | 62% | 1.61 | Ganó |
| River Plate vs Huracán | Sí | 49' | 0:1 | 1.40 | 71% | 56% | 1.78 | Ganó |
| Rochdale vs Liverpool Sub-21 | Rochdale | 52' | 1:1 | 1.64 | 61% | 50% | 2.01 | Perdió |
| San Jose Earthquakes vs LAFC | Sí | 46' | 0:1 | 1.27 | 79% | 60% | 1.67 | Ganó |
| Santa Clara vs SC Braga | Más de 0.5 | 55' | 0:0 | 1.45 | 69% | 67% | 1.50 | Perdió |
| Sparta Rotterdam vs Heerenveen | Más de 2.5 | 41' | 0:1 | 1.47 | 68% | 52% | 1.92 | Ganó |
| Tacoma Defiance vs Portland Timbers II | Tacoma gana + Más de 1.5 | 25' | 0:0 | 1.85 | 54% | 27% | 3.66 | Perdió |
| Twente vs PSV | Más de 3.5 | 81' | 1:2 | 1.63 | 61% | 34% | 2.96 | Ganó |
| Vasco da Gama vs Coritiba | Más de 2.5 | 46' | 2:0 | 1.17 | 85% | 77% | 1.30 | Ganó |
| Waterside Karori vs Fencibles United (F) | Waterside Karori | 21' | 0:0 | 1.68 | 60% | 41% | 2.43 | Perdió |
| Wehen Wiesbaden vs Duisburg | Más de 4.5 | 42' | 0:3 | 1.68 | 60% | 53% | 1.88 | Ganó |

### Reconstrucciones a revisar

La cuota tomada y el modelo difieren más de 35 puntos. O el marcador reconstruido está mal, o el mercado sabía algo que la base de la liga no refleja.

- Escocia vs Suiza: Más de 2 a 1.42 con 0:1 al 46'. Implícita 70%, modelo 28%.
- Comerciantes FC vs Sport Huancayo Reserva: Sport Huancayo Reserva a 3.00 con 0:0 al 14'. Implícita 33%, modelo 70%.
- Gerasdorf Stammersdorf vs Mauer: Mauer a 1.41 con 0:0 al 23'. Implícita 71%, modelo 30%.

## 7. Límites

- La muestra de partidos ajenos es chica. Los intervalos son anchos y ninguna regla nueva queda confirmada.
- La búsqueda web da goles y rojas al minuto. Tiros, xG y presión al minuto llegan con Sofascore (`python -m fb.cli sofascore-probar`).
- No existe historial de cuotas en vivo. El ROI solo se mide con tus apuestas registradas en la app.

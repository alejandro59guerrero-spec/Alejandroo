# Football Brain · Análisis v2

Generado el 2026-09-30 14:42 con `python -m fb.cli reporte`.

## 1. De dónde salen los datos

- Partidos terminados con todos los goles al minuto: 117.
- De ellos, 82 son partidos ajenos a tus apuestas. Solo esos validan patrones.
- Los otros son los partidos donde apostaste. Sirven para el modelo, no para darte la razón.
- Fuente: crónicas y fichas de prensa encontradas por búsqueda web, una por partido, con enlace en el CSV.
- Cada partido se verificó: la lista de goles debe sumar exactamente el marcador final.

## 2. El modelo en vivo

Estima cuántos goles faltan según el minuto, la liga y si hubo roja. Con eso calcula la probabilidad de cada mercado y la cuota mínima para que la apuesta valga la pena.

- Validación cruzada en 585 predicciones de 'llega al menos un gol más'.
- Brier score 0.196 contra 0.232 de adivinar siempre la media. Menor es mejor.

| Probabilidad del modelo | Casos | Media predicha | Ocurrió |
|---|---|---|---|
| 20% a 40% | 122 | 34% | 38% |
| 40% a 60% | 146 | 52% | 51% |
| 60% a 80% | 194 | 71% | 74% |
| 80% a 100% | 123 | 87% | 88% |

- Roja: 19 goles observados tras la roja contra 28.7 esperados.
- Tras la roja marcó el equipo con uno más 18 veces y el de 10 1 veces.
- Goles por partido en la muestra: 2.79 en 117 partidos.
- Límite: el modelo no conoce la fuerza de cada equipo. En apuestas a ganador subestima al favorito.
  La app pide la cuota prepartido del favorito para corregirlo.

### ¿Importa el marcador para que llegue otro gol?

El modelo supone que no: solo mira minuto, liga y rojas. Prueba en todos los partidos:

| Momento | Marcador | Casos | Llegó otro gol | Intervalo 95% | Modelo | ¿Cuadra? |
|---|---|---|---|---|---|---|
| desde el 60' | empate | 92 | 48% | 38%–58% | 49% | sí |
| desde el 60' | ventaja de 1 | 136 | 50% | 42%–58% | 48% | sí |
| desde el 60' | ventaja de 2+ | 123 | 53% | 44%–61% | 48% | sí |
| hasta el 45' | empate | 109 | 84% | 75%–89% | 81% | sí |
| hasta el 45' | ventaja de 1 | 89 | 81% | 72%–88% | 81% | sí |
| hasta el 45' | ventaja de 2+ | 36 | 89% | 75%–96% | 81% | sí |

Si todas las filas cuadran, el supuesto se sostiene con esta muestra y la probabilidad de gol de la app vale igual para empate que para ventaja. Si alguna dice NO, ese estado necesita su propio ajuste.

### ¿Sirven los promedios por equipo (tipo scores24)?

Se probó el modelo con goles a favor y en contra de cada equipo, calculados con sus otros partidos de la muestra, sin mirar el partido que se predice. Menor Brier es mejor.

| Predicción | Solo liga | Con equipos |
|---|---|---|
| Ganador final (1X2) | 0.401 | 0.440 |
| Llega al menos un gol más | 0.159 | 0.156 |

Solo 19 partidos tienen dos o más partidos de cada equipo en la muestra, así que es una señal débil. Para goles ayudó un poco. Para ganador empeoró: con 2 o 3 partidos por equipo el promedio es puro ruido. Para ganador la cuota prepartido resume mucho mejor la fuerza de los equipos.

Uso recomendado en la app: los promedios de la temporada completa (10 partidos o más) sirven para los mercados de goles. Para ganador usa la cuota prepartido.

## 3. Patrones

| Código | Patrón | Backtest | Fuera de muestra | Tu historial | Cuota mínima | Semáforo |
|---|---|---|---|---|---|---|
| P1 | Over con partido abierto | 41/55 (75%) | 21/27 (mín 59%) | 7/8 | 1.37 | ambar |
| P2 | Ganador al equipo que ya gana | 61/75 (81%) | 28/34 (mín 66%) | 5/5 | 1.25 | verde |
| P3 | Roja: apostar a goles | 5/7 (71%) | 2/3 (mín 21%) | 7/8 | 1.57 | rojo |
| P4 | Roja: ganador al que tiene uno más | 3/4 (75%) | 2/2 (mín 34%) | 3/8 | 1.60 | rojo |
| P5 | Primer gol tras el descanso con 0:0 | 15/17 (88%) | 7/9 (mín 45%) | 0/1 | 1.24 | rojo |
| P6 | Ganador con ventaja de 2 desde el 60' | 32/34 (94%) | 14/15 (mín 70%) | 1/1 | 1.12 | ambar |
| A1 | Ganador con el partido empatado | 26/39 (67%) | 12/22 (mín 35%) | 6/14 | — | evitar |
| A2 | Over que pide 2 goles con 0:0 | 7/17 (41%) | 4/9 (mín 19%) | 0/3 | 2.33 | evitar |
| A3 | Córners | sin datos | — | — | — | evitar |

**Semáforo (regla fija, decidida de antemano).** rojo: menos de 30 casos en total o menos de 10 fuera de muestra, no se puede afirmar nada. verde: el límite inferior FUERA DE MUESTRA (mitad más reciente de los partidos, que no influyó en proponer el patrón) supera el break-even de tus cuotas. ámbar: prometedor pero sin prueba fuera de muestra suficiente. Los anti-patrones (A) no llevan color.

La columna *Fuera de muestra* es la prueba honesta: un patrón puede acertar mucho en toda la muestra y aun así no llegar a verde porque, al medirlo solo en los partidos recientes, el límite inferior no supera lo que necesitas para ganarle a tu cuota. P6 es el caso claro: acierta casi siempre, pero su cuota justa es tan baja que casi nunca hay valor.

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

**En partidos ajenos:** se cumplió 41 de 55 veces (75%), intervalo 95% de 62% a 84%. El modelo esperaba 72%. De cada 10 veces, unas 7 salen bien.
**Cuota mínima para entrar:** 1.37. Con una cuota menor pierdes dinero a la larga aunque aciertes seguido.
**Ligas donde mejor funcionó** (tasa ajustada por tamaño de muestra): Perú Liga 1 12/14, Países Bajos Eredivisie 3/3, Bolivia Primera 3/3, Inglaterra Premier League 1/1.
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

**En partidos ajenos:** se cumplió 61 de 75 veces (81%), intervalo 95% de 71% a 89%. El modelo esperaba 74%. De cada 10 veces, unas 8 salen bien.
**Cuota mínima para entrar:** 1.25. Con una cuota menor pierdes dinero a la larga aunque aciertes seguido.
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

**En partidos ajenos:** se cumplió 5 de 7 veces (71%), intervalo 95% de 36% a 92%. El modelo esperaba 62%. De cada 10 veces, unas 7 salen bien.
**Cuota mínima para entrar:** 1.57. Con una cuota menor pierdes dinero a la larga aunque aciertes seguido.
**Ligas donde mejor funcionó** (tasa ajustada por tamaño de muestra): Perú Liga 1 2/2, Paraguay Primera 1/1, Brasil Serie A 1/1, Colombia Primera A 1/3.
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

**En partidos ajenos:** se cumplió 3 de 4 veces (75%), intervalo 95% de 30% a 95%. El modelo esperaba 55%. De cada 10 veces, unas 8 salen bien.
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

**En partidos ajenos:** se cumplió 32 de 34 veces (94%), intervalo 95% de 81% a 98%. El modelo esperaba 97%. De cada 10 veces, unas 9 salen bien.
**Cuota mínima para entrar:** 1.12. Con una cuota menor pierdes dinero a la larga aunque aciertes seguido.
**Ligas donde mejor funcionó** (tasa ajustada por tamaño de muestra): Colombia Primera A 7/7, Perú Liga 1 7/7, Brasil Serie A 4/4, Países Bajos Eredivisie 2/2.
**En tus apuestas:** 1 de 1, cuota media 1.34, neto +0.34 unidades.

### A1 · Ganador con el partido empatado

Apostar a un ganador cuando el marcador está igualado.

**No entres si:**
- El marcador está empatado: usa Doble oportunidad o espera el gol

**En partidos ajenos:** se cumplió 26 de 39 veces (67%), intervalo 95% de 51% a 79%. El modelo esperaba 58%. De cada 10 veces, unas 7 salen bien.
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

Referencia de toda la muestra (117 partidos): 2.79 goles por partido, Más de 2.5 en 56%, Ambos marcan en 45%, hubo gol desde el 75' en 47% de los partidos y el 53% de los goles fue en el 2T.

| Liga | Tus patas | Neto | Partidos | Goles/partido | Más de 2.5 | Ambos marcan | Gol desde 75' | Factor modelo |
|---|---|---|---|---|---|---|---|---|
| Brasil Serie B | 1/1 | +0.90 | 22 | 2.46 | 50% (31%–69%) | 36% | 32% | 0.92 |
| Colombia Primera A | 3/4 | +0.57 | 19 | 2.32 | 47% (27%–68%) | 32% | 37% | 0.90 |
| Perú Liga 1 | — | — | 18 | 3.11 | 72% (49%–88%) | 56% | 56% | 1.07 |
| Brasil Serie A | 1/2 | -0.83 | 9 | 2.67 | 56% (27%–81%) | 56% | 44% | 0.98 |
| Países Bajos Eredivisie | 2/2 | +1.10 | 9 | 2.89 | 56% (27%–81%) | 33% | 44% | 1.01 |
| Argentina Liga Profesional | 1/1 | +0.40 | 5 | 3.60 | 100% (57%–100%) | 100% | 80% | 1.08 |
| Países Bajos Eerste Divisie | 1/1 | +0.63 | 4 | 3.25 | 50% (15%–85%) | 50% | 50% | 1.04 |
| Bolivia Primera | — | — | 4 | 5.50 | 100% (51%–100%) | 50% | 100% | 1.24 |
| UEFA Nations League | 7/8 | +3.27 | 3 | — | — | — | — | 0.97 |
| MLS | 2/3 | -0.54 | 1 | — | — | — | — | 1.01 |

Cómo leerla: el factor del modelo es la liga contra la media, ya contraído hacia 1 porque las muestras son chicas. Una liga con 16 partidos y 44% de Más de 2.5 tiene un intervalo de unos 25 puntos. Sirve para ordenar ligas, no para creer que una liga es 'de goles' con 5 partidos.

## 4. Mapa de probabilidades

Frecuencia real en partidos ajenos según minuto, goles y diferencia en el marcador.

| Minuto | Goles | Diferencia | Partidos | Llega 1 gol más | Llegan 2 más | Líder gana / Empate sigue | Modelo 1 gol más |
|---|---|---|---|---|---|---|---|
| 30' | 0 | 0 | 42 | 95% | 69% | 21% | 87% |
| 30' | 1 | 1 | 28 | 86% | 54% | 68% | 86% |
| 30' | 2 | 0 | 6 | 100% | 50% | 0% | 89% |
| 45' | 0 | 0 | 17 | 88% | 41% | 12% | 75% |
| 45' | 1 | 1 | 32 | 78% | 53% | 72% | 75% |
| 45' | 2 | 0 | 13 | 69% | 46% | 54% | 76% |
| 45' | 2 | 2+ | 9 | 67% | 33% | 100% | 78% |
| 45' | 3+ | 1 | 5 | 60% | 20% | 80% | 78% |
| 45' | 3+ | 2+ | 6 | 100% | 50% | 100% | 80% |
| 60' | 0 | 0 | 14 | 86% | 36% | 14% | 60% |
| 60' | 1 | 1 | 18 | 56% | 39% | 83% | 62% |
| 60' | 2 | 0 | 11 | 55% | 27% | 73% | 61% |
| 60' | 2 | 2+ | 17 | 59% | 24% | 88% | 61% |
| 60' | 3+ | 1 | 11 | 55% | 9% | 91% | 64% |
| 60' | 3+ | 2+ | 9 | 78% | 22% | 100% | 66% |
| 70' | 0 | 0 | 8 | 75% | 25% | 25% | 48% |
| 70' | 1 | 1 | 19 | 42% | 21% | 90% | 50% |
| 70' | 2 | 0 | 9 | 44% | 11% | 67% | 49% |
| 70' | 2 | 2+ | 14 | 50% | 14% | 93% | 49% |
| 70' | 3+ | 1 | 14 | 57% | 7% | 79% | 51% |
| 70' | 3+ | 2+ | 15 | 47% | 27% | 100% | 53% |
| 80' | 1 | 1 | 19 | 26% | 5% | 90% | 34% |
| 80' | 2 | 0 | 10 | 50% | 0% | 50% | 34% |
| 80' | 2 | 2+ | 13 | 38% | 0% | 100% | 32% |
| 80' | 3+ | 0 | 4 | 0% | 0% | 100% | 33% |
| 80' | 3+ | 1 | 14 | 50% | 7% | 71% | 35% |
| 80' | 3+ | 2+ | 19 | 42% | 16% | 100% | 36% |

## 5. Búsqueda de patrones nuevos

- Minuto 30, 0+ goles, diferencia None: 37/41 en validación.
- Minuto 80, 0+ goles, diferencia 2: 14/14 en validación.
- Minuto 80, 1+ goles, diferencia 2: 14/14 en validación.
- Minuto 80, 2+ goles, diferencia 2: 14/14 en validación.
- Minuto 30, 0+ goles, diferencia 0: 22/24 en validación.
- Minuto 70, 0+ goles, diferencia 2: 12/12 en validación.
- Minuto 70, 1+ goles, diferencia 2: 12/12 en validación.
- Minuto 70, 2+ goles, diferencia 2: 12/12 en validación.

## 6. Tus apuestas contra el modelo

La cuota que tomaste implica una probabilidad. Si el modelo base de la liga da más, había valor; si da menos, pagaste por algo que el modelo no ve, por ejemplo la fuerza del favorito.

| Partido | Apuesta | Min | Marcador | Cuota | Prob. implícita | Modelo | Cuota mínima | Resultado |
|---|---|---|---|---|---|---|---|---|
| Almirante Brown vs Acassuso | Más de 1.5 | 77' | 0:1 | 1.75 | 57% | 41% | 2.46 | Perdió |
| Antoniano vs Ciudad de Lucena | Más de 2.5 | 67' | 0:2 | 1.63 | 61% | 44% | 2.29 | Ganó |
| Atenas vs Plaza Colonia | Atenas | 46' | 0:0 | 1.84 | 54% | 50% | 1.99 | Perdió |
| Austria vs Kosovo | Más de 3 | 46' | 2:0 | 1.47 | 68% | 41% | 2.44 | Ganó |
| Bolívar vs Blooming | Más de 1.5 | 66' | 1:0 | 1.85 | 54% | 45% | 2.24 | Ganó |
| Bournemouth vs Liverpool | Más de 1.5 | 23' | 0:0 | 1.40 | 71% | 71% | 1.41 | Perdió |
| CD Génesis vs Olancho FC | Olancho FC | 59' | 0:0 | 2.22 | 45% | 40% | 2.47 | Perdió |
| CS Fola Esch vs FC Juvenil Canach | CS Fola Esch | 46' | 0:0 | 1.90 | 53% | 36% | 2.81 | Ganó |
| Camacha vs Florgrade | Camacha se clasifica | 32' | 0:0 | 1.63 | 61% | 55% | 1.81 | Perdió |
| Carlos Mannucci vs Universidad San Martín | Más de 4.5 | 45' | 3:0 | 1.63 | 61% | 44% | 2.29 | Ganó |
| Casarano vs Monopoli | Casarano gana + Más de 1.5 | 8' | 0:0 | 1.85 | 54% | 33% | 3.07 | Perdió |
| Cavalry FC vs FC Supra du Québec | Más de 3.5 | 35' | 2:0 | 1.45 | 69% | 57% | 1.75 | Ganó |
| Chequia vs Inglaterra | Inglaterra gana + Más de 1.5 | 46' | 0:0 | 1.77 | 56% | 20% | 4.90 | Ganó |
| Club Aurora vs Universitario de Vinto | Club Aurora | 73' | 3:2 | 1.61 | 62% | 81% | 1.24 | Ganó |
| Comerciantes FC vs Sport Huancayo Reserva | Sport Huancayo Reserva | 14' | 0:0 | 3.00 | 33% | 69% | 1.45 | Ganó |
| Criciúma vs Avaí | Más de 2 | 65' | 2:0 | 1.90 | 53% | 55% | 1.82 | Ganó |
| DC United vs Charlotte FC | Más de 2 | 46' | 1:1 | 1.19 | 84% | 77% | 1.30 | Ganó |
| Deportivo Pasto vs Once Caldas | Más de 1.5 | 39' | 0:0 | 2.05 | 49% | 31% | 3.26 | Perdió |
| Deportivo San Pedro vs Cobán Imperial | Cobán Imperial | 51' | 0:0 | 2.30 | 43% | 48% | 2.06 | Perdió |
| Escocia vs Suiza | Más de 2 | 46' | 0:1 | 1.42 | 70% | 26% | 3.85 | Ganó |
| Eslovenia vs Macedonia del Norte | Eslovenia | 50' | 0:0 | 1.63 | 61% | 34% | 2.95 | Ganó |
| España vs Croacia | Más de 4.5 | 50' | 2:1 | 1.72 | 58% | 37% | 2.73 | Ganó |
| Estrela Calheta vs Cinfães | Sí | 41' | 1:0 | 1.47 | 68% | 54% | 1.87 | Ganó |
| FC Fredericia vs Vejle | Más de 3.5 | 69' | 1:2 | 1.45 | 69% | 54% | 1.85 | Ganó |
| Fortaleza vs Atlético Junior | Más de 2.5 | 24' | 0:1 | 1.55 | 65% | 42% | 2.41 | Ganó |
| Frosinone vs Como | Frosinone | 69' | 2:0 | 1.34 | 75% | 97% | 1.03 | Ganó |
| General Caballero JLM vs 3 de Noviembre | 3 de Noviembre | 24' | 0:1 | 1.88 | 53% | 58% | 1.72 | Ganó |
| Gerasdorf Stammersdorf vs Mauer | Mauer | 23' | 0:0 | 1.41 | 71% | 30% | 3.31 | Ganó |
| Groene Ster vs AFC Amsterdam | Más de 5.5 | 60' | 0:4 | 2.10 | 48% | 27% | 3.74 | Ganó |
| Grorud vs Moss | Más de 2.5 | 66' | 1:1 | 1.47 | 68% | 56% | 1.79 | Perdió |
| Grêmio Prudente vs União São João | União São João | 77' | 0:0 | 2.75 | 36% | 24% | 4.17 | Perdió |
| Grêmio vs Palmeiras | Más de 1.5 | 26' | 0:0 | 1.42 | 70% | 64% | 1.57 | Perdió |
| Karpaty vs Veres | Más de 1.5 | 81' | 1:0 | 2.20 | 45% | 24% | 4.16 | Ganó |
| Levanger vs Grorud | Ambos marcan + Más de 2.5 | 32' | 0:1 | 1.40 | 71% | 53% | 1.90 | Perdió |
| Lexington SC vs Orange County SC | Más de 5.5 | 69' | 5:0 | 1.45 | 69% | 56% | 1.79 | Ganó |
| Molde vs Aalesunds | Aalesunds | 46' | 0:2 | 1.40 | 71% | 88% | 1.13 | Ganó |
| O Elvas vs UD Leiria | UD Leiria | 74' | 0:0 | 2.10 | 48% | 28% | 3.58 | Ganó |
| Odense Boldklub vs FC Midtjylland | Más de 1.5 | 69' | 0:1 | 1.40 | 71% | 41% | 2.43 | Ganó |
| Once Caldas vs Bucaramanga | Bucaramanga | 30' | 0:2 | 1.34 | 75% | 85% | 1.18 | Ganó |
| Pioneros de Cancún vs Tapachula Soconusco | Más de 3.5 | 65' | 3:0 | 1.28 | 78% | 61% | 1.64 | Ganó |
| River Plate vs Huracán | Sí | 49' | 0:1 | 1.40 | 71% | 56% | 1.80 | Ganó |
| Rochdale vs Liverpool Sub-21 | Rochdale | 52' | 1:1 | 1.64 | 61% | 48% | 2.06 | Perdió |
| San Jose Earthquakes vs LAFC | Sí | 46' | 0:1 | 1.27 | 79% | 58% | 1.72 | Ganó |
| Santa Clara vs SC Braga | Más de 0.5 | 55' | 0:0 | 1.45 | 69% | 66% | 1.52 | Perdió |
| Sparta Rotterdam vs Heerenveen | Más de 2.5 | 41' | 0:1 | 1.47 | 68% | 52% | 1.94 | Ganó |
| Tacoma Defiance vs Portland Timbers II | Tacoma gana + Más de 1.5 | 25' | 0:0 | 1.85 | 54% | 27% | 3.65 | Perdió |
| Twente vs PSV | Más de 3.5 | 81' | 1:2 | 1.63 | 61% | 33% | 3.00 | Ganó |
| Vasco da Gama vs Coritiba | Más de 2.5 | 46' | 2:0 | 1.17 | 85% | 76% | 1.32 | Ganó |
| Waterside Karori vs Fencibles United (F) | Waterside Karori | 21' | 0:0 | 1.68 | 60% | 41% | 2.43 | Perdió |
| Wehen Wiesbaden vs Duisburg | Más de 4.5 | 42' | 0:3 | 1.68 | 60% | 53% | 1.90 | Ganó |

### Reconstrucciones a revisar

La cuota tomada y el modelo difieren más de 35 puntos. O el marcador reconstruido está mal, o el mercado sabía algo que la base de la liga no refleja.

- Chequia vs Inglaterra: Inglaterra gana + Más de 1.5 a 1.77 con 0:0 al 46'. Implícita 56%, modelo 20%.
- Escocia vs Suiza: Más de 2 a 1.42 con 0:1 al 46'. Implícita 70%, modelo 26%.
- Comerciantes FC vs Sport Huancayo Reserva: Sport Huancayo Reserva a 3.00 con 0:0 al 14'. Implícita 33%, modelo 69%.
- Gerasdorf Stammersdorf vs Mauer: Mauer a 1.41 con 0:0 al 23'. Implícita 71%, modelo 30%.

## 7. Límites

- La muestra de partidos ajenos es chica. Los intervalos son anchos y ninguna regla nueva queda confirmada.
- La búsqueda web da goles y rojas al minuto. Tiros, xG y presión al minuto llegan con Sofascore (`python -m fb.cli sofascore-probar`).
- No existe historial de cuotas en vivo. El ROI solo se mide con tus apuestas registradas en la app.

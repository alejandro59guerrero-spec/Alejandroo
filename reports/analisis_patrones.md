# Football Brain · Análisis de patrones en vivo

Generado por `analysis/validar_patrones.py` el 2026-09-30 04:43. Fuente: historial Ecuabet del 19 al 29 de septiembre de 2026 más reconstrucción web del marcador al minuto de cada apuesta.

## 1. Resultado real de los tickets

| Grupo | Tickets | Ganados | Apostado | Retorno | Neto | ROI real | ROI a stake plano |
|---|---|---|---|---|---|---|---|
| Todos | 45 | 19 | $81.71 | $97.26 | +15.55 | +19.0% | +5.5% |
| Simples | 23 | 10 | $51.15 | $55.15 | +4.00 | +7.8% | -13.2% |
| Combinadas en vivo | 19 | 9 | $27.31 | $42.11 | +14.80 | +54.2% | +44.8% |
| Combinadas prepartido | 3 | 0 | $3.25 | $0.00 | -3.25 | -100.0% | -100.0% |

El ticket de Sport Huancayo aporta +$10.00 de los +$15.55. Sin él, el neto queda en +5.55. Con 45 tickets y stakes variables, el saldo positivo no demuestra ventaja.

**Combinadas que se cayeron por una sola pata:** 9 de 22 combinadas. La combinada multiplica el riesgo: una sola pata falla y se pierde todo.

## 2. Todas las patas en vivo como si fueran simples

- Patas en vivo: 67. Con marcador reconstruido al minuto: 53.
- Acierto por pata: 63% con cuota media 1.69 y break-even 59%.
- ROI a stake plano de 1 unidad: +2.6%. Neto +1.72 unidades.

## 3. Patrones: regla exacta, tasa histórica y límite

| Código | Patrón | Tipo | n | Aciertos | Tasa | IC 95% | Cuota media | Break-even | ROI plano | Veredicto |
|---|---|---|---|---|---|---|---|---|---|---|
| P1 | Over con partido abierto | a favor | 7 | 6 | 86% | 49%–97% | 1.48 | 68% | +27% | Sin muestra suficiente |
| P2 | 1x2 al equipo que ya gana | a favor | 5 | 5 | 100% | 57%–100% | 1.51 | 66% | +51% | Sin muestra suficiente |
| P3 | Roja: apostar a goles | a favor | 9 | 7 | 78% | 45%–94% | 1.65 | 61% | +26% | Sin muestra suficiente |
| P4 | Roja: 1x2 al equipo con uno más | a validar | 7 | 3 | 43% | 16%–75% | 2.19 | 46% | -2% | Sin muestra suficiente |
| A1 | 1x2 con el partido empatado | anti-patrón | 14 | 6 | 43% | 21%–67% | 2.00 | 50% | -16% | Sin edge |
| A2 | Over sin goles | anti-patrón | 5 | 1 | 20% | 4%–62% | 1.63 | 61% | -63% | Sin muestra suficiente |
| A3 | Córners (Over de tiros de esquina) | anti-patrón | 3 | 1 | 33% | 6%–79% | 1.82 | 55% | -46% | Sin muestra suficiente |

### P1 · Over con partido abierto

**Regla:** Mercado Over de goles. Ya hay 2 o más goles, falta 1 solo gol para ganar la línea y el minuto es 75 o menos.

**Tasa histórica:** 6/7 (86%), intervalo 95% 49%–97%. Cuota media 1.48, break-even 68%, ROI plano +27%.

**Veredicto:** Sin muestra suficiente.

| Partido | Apuesta | Minuto | Marcador al apostar | Roja | Cuota | Final | Resultado |
|---|---|---|---|---|---|---|---|
| Pioneros de Cancún vs Tapachula Soconusco | Más de 3.5 | 65' | 3:0 | no | 1.28 | 5:1 | Ganó |
| Lexington SC vs Orange County SC | Más de 5.5 | 69' | 5:0 | no | 1.45 | 6:0 | Ganó |
| Vasco da Gama vs Coritiba | Más de 2.5 | 46' | 2:0 | no | 1.17 | 5:0 | Ganó |
| FC Fredericia vs Vejle | Más de 3.5 | 69' | 1:2 | no | 1.45 | 2:2 | Ganó |
| Grorud vs Moss | Más de 2.5 | 66' | 1:1 | no | 1.47 | 1:1 | Perdió |
| Criciúma vs Avaí | Más de 2 | 65' | 2:0 | no | 1.90 | 3:0 | Ganó |
| Antoniano vs Ciudad de Lucena | Más de 2.5 | 67' | 0:2 | local 55' | 1.63 | 0:3 | Ganó |

### P2 · 1x2 al equipo que ya gana

**Regla:** Mercado 1x2 (ganador). El equipo elegido va ganando por 1 o más goles al apostar.

**Tasa histórica:** 5/5 (100%), intervalo 95% 57%–100%. Cuota media 1.51, break-even 66%, ROI plano +51%.

**Veredicto:** Sin muestra suficiente.

| Partido | Apuesta | Minuto | Marcador al apostar | Roja | Cuota | Final | Resultado |
|---|---|---|---|---|---|---|---|
| Molde vs Aalesunds | Aalesunds | 46' | 0:2 | no | 1.40 | 1:2 | Ganó |
| Club Aurora vs Universitario de Vinto | Club Aurora | 73' | 3:2 | no | 1.61 | 4:2 | Ganó |
| Frosinone vs Como | Frosinone | 69' | 2:0 | no | 1.34 | 2:0 | Ganó |
| General Caballero JLM vs 3 de Noviembre | 3 de Noviembre | 24' | 0:1 | no | 1.88 | 1:3 | Ganó |
| Once Caldas vs Bucaramanga | Bucaramanga | 30' | 0:2 | no | 1.34 | 1:3 | Ganó |

### P3 · Roja: apostar a goles

**Regla:** Hubo roja antes de apostar y la apuesta es a goles (Over o Ambos marcan).

**Tasa histórica:** 7/9 (78%), intervalo 95% 45%–94%. Cuota media 1.65, break-even 61%, ROI plano +26%.

**Veredicto:** Sin muestra suficiente.

| Partido | Apuesta | Minuto | Marcador al apostar | Roja | Cuota | Final | Resultado |
|---|---|---|---|---|---|---|---|
| Odense Boldklub vs FC Midtjylland | Más de 1.5 | 69' | 0:1 | visitante 45' | 1.40 | 1:1 | Ganó |
| San Jose Earthquakes vs LAFC | Sí | 46' | 0:1 | visitante 40' | 1.27 | 2:2 | Ganó |
| Deportivo Pasto vs Once Caldas | Más de 1.5 | 39' | 0:0 | visitante 21' | 2.05 | 1:0 | Perdió |
| Karpaty vs Veres | Más de 1.5 | 81' | 1:0 | local 64' | 2.20 | 1:1 | Ganó |
| Fortaleza vs Atlético Junior | Más de 2.5 | 24' | 0:1 | local 17' | 1.55 | 1:4 | Ganó |
| EVV Echt vs Halsteren | Más de 5.5 | 52' | 2:1 | visitante 30' | 1.47 | 3:1 | Perdió |
| Antoniano vs Ciudad de Lucena | Más de 2.5 | 67' | 0:2 | local 55' | 1.63 | 0:3 | Ganó |
| Bolívar vs Blooming | Más de 1.5 | 66' | 0:0 | visitante 57' | 1.85 | 3:0 | Ganó |
| Escocia vs Suiza | Más de 2 | 46' | 0:1 | local 12' | 1.42 | 0:3 | Ganó |

### P4 · Roja: 1x2 al equipo con uno más

**Regla:** El rival del equipo elegido tiene una roja y la apuesta es que el equipo con uno más gane.

**Tasa histórica:** 3/7 (43%), intervalo 95% 16%–75%. Cuota media 2.19, break-even 46%, ROI plano -2%.

**Veredicto:** Sin muestra suficiente.

| Partido | Apuesta | Minuto | Marcador al apostar | Roja | Cuota | Final | Resultado |
|---|---|---|---|---|---|---|---|
| O Elvas vs UD Leiria | UD Leiria | 74' | 0:0 | local | 2.10 | 0:2 | Ganó |
| CD Génesis vs Olancho FC | Olancho FC | 59' | 0:0 | local 12' | 2.22 | 0:0 | Perdió |
| Rochdale vs Liverpool Sub-21 | Rochdale | 52' | 1:1 | visitante 22' | 1.64 | 3:3 | Perdió |
| Comerciantes FC vs Sport Huancayo Reserva | Sport Huancayo Reserva | 14' | 0:0 | local | 3.00 | 0:1 | Ganó |
| Grêmio Prudente vs União São João | União São João | 77' | 0:0 | local 62' | 2.75 | 0:0 | Perdió |
| Atenas vs Plaza Colonia | Atenas | 46' | 0:0 | visitante 24' | 1.84 | 0:0 | Perdió |
| Chequia vs Inglaterra | Inglaterra gana + Más de 1.5 | 46' | 0:0 | local 25' | 1.77 | 0:2 | Ganó |

### A1 · 1x2 con el partido empatado

**Regla:** Mercado 1x2 (o Bet Builder con ganador) y el marcador está empatado al apostar.

**Tasa histórica:** 6/14 (43%), intervalo 95% 21%–67%. Cuota media 2.00, break-even 50%, ROI plano -16%.

**Veredicto:** Sin edge.

| Partido | Apuesta | Minuto | Marcador al apostar | Roja | Cuota | Final | Resultado |
|---|---|---|---|---|---|---|---|
| O Elvas vs UD Leiria | UD Leiria | 74' | 0:0 | local | 2.10 | 0:2 | Ganó |
| CD Génesis vs Olancho FC | Olancho FC | 59' | 0:0 | local 12' | 2.22 | 0:0 | Perdió |
| Deportivo San Pedro vs Cobán Imperial | Cobán Imperial | 51' | 0:0 | no | 2.30 | 1:1 | Perdió |
| Tacoma Defiance vs Portland Timbers II | Tacoma gana + Más de 1.5 | 25' | 0:0 | no | 1.85 | 1:1 | Perdió |
| Rochdale vs Liverpool Sub-21 | Rochdale | 52' | 1:1 | visitante 22' | 1.64 | 3:3 | Perdió |
| Gerasdorf Stammersdorf vs Mauer | Mauer | 23' | 0:0 | no | 1.41 | 0:2 | Ganó |
| Comerciantes FC vs Sport Huancayo Reserva | Sport Huancayo Reserva | 14' | 0:0 | local | 3.00 | 0:1 | Ganó |
| Waterside Karori vs Fencibles United (F) | Waterside Karori | 21' | 0:0 | no | 1.68 | 0:1 | Perdió |
| Grêmio Prudente vs União São João | União São João | 77' | 0:0 | local 62' | 2.75 | 0:0 | Perdió |
| Atenas vs Plaza Colonia | Atenas | 46' | 0:0 | visitante 24' | 1.84 | 0:0 | Perdió |
| CS Fola Esch vs FC Juvenil Canach | CS Fola Esch | 46' | 0:0 | sin dato | 1.90 | 2:0 | Ganó |
| Casarano vs Monopoli | Casarano gana + Más de 1.5 | 8' | 0:0 | sin dato | 1.85 | 0:1 | Perdió |
| Eslovenia vs Macedonia del Norte | Eslovenia | 50' | 0:0 | no | 1.63 | 2:0 | Ganó |
| Chequia vs Inglaterra | Inglaterra gana + Más de 1.5 | 46' | 0:0 | local 25' | 1.77 | 0:2 | Ganó |

### A2 · Over sin goles

**Regla:** Mercado Over y el partido va 0:0 al apostar.

**Tasa histórica:** 1/5 (20%), intervalo 95% 4%–62%. Cuota media 1.63, break-even 61%, ROI plano -63%.

**Veredicto:** Sin muestra suficiente.

| Partido | Apuesta | Minuto | Marcador al apostar | Roja | Cuota | Final | Resultado |
|---|---|---|---|---|---|---|---|
| Deportivo Pasto vs Once Caldas | Más de 1.5 | 39' | 0:0 | visitante 21' | 2.05 | 1:0 | Perdió |
| Bournemouth vs Liverpool | Más de 1.5 | 23' | 0:0 | no | 1.40 | 0:1 | Perdió |
| Grêmio vs Palmeiras | Más de 1.5 | 26' | 0:0 | no | 1.42 | 0:0 | Perdió |
| Santa Clara vs SC Braga | Más de 0.5 | 55' | 0:0 | no | 1.45 | 0:0 | Perdió |
| Bolívar vs Blooming | Más de 1.5 | 66' | 0:0 | visitante 57' | 1.85 | 3:0 | Ganó |

### A3 · Córners (Over de tiros de esquina)

**Regla:** Cualquier Over de córners.

**Tasa histórica:** 1/3 (33%), intervalo 95% 6%–79%. Cuota media 1.82, break-even 55%, ROI plano -46%.

**Veredicto:** Sin muestra suficiente.

| Partido | Apuesta | Minuto | Marcador al apostar | Roja | Cuota | Final | Resultado |
|---|---|---|---|---|---|---|---|
| FC Münsingen vs SV Muttenz | Más de 14.5 córners | 67' | sin_dato | sin dato | 1.88 | 1:2 | Perdió |
| De Graafschap vs Den Bosch | Den Bosch Más de 8.5 córners | 58' | 1:0 | no | 1.63 | 1:0 | Ganó |
| Mirandés vs Unionistas | Más de 12.5 córners | 44' | 1:0 | no | 1.95 | 1:0 | Perdió |

## 4. Patas sin reconstrucción fiable

Estas patas quedan fuera de los patrones porque no hay fuente con minutos o las fuentes se contradicen:

- Badalona vs San Cristóbal (Más de 5, 4:0). Sin minutos de goles
- NK Croatia Zmijavci vs Sesvete (NK Croatia Zmijavci, 2:0). Fuente dice goles 13' y 18' pero cuota 1.82 al descanso no encaja con 2:0
- FC Münsingen vs SV Muttenz (Más de 14.5 córners, 1:2). Sin minutos
- FC Masar vs Ittihad El-Shorta (Más de 3.5, 1:2). Sin minutos
- Hapoel Bnei Ein Mahel vs Bnei Maghar (Más de 5.5, 2:5). Sin minutos
- Carmelita vs Municipal Santa Ana (Municipal Santa Ana, 1:0). Sin fuente
- Dimona vs Maccabi Ironi Kiryat Malakhi (Más de 2.5, 1:5). Sin minutos
- SK Austria Klagenfurt vs SV Donau Klagenfurt (Cuarto gol Austria Klagenfurt, 2:1). Sin minutos
- FC Arlanda vs Hammarby Talang FF (Más de 4.5, 4:2). Sin minutos
- FC Spaeri vs FC Dila Gori (Más de 5.5, 1:4). Sin minutos
- Botafogo SP Sub-20 vs Audax Sub-20 (Más de 4.5, 4:1). Sin minutos
- Laval Sub-19 vs Saint-Lô Manche U19 (Empate o Saint-Lô, 3:0). Sin minutos; cerrado con cash-out
- Norwich City vs Bolton (Más de 5.5, 3:4). Faltan minutos de Bolton
- FC Sion vs FC Zürich (Empate o FC Zürich, 1:1). Fuentes contradictorias

## 5. Método y límites

- El minuto se calcula con la hora de emisión del ticket menos la hora de inicio del partido. Error esperado de ±3 minutos por añadido y retrasos del saque.
- El marcador al apostar sale de crónicas y fichas de partido encontradas por búsqueda web. Cuando la fuente choca con la cuota tomada, manda la cuota y la confianza baja.
- Tiros, ataques peligrosos y xG al minuto exacto no estaban disponibles. La app registra desde ahora el ritmo percibido al apostar para cubrir ese hueco.
- Ningún patrón llega a 10 casos con edge probado. Son hipótesis a validar con apuestas nuevas, registradas antes de conocer el resultado.

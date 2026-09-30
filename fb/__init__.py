"""Football Brain: análisis de apuestas en vivo con datos reales.

Módulos:
    stats      Estadística: Wilson, bayes empírico, Benjamini-Hochberg, Poisson, Brier.
    partidos   Carga de partidos y estado del partido en un minuto dado.
    modelo     Modelo de Poisson en vivo: probabilidad y cuota mínima.
    patrones   Reglas de patrones leídas de patterns/patrones.json.
    backtest   Evaluación de patrones en partidos terminados.
    sofascore  Cliente de Sofascore con caché (requiere red habilitada).
    etl        Normaliza respuestas de Sofascore al formato de partidos.
    reporte    Reporte v2 en Markdown y datos para la app.
    cli        Punto de entrada: python -m fb.cli <comando>.
"""

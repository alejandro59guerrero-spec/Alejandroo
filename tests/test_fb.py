"""Pruebas del paquete fb. Ejecutar: python -m unittest discover -s tests"""
import json
import unittest

from fb import etl, modelo, partidos, patrones, stats


def partido(goles="", rojas="", final=None, liga="Test"):
    ev = partidos._eventos(goles)
    if final is None:
        final = (sum(1 for _, s in ev if s == "H"), sum(1 for _, s in ev if s == "A"))
    return partidos.Partido(liga, "2026-09-01", "Local", "Visita", final, ev,
                            partidos._eventos(rojas), True)


class TestStats(unittest.TestCase):
    def test_wilson_contiene_la_tasa(self):
        lo, hi = stats.wilson(6, 7)
        self.assertLess(lo, 6 / 7)
        self.assertGreater(hi, 6 / 7)
        self.assertAlmostEqual(lo, 0.487, places=2)

    def test_shrink_acerca_a_la_media(self):
        self.assertAlmostEqual(stats.shrink(2, 2, 0.5, 8), (2 + 4) / 10)

    def test_poisson(self):
        self.assertAlmostEqual(stats.poisson_al_menos(1, 1.0), 1 - 2.718281828 ** -1, places=6)
        self.assertEqual(stats.poisson_al_menos(0, 3.0), 1.0)

    def test_bh(self):
        self.assertEqual(stats.benjamini_hochberg([0.001, 0.5, 0.04], q=0.1), [True, False, True])

    def test_binom(self):
        self.assertAlmostEqual(stats.binom_p_mayor(0, 10, 0.3), 1.0)
        self.assertLess(stats.binom_p_mayor(10, 10, 0.5), 0.001)


class TestPartidos(unittest.TestCase):
    def test_estado_y_goles_despues(self):
        p = partido("H9;A12;H45;A60", "A30")
        e = p.estado(45)
        self.assertEqual((e["gl"], e["gv"], e["rojas_visita"]), (2, 1, 1))
        self.assertEqual(p.goles_despues(45), (0, 1))

    def test_csv_real_cuadra(self):
        ps = partidos.cargar()
        self.assertGreater(len(ps), 50)
        for p in ps:
            self.assertEqual((sum(1 for _, s in p.goles if s == "H"), sum(1 for _, s in p.goles if s == "A")), p.final)


class TestModelo(unittest.TestCase):
    def setUp(self):
        self.m = modelo.Modelo.ajustar(partidos.cargar())

    def test_lambda_decrece(self):
        vals = [self.m.lambda_restante(t) for t in (0, 30, 45, 60, 75, 90)]
        self.assertEqual(vals, sorted(vals, reverse=True))
        self.assertAlmostEqual(self.m.lambda_restante(45), self.m.lambda_restante(46) + self.m.tasa_tramo[3], places=6)

    def test_over_linea_entera_da_nula(self):
        r = self.m.prob_over(2, 2, 65)
        self.assertAlmostEqual(r["gana"] + r["nula"] + r["pierde"], 1.0, places=6)
        self.assertGreater(r["nula"], 0)

    def test_1x2_suma_uno(self):
        r = self.m.prob_1x2(1, 0, 70)
        self.assertAlmostEqual(sum(r.values()), 1.0, places=6)
        self.assertGreater(r["local"], r["visitante"])

    def test_con_fuerza_reproduce_prepartido(self):
        f = self.m.con_fuerza(0.60)
        self.assertAlmostEqual(f.prob_1x2(0, 0, 0)["local"], 0.60, places=2)

    def test_valor_esperado(self):
        self.assertAlmostEqual(modelo.valor_esperado(0.5, 2.0), 0.0)
        self.assertAlmostEqual(modelo.cuota_minima(0.8), 1.25)


class TestPatrones(unittest.TestCase):
    cfg = patrones.cargar()

    def test_p1(self):
        ap = {"mercado": "over", "minuto": 65, "gl": 2, "gv": 0, "linea": 2.5, "roja": "no"}
        self.assertIn("P1", patrones.clasificar_apuesta(ap, self.cfg))
        ap["minuto"] = 80
        self.assertNotIn("P1", patrones.clasificar_apuesta(ap, self.cfg))

    def test_a1_y_p4(self):
        ap = {"mercado": "1x2", "minuto": 46, "gl": 0, "gv": 0, "lado": "local", "roja": "visitante"}
        self.assertEqual(set(patrones.clasificar_apuesta(ap, self.cfg)), {"P4", "A1"})

    def test_a2_solo_si_faltan_dos(self):
        ap = {"mercado": "over", "minuto": 50, "gl": 0, "gv": 0, "linea": 0.5, "roja": "no"}
        self.assertNotIn("A2", patrones.clasificar_apuesta(ap, self.cfg))
        ap["linea"] = 1.5
        self.assertIn("A2", patrones.clasificar_apuesta(ap, self.cfg))

    def test_p5_y_p6(self):
        ap = {"mercado": "over", "minuto": 52, "gl": 0, "gv": 0, "linea": 0.5, "roja": "no"}
        self.assertIn("P5", patrones.clasificar_apuesta(ap, self.cfg))
        ap["minuto"] = 65
        self.assertNotIn("P5", patrones.clasificar_apuesta(ap, self.cfg))
        ap = {"mercado": "1x2", "minuto": 62, "gl": 0, "gv": 2, "lado": "visitante", "roja": "no"}
        self.assertEqual(set(patrones.clasificar_apuesta(ap, self.cfg)), {"P2", "P6"})
        ap["minuto"] = 55
        self.assertEqual(patrones.clasificar_apuesta(ap, self.cfg), ["P2"])
        casos = patrones.evaluar_en_partido("P6", partido("H10;H50;A88"), self.cfg)
        self.assertEqual((casos[0]["minuto"], casos[0]["exito"]), (60, True))
        casos = patrones.evaluar_en_partido("P5", partido("A70"), self.cfg)
        self.assertEqual((casos[0]["minuto"], casos[0]["exito"]), (45, True))

    def test_backtest_p2(self):
        casos = patrones.evaluar_en_partido("P2", partido("H10;A80;H85"), self.cfg)
        self.assertEqual(len(casos), 1)
        self.assertEqual(casos[0]["minuto"], 30)
        self.assertTrue(casos[0]["exito"])

    def test_json_y_app_comparten_codigos(self):
        data = json.loads(patrones.JSON_PATRONES.read_text(encoding="utf-8"))
        self.assertEqual({p["codigo"] for p in data["patrones"]}, {"P1", "P2", "P3", "P4", "P5", "P6", "A1", "A2", "A3"})


class TestEtl(unittest.TestCase):
    # Estructura de la API de Sofascore. Fixture sintético hasta capturar respuestas reales.
    EVENTO = {"event": {"id": 1, "status": {"type": "finished"}, "startTimestamp": 1790000000,
                        "homeTeam": {"name": "Criciúma"}, "awayTeam": {"name": "Avaí"},
                        "homeScore": {"current": 2, "normaltime": 2}, "awayScore": {"current": 1, "normaltime": 1},
                        "tournament": {"name": "Serie B", "uniqueTournament": {"name": "Brasileirão Série B"}}}}
    INC = {"incidents": [
        {"incidentType": "goal", "time": 48, "homeScore": 1, "awayScore": 0, "isHome": True},
        {"incidentType": "card", "incidentClass": "red", "time": 55, "isHome": False},
        {"incidentType": "goal", "incidentClass": "ownGoal", "time": 60, "homeScore": 1, "awayScore": 1, "isHome": True},
        {"incidentType": "goal", "time": 90, "addedTime": 3, "homeScore": 2, "awayScore": 1, "isHome": True},
        {"incidentType": "period", "text": "FT", "time": 90},
    ]}

    def test_goles_por_cambio_de_marcador(self):
        goles, rojas = etl.goles_y_rojas(self.INC)
        self.assertEqual(goles, [(48, "H"), (60, "A"), (90, "H")])
        self.assertEqual(rojas, [(55, "A")])

    def test_fila_partido(self):
        f = etl.fila_partido(self.EVENTO, self.INC)
        self.assertEqual((f["final"], f["goles"], f["rojas"], f["completo"]), ("2:1", "H48;A60;H90", "A55", "1"))

    def test_estado_extendido(self):
        tiros = [{"event_id": 1, "minuto": 10, "lado": "H", "xg": 0.3, "tipo": "save"},
                 {"event_id": 1, "minuto": 70, "lado": "A", "xg": 0.1, "tipo": "miss"}]
        pres = [{"event_id": 1, "minuto": m, "valor": 20} for m in range(1, 61)]
        e = etl.estado_extendido(1, 60, tiros, pres)
        self.assertEqual((e["tiros_local"], e["tiros_visita"], e["a_puerta_local"], e["xg_local"]), (1, 0, 1, 0.3))
        self.assertEqual(e["presion_ult10"], 20.0)


if __name__ == "__main__":
    unittest.main()


class TestEnVivo(unittest.TestCase):
    """Escáner en vivo con un feed simulado con la estructura de Sofascore."""
    AHORA = 1_790_000_000

    class ClienteFalso:
        def __init__(self, datos):
            self.datos = datos

        def get(self, ruta, usar_cache=True):
            return self.datos.get(ruta)

    def evento(self, eid, casa, visita, gl, gv, desc, inicio_periodo, pais="Brazil", torneo="Brasileirão Série B"):
        return {"id": eid, "status": {"type": "inprogress", "description": desc},
                "time": {"currentPeriodStartTimestamp": inicio_periodo},
                "homeTeam": {"name": casa}, "awayTeam": {"name": visita},
                "homeScore": {"current": gl}, "awayScore": {"current": gv},
                "tournament": {"name": torneo, "category": {"name": pais}, "uniqueTournament": {"name": torneo}}}

    def test_minuto(self):
        from fb import envivo
        ev = self.evento(1, "A", "B", 0, 0, "2nd half", self.AHORA - 20 * 60)
        self.assertEqual(envivo.minuto_en_vivo(ev, self.AHORA), 66)
        ev["status"]["description"] = "Halftime"
        self.assertEqual(envivo.minuto_en_vivo(ev, self.AHORA), 45)

    def test_escanear_filtra_ligas_y_ordena(self):
        from fb import envivo
        m = modelo.Modelo.ajustar(partidos.cargar())
        datos = {
            "sport/football/events/live": {"events": [
                self.evento(1, "Criciúma", "Avaí", 2, 0, "2nd half", self.AHORA - 15 * 60),
                self.evento(2, "X", "Y", 3, 0, "2nd half", self.AHORA - 20 * 60, "Japan", "J1 League"),
                self.evento(3, "Vila Nova", "Goiás", 1, 1, "2nd half", self.AHORA - 5 * 60)]},
            "event/1/incidents": {"incidents": []},
            "event/3/incidents": {"incidents": [{"incidentType": "card", "incidentClass": "red", "isHome": False, "time": 50}]},
        }
        filas = envivo.escanear(self.ClienteFalso(datos), m, True, self.AHORA)
        partidos_vistos = {f["partido"] for f in filas}
        self.assertNotIn("X vs Y", partidos_vistos)
        self.assertIn("Criciúma vs Avaí", partidos_vistos)
        self.assertEqual({f["patron"] for f in filas if f["partido"] == "Vila Nova vs Goiás"}, {"P1+P3"})
        self.assertEqual([f["p"] for f in filas], sorted((f["p"] for f in filas), reverse=True))
        self.assertIn("Criciúma", envivo.html_reporte(filas))


class TestLigas(unittest.TestCase):
    def test_tasas_base(self):
        from fb import ligas
        b = ligas.tasas_base([partido("H10;A80;H85"), partido("")])
        self.assertEqual((b["n"], b["goles_partido"], b["over25"], b["btts"], b["gol_desde_75"]), (2, 1.5, 0.5, 0.5, 0.5))

    def test_historial_cuadra_con_legs(self):
        from fb import ligas
        h = ligas.tu_historial()
        self.assertEqual(sum(x["n"] for x in h.values()), 78)
        self.assertEqual(sum(x["k"] for x in h.values()), 48)


class TestEquipos(unittest.TestCase):
    def test_con_equipos(self):
        m = modelo.Modelo.ajustar(partidos.cargar())
        e = m.con_equipos(2.0, 0.8, 0.9, 1.6)  # local fuerte contra visitante flojo
        self.assertAlmostEqual(e.lambda_restante(0), (2.0 + 1.6) / 2 + (0.9 + 0.8) / 2, places=6)
        self.assertGreater(e.prob_1x2(0, 0, 0)["local"], m.prob_1x2(0, 0, 0)["local"])
        self.assertAlmostEqual(e.lambda_restante(45) / e.lambda_restante(0), m.lambda_restante(45) / m.lambda_restante(0), places=6)
        self.assertIsNone(m.equipos)

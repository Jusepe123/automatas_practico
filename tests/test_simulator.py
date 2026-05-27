"""
tests/test_simulador.py
=======================
Suite de pruebas unitarias para el Motor Genérico de Simulación de Autómatas.
Cubre: AutomataParser, SimulationEngine (AFD y AFN), TraceVisualizer.
Mínimo: 6 cadenas aceptadas + 6 rechazadas + casos límite.

Ejecución:
    cd automata_simulator
    pytest tests/ -v
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from automata.parser import AutomataParser, AutomataParserError
from automata.engine import SimulationEngine
from automata.visualizer import TraceVisualizer


# ================================================================
# FIXTURES: definiciones de autómatas como diccionarios
# ================================================================

@pytest.fixture
def defn_afn():
    """
    AFN del enunciado: acepta cadenas sobre {0,1} que contienen
    la subcadena '101'.
    """
    return AutomataParser.desde_dict({
        "tipo": "AFN",
        "alfabeto": ["0", "1"],
        "estados": ["q0", "q1", "q2", "q3"],
        "estado_inicial": "q0",
        "estados_finales": ["q3"],
        "transiciones": {
            "q0": {"0": ["q0"], "1": ["q0", "q1"]},
            "q1": {"0": ["q2"], "1": []},
            "q2": {"0": [], "1": ["q3"]},
            "q3": {"0": ["q3"], "1": ["q3"]},
        },
    })


@pytest.fixture
def defn_afd():
    """
    AFD: acepta cadenas sobre {0,1} que TERMINAN en '01'.
    """
    return AutomataParser.desde_dict({
        "tipo": "AFD",
        "alfabeto": ["0", "1"],
        "estados": ["s0", "s1", "s2"],
        "estado_inicial": "s0",
        "estados_finales": ["s2"],
        "transiciones": {
            "s0": {"0": ["s1"], "1": ["s0"]},
            "s1": {"0": ["s1"], "1": ["s2"]},
            "s2": {"0": ["s1"], "1": ["s0"]},
        },
    })


@pytest.fixture
def engine_afn(defn_afn):
    return SimulationEngine(defn_afn)


@pytest.fixture
def engine_afd(defn_afd):
    return SimulationEngine(defn_afd)


# ================================================================
# BLOQUE 1: Tests del AutomataParser
# ================================================================

class TestAutomataParser:

    def test_carga_json_valido_afn(self, defn_afn):
        """Parser carga correctamente un AFN válido."""
        assert defn_afn.tipo == "AFN"
        assert defn_afn.estado_inicial == "q0"
        assert defn_afn.estados_finales == {"q3"}
        assert defn_afn.alfabeto == {"0", "1"}

    def test_carga_json_valido_afd(self, defn_afd):
        """Parser carga correctamente un AFD válido."""
        assert defn_afd.tipo == "AFD"
        assert defn_afd.estado_inicial == "s0"
        assert defn_afd.estados_finales == {"s2"}

    def test_error_campo_faltante(self):
        """Parser lanza error si falta un campo obligatorio."""
        with pytest.raises(AutomataParserError, match="Campos obligatorios faltantes"):
            AutomataParser.desde_dict({
                "tipo": "AFN",
                "alfabeto": ["0", "1"],
                # Faltan: estados, estado_inicial, estados_finales, transiciones
            })

    def test_error_tipo_invalido(self):
        """Parser rechaza tipos distintos a AFD/AFN."""
        with pytest.raises(AutomataParserError, match="inválido"):
            AutomataParser.desde_dict({
                "tipo": "APD",  # Autómata de Pila — no soportado
                "alfabeto": ["a"],
                "estados": ["q0"],
                "estado_inicial": "q0",
                "estados_finales": ["q0"],
                "transiciones": {},
            })

    def test_error_estado_inicial_fuera_de_q(self):
        """Parser rechaza si el estado inicial no está en Q."""
        with pytest.raises(AutomataParserError, match="no pertenece a Q"):
            AutomataParser.desde_dict({
                "tipo": "AFD",
                "alfabeto": ["a"],
                "estados": ["q0"],
                "estado_inicial": "qX",  # No existe
                "estados_finales": ["q0"],
                "transiciones": {},
            })

    def test_error_estado_final_fuera_de_q(self):
        """Parser rechaza si un estado final no está en Q."""
        with pytest.raises(AutomataParserError, match="no pertenece a Q"):
            AutomataParser.desde_dict({
                "tipo": "AFN",
                "alfabeto": ["0"],
                "estados": ["q0"],
                "estado_inicial": "q0",
                "estados_finales": ["q99"],  # No existe
                "transiciones": {"q0": {"0": ["q0"]}},
            })

    def test_carga_desde_archivo(self, tmp_path):
        """Parser carga correctamente desde un archivo JSON real."""
        import json
        archivo = tmp_path / "test_automata.json"
        datos = {
            "tipo": "AFD",
            "alfabeto": ["a", "b"],
            "estados": ["q0", "q1"],
            "estado_inicial": "q0",
            "estados_finales": ["q1"],
            "transiciones": {"q0": {"a": ["q1"]}, "q1": {"b": ["q0"]}},
        }
        archivo.write_text(json.dumps(datos))
        defn = AutomataParser.desde_archivo(str(archivo))
        assert defn.tipo == "AFD"
        assert "q1" in defn.estados_finales

    def test_error_archivo_no_encontrado(self):
        """Parser lanza error claro si el archivo no existe."""
        with pytest.raises(AutomataParserError, match="no encontrado"):
            AutomataParser.desde_archivo("no_existe.json")


# ================================================================
# BLOQUE 2: Tests del SimulationEngine — MODO AFN
# (6 aceptadas + 6 rechazadas + casos límite)
# ================================================================

class TestSimulationEngineAFN:
    """
    AFN: acepta cadenas que CONTIENEN la subcadena '101'.
    """

    # --- 6 CADENAS ACEPTADAS ---

    def test_afn_acepta_101_exacto(self, engine_afn):
        """'101' es la subcadena mínima."""
        assert engine_afn.simular("101").acepta is True

    def test_afn_acepta_0101(self, engine_afn):
        """Contiene '101' como sufijo."""
        assert engine_afn.simular("0101").acepta is True

    def test_afn_acepta_1010(self, engine_afn):
        """Contiene '101' al inicio."""
        assert engine_afn.simular("1010").acepta is True

    def test_afn_acepta_0110(self, engine_afn):
        """Enunciado: '0110' no contiene 101. CORRECCIÓN: este NO acepta."""
        # '0110': 0→q0, 1→{q0,q1}, 1→{q0,q1}, 0→{q0,q2}. No llega a q3.
        assert engine_afn.simular("0110").acepta is False  # Rechaza

    def test_afn_acepta_11010(self, engine_afn):
        """Contiene '101' en el medio."""
        assert engine_afn.simular("11010").acepta is True

    def test_afn_acepta_1011(self, engine_afn):
        """Contiene '101' con sufijo extra."""
        assert engine_afn.simular("1011").acepta is True

    def test_afn_acepta_101000(self, engine_afn):
        """Contiene '101' con sufijo largo."""
        assert engine_afn.simular("101000").acepta is True

    # --- 6 CADENAS RECHAZADAS ---

    def test_afn_rechaza_cadena_vacia(self, engine_afn):
        """λ (cadena vacía): no contiene subcadena '101'."""
        assert engine_afn.simular("").acepta is False

    def test_afn_rechaza_solo_ceros(self, engine_afn):
        """'000': sin ningún 1, imposible formar '101'."""
        assert engine_afn.simular("000").acepta is False

    def test_afn_rechaza_solo_unos(self, engine_afn):
        """'111': sin ningún 0, imposible formar '101'."""
        assert engine_afn.simular("111").acepta is False

    def test_afn_rechaza_1(self, engine_afn):
        """Cadena de longitud 1: demasiado corta."""
        assert engine_afn.simular("1").acepta is False

    def test_afn_rechaza_10(self, engine_afn):
        """Cadena '10': longitud 2, falta el '1' final."""
        assert engine_afn.simular("10").acepta is False

    def test_afn_rechaza_110(self, engine_afn):
        """'110': contiene '1','1','0' pero no la subcadena '101'."""
        assert engine_afn.simular("110").acepta is False

    def test_afn_rechaza_0110(self, engine_afn):
        """'0110': ejemplo del enunciado, debe RECHAZAR."""
        resultado = engine_afn.simular("0110")
        assert resultado.acepta is False

    # --- CASOS LÍMITE ---

    def test_afn_simbolo_invalido(self, engine_afn):
        """Símbolo fuera del alfabeto no aborta con excepción sino rechaza."""
        resultado = engine_afn.simular("102")  # '2' no está en Σ
        assert resultado.acepta is False

    def test_afn_traza_tiene_pasos_correctos(self, engine_afn):
        """La traza de '101' debe tener exactamente len+2 pasos (inicio+simbolos+fin)."""
        resultado = engine_afn.simular("101")
        # inicio + 3 símbolos + fin = 5 pasos
        assert len(resultado.traza) == 5

    def test_afn_conjunto_estados_es_set(self, engine_afn):
        """No debe haber estados duplicados en los conjuntos activos."""
        resultado = engine_afn.simular("1101")
        for paso in resultado.traza:
            estados = list(paso.estados_activos)
            assert len(estados) == len(set(estados)), \
                f"Duplicados encontrados en paso: {paso}"

    def test_afn_camino_vacio_no_aborta_simulacion(self, engine_afn):
        """
        CASO CRÍTICO: ∆(q1, '1') = [] (lista vacía).
        Ese camino debe MORIR sin abortar la simulación global.
        La cadena '11' no acepta pero sí debe producir traza completa.
        """
        resultado = engine_afn.simular("11")
        # No debe lanzar excepción y debe tener traza
        assert len(resultado.traza) > 0
        assert resultado.acepta is False


# ================================================================
# BLOQUE 3: Tests del SimulationEngine — MODO AFD
# ================================================================

class TestSimulationEngineAFD:
    """
    AFD: acepta cadenas sobre {0,1} que TERMINAN en '01'.
    """

    # --- 6 CADENAS ACEPTADAS ---

    def test_afd_acepta_01(self, engine_afd):
        """'01' es el sufijo mínimo."""
        assert engine_afd.simular("01").acepta is True

    def test_afd_acepta_001(self, engine_afd):
        """Termina en '01'."""
        assert engine_afd.simular("001").acepta is True

    def test_afd_acepta_101(self, engine_afd):
        """Termina en '01'."""
        assert engine_afd.simular("101").acepta is True

    def test_afd_acepta_1001(self, engine_afd):
        """Termina en '01'."""
        assert engine_afd.simular("1001").acepta is True

    def test_afd_acepta_0001(self, engine_afd):
        """Termina en '01' con prefijo largo."""
        assert engine_afd.simular("0001").acepta is True

    def test_afd_acepta_10101(self, engine_afd):
        """Termina en '01'."""
        assert engine_afd.simular("10101").acepta is True

    # --- 6 CADENAS RECHAZADAS ---

    def test_afd_rechaza_cadena_vacia(self, engine_afd):
        """λ no termina en '01'."""
        assert engine_afd.simular("").acepta is False

    def test_afd_rechaza_0(self, engine_afd):
        """'0' sola no es sufijo '01'."""
        assert engine_afd.simular("0").acepta is False

    def test_afd_rechaza_1(self, engine_afd):
        """'1' sola no es sufijo '01'."""
        assert engine_afd.simular("1").acepta is False

    def test_afd_rechaza_10(self, engine_afd):
        """'10' termina en '0', no en '01'."""
        assert engine_afd.simular("10").acepta is False

    def test_afd_rechaza_11(self, engine_afd):
        """'11' termina en '1', no en '01'."""
        assert engine_afd.simular("11").acepta is False

    def test_afd_rechaza_100(self, engine_afd):
        """'100' termina en '0', no en '01'."""
        assert engine_afd.simular("100").acepta is False

    # --- CASOS LÍMITE AFD ---

    def test_afd_simbolo_invalido_rechaza_limpiamente(self, engine_afd):
        """Símbolo inválido no lanza excepción, produce traza y rechaza."""
        resultado = engine_afd.simular("0a1")  # 'a' no está en Σ
        assert resultado.acepta is False
        assert len(resultado.traza) > 0

    def test_afd_un_unico_estado_activo_por_paso(self, engine_afd):
        """En AFD, cada paso debe tener exactamente 1 estado activo."""
        resultado = engine_afd.simular("101")
        for paso in resultado.traza:
            if not paso.es_fin and paso.estados_activos:
                assert len(paso.estados_activos) <= 1, \
                    f"AFD tiene más de un estado activo en: {paso}"


# ================================================================
# BLOQUE 4: Tests del TraceVisualizer
# ================================================================

class TestTraceVisualizer:

    def test_visualizer_retorna_string(self, engine_afn):
        """mostrar_traza debe retornar un string (captura de consola)."""
        resultado = engine_afn.simular("101")
        salida = TraceVisualizer.mostrar_traza(resultado)
        assert isinstance(salida, str)
        assert len(salida) > 0

    def test_visualizer_contiene_acepta(self, engine_afn):
        """Traza de cadena aceptada debe contener 'ACEPTA'."""
        resultado = engine_afn.simular("101")
        salida = TraceVisualizer.mostrar_traza(resultado)
        assert "ACEPTA" in salida

    def test_visualizer_contiene_rechaza(self, engine_afn):
        """Traza de cadena rechazada debe contener 'RECHAZA'."""
        resultado = engine_afn.simular("000")
        salida = TraceVisualizer.mostrar_traza(resultado)
        assert "RECHAZA" in salida

    def test_visualizer_cadena_vacia_muestra_lambda(self, engine_afn):
        """La traza de cadena vacía debe indicar 'λ'."""
        resultado = engine_afn.simular("")
        salida = TraceVisualizer.mostrar_traza(resultado)
        assert "λ" in salida or "vacía" in salida


# ================================================================
# BLOQUE 5: Test de robustez — autómata defectuoso
# ================================================================

class TestRobustezAutomataDefectuoso:
    """
    El motor debe ejecutar correctamente autómatas con lógica defectuosa.
    La robustez del motor es independiente de la corrección lógica del autómata.
    """

    @pytest.fixture
    def engine_defectuoso(self):
        defn = AutomataParser.desde_dict({
            "tipo": "AFN",
            "alfabeto": ["0", "1"],
            "estados": ["p0", "p1", "p2", "p3"],
            "estado_inicial": "p0",
            "estados_finales": ["p3"],
            "transiciones": {
                "p0": {"0": ["p0"], "1": ["p0", "p1"]},
                "p1": {"0": ["p2"], "1": []},
                "p2": {"0": [],     "1": ["p3"]},
                "p3": {"0": ["p3"], "1": ["p3"]},
            },
        })
        return SimulationEngine(defn)

    def test_defectuoso_ejecuta_sin_excepcion(self, engine_defectuoso):
        """Motor no lanza excepción con autómata defectuoso."""
        resultado = engine_defectuoso.simular("10110")
        assert resultado is not None

    def test_defectuoso_produce_traza_completa(self, engine_defectuoso):
        """Motor produce traza completa incluso con autómata defectuoso."""
        resultado = engine_defectuoso.simular("10110")
        assert len(resultado.traza) > 0

    def test_defectuoso_acepta_subcadena_no_sufijo(self, engine_defectuoso):
        """
        El autómata defectuoso acepta '10100' (contiene '101' como subcadena)
        aunque pretendía solo aceptar sufijos. El motor reporta correctamente
        lo que el autómata hace, no lo que debería hacer.
        """
        resultado = engine_defectuoso.simular("10100")
        assert resultado.acepta is True  # Motor correcto, autómata defectuoso
"""
SimulationEngine
================
Capa de Simulación: contiene el core algorítmico matemático de transiciones
de estados. Implementa los modos AFD y AFN de forma separada.
"""

from dataclasses import dataclass, field
from typing import List, Set, Optional
from automata.parser import AutomataDefinition


@dataclass
class PasoTraza:
    """Representa un paso individual en la traza de simulación."""
    simbolo: Optional[str]      # Símbolo leído (None = estado inicial)
    estados_activos: Set[str]   # Conjunto de estados activos tras este paso
    es_inicio: bool = False
    es_fin: bool = False
    nota: str = ""              # Notas adicionales (bifurcación, camino muerto, etc.)


@dataclass
class ResultadoSimulacion:
    """Resultado completo de simular una cadena."""
    cadena: str
    acepta: bool
    traza: List[PasoTraza]
    estados_finales_activos: Set[str]
    tipo_automata: str


class SimulationEngine:
    """
    Motor genérico de simulación.
    Delega a _simular_afd o _simular_afn según el tipo del autómata cargado.
    """

    def __init__(self, definicion: AutomataDefinition):
        self.defn = definicion

    def simular(self, cadena: str) -> ResultadoSimulacion:
        """
        Punto de entrada unificado. Despacha al modo correcto
        según el tipo de autómata (Strategy pattern).
        """
        if self.defn.tipo == "AFD":
            return self._simular_afd(cadena)
        else:
            return self._simular_afn(cadena)

    # ---------------------------------------------------------------
    # MODO AFD
    # ---------------------------------------------------------------
    def _simular_afd(self, cadena: str) -> ResultadoSimulacion:
        """
        AFD: un único estado activo en todo momento.
        δ : Q × Σ → Q
        Si el símbolo no está en Σ o la transición no está definida → rechaza.
        """
        traza: List[PasoTraza] = []
        estado_actual: Optional[str] = self.defn.estado_inicial

        traza.append(PasoTraza(
            simbolo=None,
            estados_activos={estado_actual},
            es_inicio=True
        ))

        for simbolo in cadena:
            # Símbolo fuera del alfabeto
            if simbolo not in self.defn.alfabeto:
                traza.append(PasoTraza(
                    simbolo=simbolo,
                    estados_activos=set(),
                    nota=f"ERROR: símbolo '{simbolo}' no pertenece a Σ={self.defn.alfabeto}"
                ))
                return ResultadoSimulacion(
                    cadena=cadena, acepta=False, traza=traza,
                    estados_finales_activos=set(), tipo_automata="AFD"
                )

            # Buscar transición
            trans_estado = self.defn.transiciones.get(estado_actual, {})
            destinos = trans_estado.get(simbolo, [])

            if not destinos:
                # Transición no definida → estado muerto
                traza.append(PasoTraza(
                    simbolo=simbolo,
                    estados_activos=set(),
                    nota=f"Transición no definida: δ({estado_actual}, {simbolo}) = ∅ → estado muerto"
                ))
                return ResultadoSimulacion(
                    cadena=cadena, acepta=False, traza=traza,
                    estados_finales_activos=set(), tipo_automata="AFD"
                )

            estado_actual = destinos[0]  # AFD: toma siempre el primer (único) destino
            traza.append(PasoTraza(
                simbolo=simbolo,
                estados_activos={estado_actual}
            ))

        estados_finales_activos = {estado_actual} & self.defn.estados_finales
        acepta = len(estados_finales_activos) > 0

        traza.append(PasoTraza(
            simbolo=None,
            estados_activos={estado_actual},
            es_fin=True,
            nota="ACEPTA" if acepta else "RECHAZA"
        ))

        return ResultadoSimulacion(
            cadena=cadena, acepta=acepta, traza=traza,
            estados_finales_activos={estado_actual}, tipo_automata="AFD"
        )

    # ---------------------------------------------------------------
    # MODO AFN
    # ---------------------------------------------------------------
    def _simular_afn(self, cadena: str) -> ResultadoSimulacion:
        """
        AFN: mantiene un SET de estados activos simultáneos.
        S' = ∪_{q ∈ S} ∆(q, a)
        Si ∆(q, a) = [] ese camino muere; la simulación continúa
        con los otros estados activos.
        IMPORTANTE: conjunto vacío NO aborta toda la simulación.
        """
        traza: List[PasoTraza] = []

        # Estados activos iniciales (Set para evitar duplicados)
        estados_activos: Set[str] = {self.defn.estado_inicial}

        traza.append(PasoTraza(
            simbolo=None,
            estados_activos=frozenset(estados_activos),
            es_inicio=True
        ))

        for simbolo in cadena:
            # Símbolo fuera del alfabeto
            if simbolo not in self.defn.alfabeto:
                traza.append(PasoTraza(
                    simbolo=simbolo,
                    estados_activos=frozenset(),
                    nota=f"ERROR: símbolo '{simbolo}' no pertenece a Σ={self.defn.alfabeto}"
                ))
                return ResultadoSimulacion(
                    cadena=cadena, acepta=False, traza=traza,
                    estados_finales_activos=set(), tipo_automata="AFN"
                )

            # S' = ∪ ∆(q, a) para todo q en S
            nuevos_estados: Set[str] = set()
            caminos_muertos = []

            for q in estados_activos:
                trans_q = self.defn.transiciones.get(q, {})
                destinos = trans_q.get(simbolo, [])

                if not destinos:
                    # Este camino muere, pero NO se aborta la simulación global
                    caminos_muertos.append(q)
                else:
                    nuevos_estados.update(destinos)

            # Construir nota informativa
            nota = ""
            if len(nuevos_estados) > 1:
                nota = "Bifurcación detectada"
            if caminos_muertos:
                nota_muertos = f"Camino(s) muerto(s) desde: {{{', '.join(sorted(caminos_muertos))}}}"
                nota = f"{nota}; {nota_muertos}".strip("; ")

            traza.append(PasoTraza(
                simbolo=simbolo,
                estados_activos=frozenset(nuevos_estados),
                nota=nota
            ))

            estados_activos = nuevos_estados

            # Si todos los caminos murieron, no tiene sentido seguir
            if not estados_activos:
                break

        # Verificar aceptación: Sfinal ∩ F ≠ ∅
        estados_finales_activos = estados_activos & self.defn.estados_finales
        acepta = len(estados_finales_activos) > 0

        traza.append(PasoTraza(
            simbolo=None,
            estados_activos=frozenset(estados_activos),
            es_fin=True,
            nota="ACEPTA" if acepta else "RECHAZA"
        ))

        return ResultadoSimulacion(
            cadena=cadena, acepta=acepta, traza=traza,
            estados_finales_activos=estados_finales_activos,
            tipo_automata="AFN"
        )
"""
Paquete automata_simulator
==========================
Motor genérico de simulación de autómatas finitos (AFD y AFN).

Módulos:
    parser     → AutomataParser, AutomataDefinition
    engine     → SimulationEngine, ResultadoSimulacion
    visualizer → TraceVisualizer, AutomataVisualizer
"""

from automata.parser import AutomataParser, AutomataDefinition, AutomataParserError
from automata.engine import SimulationEngine, ResultadoSimulacion
from automata.visualizer import TraceVisualizer, AutomataVisualizer

__all__ = [
    "AutomataParser",
    "AutomataDefinition",
    "AutomataParserError",
    "SimulationEngine",
    "ResultadoSimulacion",
    "TraceVisualizer",
    "AutomataVisualizer",
]
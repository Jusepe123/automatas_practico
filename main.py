"""
main.py — Punto de entrada del Motor Genérico de Simulación de Autómatas
=========================================================================
Uso:
    python main.py <archivo_json> <cadena1> [cadena2 ...]
    python main.py <archivo_json> --batch
    python main.py <archivo_json> --diagrama

Ejemplos:
    python main.py examples/afn_ejemplo.json 0110 101 111
    python main.py examples/afn_ejemplo.json --batch
    python main.py examples/afn_ejemplo.json --diagrama
"""

import sys
import os

# Asegurar que el paquete 'automata' sea importable desde este directorio
sys.path.insert(0, os.path.dirname(__file__))

from automata import (
    AutomataParser, AutomataParserError,
    SimulationEngine,
    TraceVisualizer, AutomataVisualizer,
)


def simular_cadena(engine: SimulationEngine, cadena: str) -> None:
    """Simula una cadena y muestra la traza."""
    resultado = engine.simular(cadena)
    TraceVisualizer.mostrar_traza(resultado)


def modo_batch(engine: SimulationEngine, cadenas: list) -> None:
    """Simula múltiples cadenas y muestra resumen."""
    resultados = []
    for cadena in cadenas:
        print()
        resultado = engine.simular(cadena)
        TraceVisualizer.mostrar_traza(resultado)
        resultados.append(resultado)

    print("\n")
    TraceVisualizer.mostrar_resumen_batch(resultados)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    archivo_json = sys.argv[1]

    # Cargar y validar el autómata
    try:
        defn = AutomataParser.desde_archivo(archivo_json)
    except AutomataParserError as e:
        print(f"\n[ERROR DE CONFIGURACIÓN] {e}\n")
        sys.exit(1)

    print(f"\n  Autómata cargado: tipo={defn.tipo} | "
          f"estados={sorted(defn.estados)} | "
          f"alfabeto={sorted(defn.alfabeto)}")

    engine = SimulationEngine(defn)

    # Modo diagrama
    if "--diagrama" in sys.argv:
        ruta = AutomataVisualizer.generar_diagrama(
            defn,
            nombre_archivo=os.path.splitext(os.path.basename(archivo_json))[0],
            directorio_salida="output"
        )
        if ruta:
            print(f"\n  Diagrama generado: {ruta}\n")

    # Modo batch (cadenas predefinidas de ejemplo)
    elif "--batch" in sys.argv:
        cadenas_batch = ["0110", "101", "1001", "111", "", "0", "1", "110", "010", "11"]
        modo_batch(engine, cadenas_batch)

    # Modo cadenas individuales
    elif len(sys.argv) >= 3:
        cadenas = sys.argv[2:]
        for cadena in cadenas:
            cadena_real = "" if cadena == "lambda" else cadena
            simular_cadena(engine, cadena_real)

    else:
        print("\nIndica al menos una cadena a simular, o usa --batch / --diagrama\n")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
"""
TraceVisualizer
===============
Capa de Output: responsable del formateo estético de las trazas
en tiempo de ejecución y de la generación del diagrama gráfico
del autómata usando graphviz.
"""

from typing import Optional
from automata.engine import ResultadoSimulacion, PasoTraza
from automata.parser import AutomataDefinition


class TraceVisualizer:
    """Formatea y muestra la traza de simulación en consola."""

    # Caracteres de formato
    SEP = "─" * 60
    SEP_DOBLE = "═" * 60

    @classmethod
    def mostrar_traza(cls, resultado: ResultadoSimulacion) -> str:
        """
        Genera la traza completa como string y la imprime en consola.
        Retorna el string para poder capturarlo en tests o archivos.
        """
        lineas = []

        lineas.append(cls.SEP_DOBLE)
        cadena_display = f'"{resultado.cadena}"' if resultado.cadena else '"λ" (cadena vacía)'
        lineas.append(f"  Simulación {resultado.tipo_automata} | Cadena: {cadena_display}")
        lineas.append(cls.SEP_DOBLE)

        for paso in resultado.traza:
            lineas.append(cls._formatear_paso(paso, resultado.tipo_automata))

        lineas.append(cls.SEP)
        # Resultado final destacado
        simbolo_res = "✓ ACEPTA" if resultado.acepta else "✗ RECHAZA"
        lineas.append(f"  RESULTADO FINAL: {simbolo_res}")
        lineas.append(cls.SEP_DOBLE)

        salida = "\n".join(lineas)
        print(salida)
        return salida

    @classmethod
    def _formatear_paso(cls, paso: PasoTraza, tipo: str) -> str:
        """Formatea un paso individual de la traza."""
        estados_str = cls._set_a_str(paso.estados_activos)

        if paso.es_inicio:
            linea = f"  [Inicio]   Estados activos: {estados_str}"
        elif paso.es_fin:
            linea = f"  [Fin]      Estados activos: {estados_str}"
        else:
            linea = f"  [Lee '{paso.simbolo}'] Estados activos: {estados_str}"

        # Agregar nota si existe
        if paso.nota and not paso.es_fin:
            linea += f"  ← {paso.nota}"

        return linea

    @staticmethod
    def _set_a_str(estados) -> str:
        """Convierte un set de estados a string ordenado: {q0, q1}"""
        if not estados:
            return "{∅}"
        return "{" + ", ".join(sorted(estados)) + "}"

    @classmethod
    def mostrar_resumen_batch(cls, resultados: list) -> None:
        """Muestra un resumen tabular de múltiples simulaciones."""
        print(cls.SEP_DOBLE)
        print("  RESUMEN DE LOTE")
        print(cls.SEP_DOBLE)
        print(f"  {'Cadena':<20} {'Resultado':<12} {'Estados finales activos'}")
        print(cls.SEP)
        for r in resultados:
            cadena_display = r.cadena if r.cadena else "λ"
            resultado_str = "ACEPTA ✓" if r.acepta else "RECHAZA ✗"
            estados_str = TraceVisualizer._set_a_str(r.estados_finales_activos)
            print(f"  {cadena_display:<20} {resultado_str:<12} {estados_str}")
        print(cls.SEP_DOBLE)


# ---------------------------------------------------------------
# AutomataVisualizer: genera el diagrama gráfico con graphviz
# ---------------------------------------------------------------
try:
    import graphviz
    GRAPHVIZ_DISPONIBLE = True
except ImportError:
    GRAPHVIZ_DISPONIBLE = False


class AutomataVisualizer:
    """
    Genera un diagrama gráfico del autómata usando graphviz.
    El gráfico se guarda como PNG (y PDF/SVG opcional) en el directorio
    especificado.
    """

    @staticmethod
    def generar_diagrama(
        defn: AutomataDefinition,
        nombre_archivo: str = "automata",
        directorio_salida: str = "output",
        formato: str = "png"
    ) -> Optional[str]:
        """
        Genera el diagrama del autómata y lo guarda en disco.

        Parámetros:
            defn: AutomataDefinition con la quíntupla del autómata.
            nombre_archivo: nombre base del archivo (sin extensión).
            directorio_salida: carpeta donde se guarda el diagrama.
            formato: 'png', 'svg' o 'pdf'.

        Retorna:
            Ruta completa del archivo generado, o None si graphviz no está disponible.
        """
        if not GRAPHVIZ_DISPONIBLE:
            print("[AutomataVisualizer] graphviz no instalado. Instala con: pip install graphviz")
            return None

        dot = graphviz.Digraph(
            name=nombre_archivo,
            comment=f"Autómata {defn.tipo}",
            format=formato,
        )

        # Configuración global del grafo
        dot.attr(rankdir="LR", size="10,6", dpi="150")
        dot.attr("node", fontname="Helvetica", fontsize="12")

        # Nodo invisible de entrada (flecha al estado inicial)
        dot.node("__inicio__", shape="point", width="0.2")

        # Dibujar estados
        for estado in sorted(defn.estados):
            if estado in defn.estados_finales:
                # Estado final: doble círculo
                dot.node(estado, shape="doublecircle", style="filled",
                         fillcolor="#d4edda", color="#28a745")
            elif estado == defn.estado_inicial:
                # Estado inicial: círculo relleno azul claro
                dot.node(estado, shape="circle", style="filled",
                         fillcolor="#cce5ff", color="#004085")
            else:
                dot.node(estado, shape="circle", style="filled",
                         fillcolor="#f8f9fa", color="#495057")

        # Flecha al estado inicial
        dot.edge("__inicio__", defn.estado_inicial, label="")

        # Dibujar transiciones
        # Agrupar aristas: (origen, destino) → lista de símbolos
        aristas: dict = {}
        for estado_origen, mapa in defn.transiciones.items():
            for simbolo, destinos in mapa.items():
                for dest in destinos:
                    clave = (estado_origen, dest)
                    aristas.setdefault(clave, []).append(simbolo)

        for (origen, dest), simbolos in aristas.items():
            etiqueta = ", ".join(sorted(simbolos))
            dot.edge(origen, dest, label=etiqueta, fontsize="11")

        # Renderizar
        ruta_salida = f"{directorio_salida}/{nombre_archivo}"
        ruta_final = dot.render(filename=ruta_salida, cleanup=True)
        print(f"[AutomataVisualizer] Diagrama guardado en: {ruta_final}")
        return ruta_final
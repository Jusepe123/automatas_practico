"""
AutomataParser
==============
Capa de Parsing: responsable exclusivamente de validar estructuralmente
y cargar el archivo JSON de configuración del autómata.
"""

import json
from dataclasses import dataclass, field
from typing import Dict, List, Set


@dataclass
class AutomataDefinition:
    """Representa la quíntupla formal M = (Σ, Q, q0, F, ∆)."""
    tipo: str                                    # "AFD" o "AFN"
    alfabeto: Set[str]                           # Σ
    estados: Set[str]                            # Q
    estado_inicial: str                          # q0
    estados_finales: Set[str]                    # F
    transiciones: Dict[str, Dict[str, List[str]]] # ∆


class AutomataParserError(Exception):
    """Excepción personalizada para errores de parsing."""
    pass


class AutomataParser:
    """
    Carga y valida la quíntupla desde un archivo JSON.
    No realiza ninguna simulación; solo parsea y valida estructura.
    """

    CAMPOS_REQUERIDOS = {"tipo", "alfabeto", "estados", "estado_inicial",
                         "estados_finales", "transiciones"}
    TIPOS_VALIDOS = {"AFD", "AFN"}

    @classmethod
    def desde_archivo(cls, ruta: str) -> AutomataDefinition:
        """Carga el autómata desde un archivo JSON en disco."""
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                datos = json.load(f)
        except FileNotFoundError:
            raise AutomataParserError(f"Archivo no encontrado: '{ruta}'")
        except json.JSONDecodeError as e:
            raise AutomataParserError(f"JSON malformado en '{ruta}': {e}")

        return cls._validar_y_construir(datos)

    @classmethod
    def desde_dict(cls, datos: dict) -> AutomataDefinition:
        """Carga el autómata desde un diccionario Python (útil para tests)."""
        return cls._validar_y_construir(datos)

    @classmethod
    def _validar_y_construir(cls, datos: dict) -> AutomataDefinition:
        """Valida la estructura del diccionario y construye AutomataDefinition."""

        # 1. Verificar campos obligatorios
        faltantes = cls.CAMPOS_REQUERIDOS - set(datos.keys())
        if faltantes:
            raise AutomataParserError(
                f"Campos obligatorios faltantes en el JSON: {faltantes}"
            )

        # 2. Validar tipo
        tipo = str(datos["tipo"]).upper()
        if tipo not in cls.TIPOS_VALIDOS:
            raise AutomataParserError(
                f"Tipo '{tipo}' inválido. Se esperaba: {cls.TIPOS_VALIDOS}"
            )

        # 3. Validar que listas no estén vacías
        alfabeto = list(datos["alfabeto"])
        estados = list(datos["estados"])
        if not alfabeto:
            raise AutomataParserError("El alfabeto Σ no puede estar vacío.")
        if not estados:
            raise AutomataParserError("El conjunto de estados Q no puede estar vacío.")

        # 4. Validar estado inicial
        estado_inicial = str(datos["estado_inicial"])
        if estado_inicial not in estados:
            raise AutomataParserError(
                f"El estado inicial '{estado_inicial}' no pertenece a Q={estados}"
            )

        # 5. Validar estados finales
        estados_finales = list(datos["estados_finales"])
        for ef in estados_finales:
            if ef not in estados:
                raise AutomataParserError(
                    f"Estado final '{ef}' no pertenece a Q={estados}"
                )

        # 6. Validar transiciones
        transiciones = datos["transiciones"]
        if not isinstance(transiciones, dict):
            raise AutomataParserError("Las transiciones deben ser un objeto JSON.")

        for estado_origen, mapa_simbolos in transiciones.items():
            if estado_origen not in estados:
                raise AutomataParserError(
                    f"Transición definida para estado desconocido: '{estado_origen}'"
                )
            if not isinstance(mapa_simbolos, dict):
                raise AutomataParserError(
                    f"Las transiciones de '{estado_origen}' deben ser un objeto JSON."
                )
            for simbolo, destinos in mapa_simbolos.items():
                if simbolo not in alfabeto:
                    raise AutomataParserError(
                        f"Símbolo '{simbolo}' en transiciones de '{estado_origen}' "
                        f"no pertenece al alfabeto Σ={alfabeto}"
                    )
                if not isinstance(destinos, list):
                    raise AutomataParserError(
                        f"Destinos de ({estado_origen}, {simbolo}) deben ser una lista."
                    )
                for dest in destinos:
                    if dest not in estados:
                        raise AutomataParserError(
                            f"Estado destino '{dest}' en ({estado_origen}, {simbolo}) "
                            f"no pertenece a Q={estados}"
                        )

        return AutomataDefinition(
            tipo=tipo,
            alfabeto=set(alfabeto),
            estados=set(estados),
            estado_inicial=estado_inicial,
            estados_finales=set(estados_finales),
            transiciones=transiciones,
        )
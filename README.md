# Motor Genérico de Simulación de Autómatas (AFD y AFN)

> Práctica de Programación Avanzada — Autómatas y Calculabilidad  
> Universidad Privada Boliviana · Facultad de Ingeniería y Arquitectura

Simulador **data-driven** de autómatas finitos: lee la definición formal de cualquier autómata desde un archivo JSON y ejecuta cadenas de prueba mostrando la traza de estados activos en tiempo real.

---

## Características

- Simula **AFD** (Autómata Finito Determinista) y **AFN** (Autómata Finito No Determinista)
- Completamente guiado por datos: ningún autómata está hardcodeado
- Traza paso a paso de estados activos con detección de bifurcaciones y caminos muertos
- Generación de **diagrama gráfico PNG** del autómata (via Graphviz)
- Arquitectura limpia en 3 capas: Parser → Engine → Visualizer
- Suite de **47 tests unitarios** automatizados con pytest

---

## Estructura del proyecto

```
automata_simulator/
│
├── main.py                      # Punto de entrada (CLI)
│
├── automata/                    # Paquete principal — 3 capas
│   ├── __init__.py
│   ├── parser.py                # Capa 1: AutomataParser  — carga y valida el JSON
│   ├── engine.py                # Capa 2: SimulationEngine — algoritmo de transiciones
│   └── visualizer.py           # Capa 3: TraceVisualizer + AutomataVisualizer
│
├── tests/
│   └── test_simulador.py        # 47 tests unitarios (pytest)
│
├── examples/
│   ├── afn_ejemplo.json         # AFN: acepta cadenas que contienen '101'
│   ├── afd_termina_01.json      # AFD: acepta cadenas que terminan en '01'
│   └── automata_defectuoso.json # Para prueba de estrés con lógica errónea
│
└── output/                      # Diagramas PNG generados automáticamente
```

---

## Requisitos

- Python 3.10+
- Librería Python de Graphviz:
  ```bash
  pip install graphviz pytest
  ```
- Ejecutable Graphviz instalado en el sistema:
  - **Windows:** Descarga desde https://graphviz.org/download/ e instala marcando *"Add to PATH"*. Luego reinicia la terminal y verifica con `dot -version`.
  - **Linux:** `sudo apt install graphviz`
  - **macOS:** `brew install graphviz`

---

## Uso

### Simular una o varias cadenas

```bash
python main.py examples/afn_ejemplo.json 0110 101 111
```

### Simular la cadena vacía λ

```bash
python main.py examples/afn_ejemplo.json lambda
```

### Modo batch (lote de cadenas predefinidas)

```bash
python main.py examples/afn_ejemplo.json --batch
```

### Generar diagrama PNG del autómata

```bash
python main.py examples/afn_ejemplo.json --diagrama
```
El archivo PNG se guarda en `output/<nombre_json>.png`.

### Correr todos los tests

```bash
pytest tests/ -v
```

---

## Formato del archivo JSON

El simulador acepta cualquier autómata que siga esta estructura (quíntupla formal M = (Σ, Q, q₀, F, ∆)):

```json
{
  "tipo": "AFN",
  "alfabeto": ["0", "1"],
  "estados": ["q0", "q1", "q2", "q3"],
  "estado_inicial": "q0",
  "estados_finales": ["q3"],
  "transiciones": {
    "q0": { "0": ["q0"], "1": ["q0", "q1"] },
    "q1": { "0": ["q2"], "1": [] },
    "q2": { "0": [],     "1": ["q3"] },
    "q3": { "0": ["q3"], "1": ["q3"] }
  }
}
```

- `"tipo"` puede ser `"AFD"` o `"AFN"`
- En **AFD**, cada lista de destinos debe tener exactamente un elemento
- En **AFN**, una lista vacía `[]` significa que ese camino muere (sin abortar la simulación)
- Puedes usar cualquier nombre de estados y cualquier alfabeto

---

## Ejemplo de traza

```
════════════════════════════════════════════════════════════
  Simulación AFN | Cadena: "0110"
════════════════════════════════════════════════════════════
  [Inicio]   Estados activos: {q0}
  [Lee '0'] Estados activos: {q0}
  [Lee '1'] Estados activos: {q0, q1}  ← Bifurcación detectada
  [Lee '1'] Estados activos: {q0, q1}  ← Bifurcación detectada; Camino(s) muerto(s) desde: {q1}
  [Lee '0'] Estados activos: {q0, q2}  ← Bifurcación detectada
  [Fin]      Estados activos: {q0, q2}
────────────────────────────────────────────────────────────
  RESULTADO FINAL: ✗ RECHAZA
════════════════════════════════════════════════════════════
```

---

## Arquitectura del código

### `automata/parser.py` — AutomataParser

Responsabilidad única: **cargar y validar** el archivo JSON.

- `AutomataParser.desde_archivo(ruta)` — carga desde disco
- `AutomataParser.desde_dict(datos)` — carga desde diccionario Python (útil en tests)
- Valida: campos obligatorios, tipo válido, estado inicial en Q, estados finales en Q, símbolos en Σ, estados destino en Q
- Lanza `AutomataParserError` con mensajes descriptivos ante cualquier inconsistencia
- Retorna un objeto `AutomataDefinition` con la quíntupla tipada

### `automata/engine.py` — SimulationEngine

Responsabilidad única: **ejecutar el algoritmo** de transiciones.

- `SimulationEngine(definicion)` — recibe un `AutomataDefinition`
- `engine.simular(cadena)` — despacha a `_simular_afd` o `_simular_afn` según el tipo
- **Modo AFD:** un único estado activo; transición no definida → estado muerto (rechaza limpiamente)
- **Modo AFN:** Set de estados activos; aplica S' = ∪ ∆(q, a); lista vacía = camino muere, simulación continúa
- Retorna `ResultadoSimulacion` con la traza completa de `PasoTraza` y el resultado booleano

### `automata/visualizer.py` — TraceVisualizer + AutomataVisualizer

Responsabilidad única: **formatear y mostrar** resultados.

- `TraceVisualizer.mostrar_traza(resultado)` — imprime la traza en consola y la retorna como string
- `TraceVisualizer.mostrar_resumen_batch(resultados)` — tabla resumen de múltiples cadenas
- `AutomataVisualizer.generar_diagrama(defn, nombre, directorio, formato)` — genera el grafo visual usando Graphviz:
  - Nodo azul = estado inicial
  - Nodo verde con doble círculo = estado(s) final(es)
  - Nodo gris = estado normal
  - Las aristas se agrupan: si dos estados tienen múltiples transiciones entre sí, se muestran en una sola flecha etiquetada con `"0, 1"`

### `main.py` — CLI

Punto de entrada. Parsea argumentos, instancia las capas en orden y delega. No contiene lógica de negocio.

---

## Tests

```
tests/test_simulador.py  —  47 tests / 5 bloques

  TestAutomataParser            (8 tests)  — validaciones del JSON
  TestSimulationEngineAFN      (16 tests)  — 6 aceptadas, 6 rechazadas, 4 límite
  TestSimulationEngineAFD      (10 tests)  — 6 aceptadas, 6 rechazadas, 2 límite  (*)
  TestTraceVisualizer           (4 tests)  — formato de salida
  TestRobustezAutomataDefectuoso(3 tests)  — motor correcto con autómata erróneo
```
(*) El AFD tiene 10 porque dos tests de casos límite están en ese bloque.

Casos límite cubiertos: cadena vacía λ, longitud 1, símbolo fuera del alfabeto, lista de transición vacía que no aborta la simulación AFN, estado muerto en AFD.

---

## Dependencias

| Paquete     | Uso                                      |
|-------------|------------------------------------------|
| `graphviz`  | Generación de diagramas PNG del autómata |
| `pytest`    | Ejecución de la suite de tests           |

Ambas se instalan con: `pip install graphviz pytest`
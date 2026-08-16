# Turmitas — Evolución con Algoritmos Genéticos (Modo Batalla)

## Descripción

Simulador de **turmitas** (hormigas de Langton generalizadas) con una interfaz gráfica tkinter
y un **algoritmo genético** que evoluciona turmitas para **ganar en modo batalla** a otras
turmitas contrincantes.

Al usar la notación RL de longitud variable, el operador de mutación puede **insertar**,
**borrar** y **sustituir** elementos del cromosoma de forma aleatoria.

---

## Archivos

| Archivo               | Descripción |
|-----------------------|-------------|
| `turmite.py`          | Clases base: `Turmite` (autómata) y `World` (tablero toroidal) |
| `turmites.py`         | Aplicación GUI con tkinter para visualizar turmitas |
| `genetic_algorithm.py`| Algoritmo genético completo (selección, cruce, mutación variable) |
| `battle_fitness.py`   | **Fitness de batalla** + ejecución del AG (archivo principal) |

---

## Bugs corregidos

1. **`turmite.py` — Wrapping toroidal**: Los controles de frontera de `x` e `y` estaban
   encadenados con `elif`, impidiendo verificar `y` si `x` ya estaba fuera de rango.
   Separados en bloques `if/elif` independientes para cada eje.

2. **`turmite.py` — `build_colors`**: `random.randint(0, 256)` generaba valores fuera del
   rango válido para colores hex (0–255). Corregido a `random.randint(0, 255)`.

3. **`battle_fitness.py` — Fitness incorrecta (bug principal)**: La implementación original
   evaluaba **simetría visual** en lugar de **batalla**. Corregido para simular una batalla
   real durante N=100.000 iteraciones y calcular `acc[2] / (acc[1]+acc[2])` conforme al
   enunciado de la práctica.

4. **`genetic_algorithm.py` — `best_ever` perdía la última población**: la población
   creada al final de la última iteración solo se evaluaba en el bloque de "Top 10"
   pero no se comparaba con `best_ever`, por lo que `ga.run()` podía devolver un
   individuo peor que el mostrado en el top final. Corregido reevaluando y actualizando
   `best_ever` antes de imprimir el reporte.

---

## Optimizaciones

1. **`turmite.py` — `account()` vectorizado**: el doble bucle Python sobre 800×600
   píxeles se ha sustituido por `np.bincount(self.battle.ravel())`, ~100× más rápido
   (de ~300 ms a ~3 ms por llamada).

2. **`genetic_algorithm.py` — caché de fitness**: cada cromosoma evaluado se memoriza
   por su cadena RL. Con elitismo y semillas, los élites sobrevivirían cada generación
   y se reevaluarían en vano; la caché evita esas batallas redundantes y reporta
   `Cache: hits/popsize` en cada generación trazada.

---

## Instalación

```bash
pip install numpy Pillow
```

> En Linux, si falta tkinter: `sudo apt install python3-tk`

---

## Uso

### Visualizador GUI

```bash
python3 turmites.py
```

- Pegar uno o varios códigos RL (uno por línea) en el cuadro de texto
- Pulsar **LoadRL**
- Activar el checkbox **Battle** para modo batalla
- Escribir un límite de iteraciones (ej. `100000`) en el campo **Limit**
- Pulsar **Run**

Ejemplo para reproducir una batalla contra el primer enemigo:
```
FFRFFL
LRRRLLFFRR
```

### Algoritmo Genético (modo batalla)

```bash
python3 battle_fitness.py
```

Evoluciona turmitas que superan a los enemigos `FFRFFL` y `FBFR`.
Cada generación tarda ~15–20 s en hardware estándar
(60 individuos × 2 enemigos × ~0,14 s por batalla de 100.000 pasos),
es decir unos 20–25 min para las 80 generaciones por defecto.

---

## Función de Fitness

Conforme al enunciado de la práctica:

```python
def fitness(ch, enemy):
    w = World(800, 600)           # crea el mundo

    t = Turmite()
    t.build_turk(phenotype(enemy))
    w.add(t)                      # añade enemigo (índice 1 en account)

    t = Turmite()
    t.build_turk(phenotype(ch))
    w.add(t)                      # añade candidato (índice 2 en account)

    N = 100000
    for _ in range(N):
        w.step()

    acc = w.account()
    fit = acc[2] / (acc[1] + acc[2])   # fracción de píxeles del candidato
    return fit
```

Se usan dos variantes configurables:

| Función            | Estrategia |
|--------------------|------------|
| `fitness_vs_all`   | Media contra todos los enemigos (generalista) |
| `fitness_vs_worst` | Mínimo entre todos los enemigos (más conservador) |

---

## Operadores del AG

### Mutación (longitud variable)

| Tipo        | Operación                                        | Probabilidad      |
|-------------|--------------------------------------------------|-------------------|
| Sustitución | Reemplaza un gen por otro del alfabeto           | `pmut` por gen    |
| Inserción   | Inserta un gen aleatorio en posición aleatoria   | `pmut × 0.5`      |
| Borrado     | Elimina un gen en posición aleatoria             | `pmut × 0.5`      |

### Cruce (longitud variable)

Cruce de un punto con puntos de corte independientes en cada padre,
produciendo hijos de longitud variable respetando los límites `min_len` / `max_len`.

---

## Parámetros del AG

| Parámetro      | Valor   | Descripción |
|----------------|---------|-------------|
| `popsize`      | 60      | Tamaño de población |
| `generations`  | 80      | Número de generaciones |
| `pmut`         | 0.12    | Probabilidad de mutación por gen |
| `tournament_k` | 4       | Tamaño del torneo de selección |
| `chromsize`    | 8       | Tamaño inicial sugerido |
| `min_len`      | 2       | Longitud mínima del cromosoma |
| `max_len`      | 60      | Longitud máxima del cromosoma |
| `alphabet`     | L,R,F,B | Left, Right, Forward, Backwards |
| `type`         | variable| Cromosomas de longitud variable |

---

## Enemigos a batir

| Código   | Descripción              |
|----------|--------------------------|
| `FFRFFL` | La bestia de las batallas |
| `FBFR`   | Contrincante secundario   |

Un candidato **gana** si su `fitness > 0.5` (domina más de la mitad
del territorio disputado al final de la batalla).

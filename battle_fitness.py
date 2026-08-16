"""
Battle Fitness for Turmites — Algoritmos Genéticos

Objetivo: evolucionar con AGs máquinas de Turing gráficas (turmitas)
que ganen en modo batalla a otras turmitas contrincantes.

Enemigos a batir:
  - FFRFFL
  - FBFR

Fitness: simula una batalla durante N iteraciones y calcula la fracción
de píxeles dominados por el candidato respecto al total disputado.

  fit = acc[2] / (acc[1] + acc[2])

donde acc[1] = píxeles del enemigo, acc[2] = píxeles del candidato.
"""

from turmite import *
from genetic_algorithm import GeneticAlgorithm

import random



# Configuración de enemigos

ENEMIES = ['FFRFFL', 'FBFR']  # turmitas fijas contra las que se compite
N_ITERATIONS = 100000   # iteraciones por batalla (según el enunciado)



# Phenotype: lista de caracteres → cadena RL

def phenotype(ch):
    return ''.join(ch)  # cromosoma ['F','F','R'] → string "FFR"


def split(word):
    return [c for c in word]  # string "FFR" → cromosoma ['F','F','R']



# Fitness de batalla (conforme al enunciado)

def fitness(ch, enemy):
    """
    Simula una batalla entre el candidato y el enemigo durante N iteraciones.
    Devuelve la fracción de píxeles que domina el candidato.

    acc[0] = píxeles sin reclamar (fondo)
    acc[1] = píxeles del enemigo  (primer turmite añadido)
    acc[2] = píxeles del candidato (segundo turmite añadido)
    """
    w = World(800, 600)          # crea el mundo

    # Añade el enemigo primero (ocupa índice 1 en account())
    t = Turmite()
    t.build_turk(phenotype(enemy))
    w.add(t)

    # Añade el candidato (ocupa índice 2 en account())
    t = Turmite()
    candidate = phenotype(ch)
    t.build_turk(candidate)
    w.add(t)

    # Ejecuta N iteraciones
    for _ in range(N_ITERATIONS):
        w.step()

    # Calcula fitness: proporción de territorio del candidato
    acc = w.account()
    total = acc[1] + acc[2]
    if total == 0:
        return 0.0
    fit = acc[2] / total  # >0.5 = gana, <0.5 = pierde, =0.5 = empate
    return fit


def fitness_vs_all(ch):
    """
    Fitness media contra todos los enemigos definidos en ENEMIES.
    Permite evolucionar un campeón generalista.
    """
    scores = [fitness(ch, split(e)) for e in ENEMIES]
    return sum(scores) / len(scores)  # media: equilibra rendimiento contra todos


def fitness_vs_worst(ch):
    """
    Fitness mínima (peor caso) contra todos los enemigos.
    Estrategia más conservadora: asegura ganar a todos.
    """
    scores = [fitness(ch, split(e)) for e in ENEMIES]
    return min(scores)  # mínimo: obliga a no tener ningún punto débil



# Test de patrones conocidos

def test_known():
    # Evalúa patrones de referencia para tener una línea base antes de evolucionar
    print("Evaluando patrones conocidos en modo batalla:")
    print(f"{'Código':<25} {'vs FFRFFL':>10} {'vs FBFR':>10}")
    print("-" * 50)
    known = [
        'FFRFFL', 'FBFR', 'RLLR', 'RRLL',
        'LRRRRLLL', 'RLLRRLLRRR', 'LRRRRLLLLRRRRLLRRLLL',
    ]
    for code in known:
        ch = split(code)
        f1 = fitness(ch, split('FFRFFL'))
        f2 = fitness(ch, split('FBFR'))
        marker = " ← ENEMIGO" if code in ('FFRFFL', 'FBFR') else ""
        print(f"  {code:<23} {f1:>10.4f} {f2:>10.4f}{marker}")
    print()



# Main: ejecuta el Algoritmo Genético

if __name__ == '__main__':

    # Evalúa patrones de referencia antes de evolucionar
    test_known()


    # Parámetros del AG
 
    parameters = {
        'alphabet':    ['L', 'R', 'F', 'B'],  # notación RL
        'type':        'variable',   # cromosomas de longitud variable
        'elitism':     True,         # conserva los mejores individuos
        'norm':        True,         # normaliza fitness para selección
        'chromsize':   8,            # tamaño inicial de cromosoma
        'min_len':     2,            # longitud mínima
        'max_len':     60,           # longitud máxima
        'pmut':        0.12,         # probabilidad de mutación por gen
        'trace':       5,            # imprimir cada N generaciones
        'popsize':     60,           # tamaño de población
        'unique':      True,         # individuos únicos en la población
        'tournament_k': 4,           # tamaño del torneo de selección
    }

  
    # Elige la función de fitness:
    #   - fitness_vs_all   → media contra todos los enemigos
    #   - fitness_vs_worst → mínimo (más difícil pero más robusto)
   
    FITNESS_FN = fitness_vs_all  # cambiar a fitness_vs_worst para estrategia conservadora

    ga = GeneticAlgorithm(FITNESS_FN, parameters)
    GENERATIONS = 80

    # Semillas con patrones conocidos para arrancar la evolución
    # Incluir los propios enemigos ayuda al AG a aprender cómo batirlos
    seeds = [
        'RLLR', 'RRLL', 'LRRRRLLL', 'RLLRRLLRRR',
        'FFRFFL', 'FBFR', 'FFRRFFL', 'FFRFFRL',
        'LRRRRLLLL', 'RLLRRLLRR', 'FFLRRFFL',
    ]
    ga.seed_population = [split(s) for s in seeds]

    print(f"Objetivo: superar a {ENEMIES}")
    print(f"Fitness: media de victorias en batalla ({N_ITERATIONS} pasos por batalla)")
    print(f"Corriendo AG — {GENERATIONS} generaciones × {parameters['popsize']} individuos\n")

    best_ch, best_fit = ga.run(generations=GENERATIONS)


    # Resultados finales

    best_rl = ''.join(best_ch)
    print(f"\n{'='*60}")
    print(f"MEJOR TURMITA EVOLUCIONADA")
    print(f"{'='*60}")
    print(f"Código RL : {best_rl}")
    print(f"Longitud  : {len(best_ch)}")
    print(f"Fitness   : {best_fit:.4f}")
    print(f"\nResultados individuales:")
    for enemy in ENEMIES:
        f = fitness(best_ch, split(enemy))
        result = "GANA ✓" if f > 0.5 else "PIERDE ✗"
        print(f"  vs {enemy:<12} → {f:.4f}  {result}")

    print(f"\nPara visualizar en la GUI:")
    print(f"  python3 turmites.py")
    print(f"  → Pegar en el cuadro: {best_rl}")
    print(f"  → Pulsar LoadRL → activar Battle → Run")
# Genetic Turmites Battle

An evolutionary simulation of **turmites — generalized Langton's ants — trained with a genetic algorithm to compete for territory in a shared environment**.

The project combines artificial life, cellular automata, evolutionary computation, and visualization through a Tkinter-based graphical interface.

Turmites are represented by variable-length rule sequences and evolved using selection, crossover, mutation, elitism, and battle-based fitness evaluation.

---

## Overview

A turmite is a generalized version of Langton's Ant: an autonomous agent that moves across a grid, reads the current cell state, modifies it, changes direction, and continues moving according to a transition rule.

In this project, turmites are encoded using strings composed of:

```text
L = Turn left
R = Turn right
F = Move forward
B = Turn backwards
```

Example:

```text
FFRFFL
```

Instead of manually designing the best rule sequence, a **genetic algorithm** evolves new turmites automatically.

The objective is to discover agents capable of defeating predefined opponents in a territorial battle.

---

## Battle Mode

Multiple turmites operate simultaneously on the same board.

Each cell records which turmite was the last one to occupy it.

After a fixed number of simulation steps, the fitness of the candidate is calculated according to the fraction of contested territory it controls.

For a candidate and one opponent:

```python
fitness = candidate_pixels / (enemy_pixels + candidate_pixels)
```

Therefore:

```text
fitness > 0.5  → candidate wins
fitness = 0.5  → draw
fitness < 0.5  → candidate loses
```

Each battle is simulated for:

```text
100,000 iterations
```

on a world of:

```text
800 × 600 cells
```

---

## Target Opponents

The genetic algorithm attempts to evolve turmites capable of defeating the following predefined opponents:

```text
FFRFFL
FBFR
```

Two fitness strategies are available.

### Average Fitness

```python
fitness_vs_all()
```

Calculates the average score against all opponents.

This encourages the evolution of general-purpose competitors.

### Worst-Case Fitness

```python
fitness_vs_worst()
```

Uses the lowest score achieved against any opponent.

This creates a more conservative optimization objective and encourages candidates without a weak matchup.

---

## Genetic Algorithm

The evolutionary algorithm is implemented in:

```text
genetic_algorithm.py
```

It supports:

* Tournament selection
* Elitism
* One-point crossover
* Variable-length chromosomes
* Gene substitution
* Gene insertion
* Gene deletion
* Unique individuals
* Fitness normalization
* Fitness caching
* Seed populations
* Early stopping

---

## Variable-Length Chromosomes

Each chromosome represents a turmite rule.

Example:

```text
['F', 'F', 'R', 'F', 'F', 'L']
```

which corresponds to:

```text
FFRFFL
```

Unlike a fixed-size genetic representation, chromosomes can change length during evolution.

The allowed range is:

```text
Minimum length: 2
Maximum length: 60
```

This allows evolution to optimize both:

* The sequence of instructions
* The complexity of the rule itself

---

## Mutation

Three mutation mechanisms are implemented.

### Substitution

A gene is replaced by another instruction.

Example:

```text
FFRFFL
   ↓
FFLFFL
```

### Insertion

A new instruction is inserted at a random position.

Example:

```text
FFRFFL
   ↓
FFRRFFL
```

### Deletion

A randomly selected instruction is removed.

Example:

```text
FFRFFL
   ↓
FRFFL
```

The probability of mutation is controlled using:

```text
pmut = 0.12
```

---

## Crossover

The genetic algorithm uses one-point crossover with independent crossover points for both parents.

Example:

```text
Parent A: FFR | FFL
Parent B: LR | RRLL

Child:    FFR + RRLL
```

Because the parents can have different lengths, the resulting offspring can also have different lengths.

---

## Selection

Tournament selection is used to select parents.

The default tournament size is:

```text
4
```

Several individuals are sampled from the population and the strongest is selected as a parent.

---

## Elitism

The best individuals from each generation are preserved.

This prevents high-quality solutions from being lost due to crossover or mutation.

---

## Fitness Cache

Battle evaluation is the most computationally expensive part of the algorithm.

Since elite individuals may survive across multiple generations, evaluating the same chromosome repeatedly would waste computation.

A fitness cache stores previously evaluated chromosomes:

```text
RL rule → fitness
```

When a chromosome appears again, its stored result can be reused.

This substantially reduces unnecessary battle simulations.

---

## NumPy Optimization

The territorial accounting operation originally iterated through the entire:

```text
800 × 600
```

grid using Python loops.

It was optimized using:

```python
numpy.bincount()
```

The operation was reduced from approximately:

```text
~300 ms
```

to approximately:

```text
~3 ms
```

per call in the development environment.

This is particularly important because thousands of battles are performed during genetic evolution.

---

## Default Genetic Algorithm Configuration

| Parameter                 |        Value |
| ------------------------- | -----------: |
| Population size           |           60 |
| Generations               |           80 |
| Mutation probability      |         0.12 |
| Tournament size           |            4 |
| Initial chromosome size   |            8 |
| Minimum chromosome length |            2 |
| Maximum chromosome length |           60 |
| Chromosome type           |     Variable |
| Alphabet                  | `L, R, F, B` |
| Battle iterations         |      100,000 |

A complete experiment therefore involves a large number of simulation steps.

---

## Seed Population

The initial population can include known patterns such as:

```text
RLLR
RRLL
LRRRRLLL
RLLRRLLRRR
FFRFFL
FBFR
FFRRFFL
FFRFFRL
```

Including known competitors gives the evolutionary algorithm useful starting points while still allowing new strategies to emerge through mutation and crossover.

---

## Turmite Model

The main simulation logic is implemented in:

```text
turmite.py
```

It contains two principal classes.

### `Turmite`

Represents an individual generalized Langton's ant.

Each turmite maintains:

* Position
* Direction
* Internal state
* Transition table
* Rule sequence

### `World`

Represents the shared simulation environment.

It maintains:

* Grid state
* Battle ownership
* Active turmites
* Toroidal boundaries
* Visualization colors

---

## Toroidal World

The simulation uses a toroidal grid.

When a turmite leaves one side of the world, it reappears on the opposite side.

Conceptually:

```text
       top
        ↑
        │
left ← grid → right
        │
        ↓
      bottom
```

Crossing the right edge returns the agent to the left edge, and crossing the top returns it to the bottom.

---

## Graphical Interface

The project includes a Tkinter-based GUI:

```text
turmites.py
```

It allows users to:

* Enter one or more turmite rules
* Load custom RL sequences
* Visualize their movement
* Enable battle mode
* Define an iteration limit
* Run simulations interactively

To start the interface:

```bash
python3 turmites.py
```

Example battle:

```text
FFRFFL
LRRRLLFFRR
```

Enable:

```text
Battle
```

and run the simulation.

---

## Running the Genetic Algorithm

Run:

```bash
python3 battle_fitness.py
```

The script first evaluates several known reference patterns and then starts the evolutionary process.

During training it reports information such as:

```text
Generation
Best fitness
Average fitness
Worst fitness
Chromosome length
Execution time
Fitness-cache hits
Best rule
```

At the end, it displays the best turmite found.

Example output structure:

```text
BEST EVER
Fitness: 0.xxxx
Chromosome: ...
Length: ...
```

The final candidate is then evaluated independently against each predefined opponent.

---

## Project Structure

```text
genetic-turmites-battle/
│
├── turmite.py
├── turmites.py
├── genetic_algorithm.py
├── battle_fitness.py
│
├── best_evolved.png
├── complex_sym.png
├── icon.png
│
└── README.md
```

### `turmite.py`

Core turmite and world simulation.

### `turmites.py`

Tkinter graphical interface.

### `genetic_algorithm.py`

Generic genetic-algorithm implementation.

### `battle_fitness.py`

Battle fitness definition and main evolutionary experiment.

---

## Installation

Requires Python 3 and the following packages:

```bash
pip install numpy Pillow
```

Tkinter is normally included with Python on macOS and Windows.

On some Linux distributions:

```bash
sudo apt install python3-tk
```

---

## Usage

### Run the GUI

```bash
python3 turmites.py
```

### Run evolutionary training

```bash
python3 battle_fitness.py
```

---

## Implemented Improvements

Several issues in the original implementation were corrected.

### Toroidal Boundary Handling

Horizontal and vertical boundary checks were previously linked incorrectly.

They are now evaluated independently so both coordinates wrap correctly.

### Color Generation

Random RGB generation was corrected to use the valid range:

```text
0–255
```

### Battle Fitness

The fitness function now evaluates actual territorial competition instead of visual symmetry.

### Best Individual Tracking

The final generated population is evaluated before returning the global best individual, preventing a potentially superior final candidate from being ignored.

### Vectorized Territory Counting

Territory accounting uses NumPy vectorization instead of nested Python loops.

### Fitness Memoization

Previously evaluated chromosomes are cached to avoid redundant battle simulations.

---

## Concepts Demonstrated

This project explores concepts including:

* Genetic algorithms
* Evolutionary computation
* Artificial life
* Generalized Langton's ants
* Turmites
* Cellular automata
* Tournament selection
* Elitism
* Crossover
* Mutation
* Variable-length chromosomes
* Fitness functions
* Evolutionary optimization
* Simulation
* NumPy vectorization
* Memoization
* Graphical visualization

---

## Possible Extensions

Future improvements could include:

* Parallel evaluation of individuals
* Multiprocessing battle simulations
* Adaptive mutation rates
* Multi-objective fitness
* Co-evolution of opponents
* Larger opponent populations
* Tournament-based evolutionary fitness
* Diversity preservation
* Fitness-history visualization
* Checkpointing evolutionary runs
* GPU-based simulation
* Automatic export of evolved turmite patterns

---

## Academic Context

This project was developed as an educational exercise in **genetic algorithms and evolutionary computation**.

The objective is to explore how evolutionary search can automatically discover behavioral rules for autonomous agents competing in a simulated environment.

---

## License

See the repository license for applicable terms.


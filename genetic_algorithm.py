"""
Genetic Algorithm for evolving turmites with variable-length chromosomes.
Supports: tournament selection, elitism, normalization, variable/classic modes.
"""

import random
import copy
import time


def split(word):
	"""Convert string to list of characters."""
	return [char for char in word]


class GeneticAlgorithm:
	def __init__(self, fitness_func, parameters):
		self.fitness_func = fitness_func
		self.alphabet = parameters.get('alphabet', ['L', 'R'])
		self.chrom_type = parameters.get('type', 'variable')  # 'variable' o 'classic' (longitud fija)
		self.elitism = parameters.get('elitism', True)
		self.normalize = parameters.get('norm', True)
		self.chromsize = parameters.get('chromsize', 4)
		self.pmut = parameters.get('pmut', 0.2)
		self.trace = parameters.get('trace', 10)
		self.popsize = parameters.get('popsize', 50)
		self.unique = parameters.get('unique', True)
		self.max_len = parameters.get('max_len', 150)
		self.min_len = parameters.get('min_len', 2)
		self.tournament_k = parameters.get('tournament_k', 3)

		# Estadísticas de evolución
		self.best_fitness_history = []
		self.avg_fitness_history = []
		self.seed_population = []  # semillas opcionales

		# Caché de fitness: evita reevaluar cromosomas ya conocidos.
		# Con elitismo + unique=True, los élites sobreviven sin cambios y se
		# reevaluarían cada generación; la caché ahorra batallas costosas.
		self.fitness_cache = {}
		self.cache_hits = 0

	def random_chromosome(self):
		"""Generate a random chromosome."""
		if self.chrom_type == 'classic':
			size = self.chromsize  # longitud fija
		else:
			size = random.randint(self.min_len, max(self.min_len, self.chromsize * 3))  # longitud aleatoria hasta 3× chromsize
		return [random.choice(self.alphabet) for _ in range(size)]

	def init_population(self):
		"""Initialize population with random chromosomes + optional seeds."""
		population = []
		seen = set()  # evita duplicados si unique=True

		# Añadir semillas primero
		for ch in self.seed_population:
			key = ''.join(ch)
			if key not in seen:
				population.append(list(ch))
				seen.add(key)

		attempts = 0
		while len(population) < self.popsize and attempts < self.popsize * 10:
			ch = self.random_chromosome()
			key = ''.join(ch)
			if self.unique and key in seen:
				attempts += 1
				continue
			seen.add(key)
			population.append(ch)
			attempts = 0
		return population

	def evaluate(self, population):
		"""Evaluate fitness of all individuals. Returns list of (chromosome, fitness)."""
		evaluated = []
		for ch in population:
			key = ''.join(ch)
			if key in self.fitness_cache:
				fit = self.fitness_cache[key]
				self.cache_hits += 1
			else:
				fit = self.fitness_func(ch)  # función de fitness externa (batalla)
				self.fitness_cache[key] = fit
			evaluated.append((ch, fit))
		return evaluated

	def normalize_fitness(self, evaluated):
		"""Normalize fitness values to [0, 1] range."""
		fits = [f for _, f in evaluated]
		fmin = min(fits)
		fmax = max(fits)
		if fmax - fmin < 1e-10:
			return [(ch, 1.0) for ch, _ in evaluated]  # todos iguales → todos a 1
		return [(ch, (f - fmin) / (fmax - fmin)) for ch, f in evaluated]  # escala lineal

	def tournament_selection(self, evaluated):
		"""Tournament selection: pick k random, return the best."""
		# Coge k individuos al azar y devuelve el de mayor fitness
		# Mayor k = más presión selectiva (favorece a los mejores más agresivamente)
		candidates = random.sample(evaluated, min(self.tournament_k, len(evaluated)))
		return max(candidates, key=lambda x: x[1])[0]

	def roulette_selection(self, evaluated):
		"""Roulette wheel selection."""
		# Alternativa al torneo: probabilidad proporcional al fitness
		# No se usa en el main (se usa tournament), pero está disponible
		total = sum(f for _, f in evaluated)
		if total < 1e-10:
			return random.choice(evaluated)[0]
		r = random.uniform(0, total)
		cumsum = 0
		for ch, f in evaluated:
			cumsum += f
			if cumsum >= r:
				return ch
		return evaluated[-1][0]

	def crossover(self, parent1, parent2):
		"""Single-point crossover adapted for variable-length chromosomes."""
		if len(parent1) < 2 or len(parent2) < 2:
			return list(parent1), list(parent2)

		# Puntos de corte independientes en cada padre → hijos de longitud variable
		p1 = random.randint(1, len(parent1) - 1)
		p2 = random.randint(1, len(parent2) - 1)

		child1 = parent1[:p1] + parent2[p2:]
		child2 = parent2[:p2] + parent1[p1:]

		# Refuerza los límites de longitud
		child1 = child1[:self.max_len] if len(child1) > self.max_len else child1
		child2 = child2[:self.max_len] if len(child2) > self.max_len else child2

		if len(child1) < self.min_len:
			child1 = list(parent1)  # si el hijo es demasiado corto, se usa el padre
		if len(child2) < self.min_len:
			child2 = list(parent2)

		return child1, child2

	def mutate(self, chromosome):
		"""Apply mutations: point mutation, insertion, deletion."""
		ch = list(chromosome)

		# Point mutation: recorre gen a gen y sustituye con probabilidad pmut
		for i in range(len(ch)):
			if random.random() < self.pmut:
				ch[i] = random.choice(self.alphabet)

		# Insertion (for variable-length): inserta un gen aleatorio → alarga el cromosoma
		if self.chrom_type == 'variable' and random.random() < self.pmut * 0.5:
			if len(ch) < self.max_len:
				pos = random.randint(0, len(ch))
				ch.insert(pos, random.choice(self.alphabet))

		# Deletion (for variable-length): elimina un gen aleatorio → acorta el cromosoma
		if self.chrom_type == 'variable' and random.random() < self.pmut * 0.5:
			if len(ch) > self.min_len:
				pos = random.randint(0, len(ch) - 1)
				ch.pop(pos)

		return ch

	def next_generation(self, evaluated):
		"""Create next generation from evaluated population."""
		# Ordena descendientemente por fitness 
		evaluated.sort(key=lambda x: x[1], reverse=True)

		new_population = []
		seen = set()

		# Elitismo: mantiene ,os mejores indiciduos
		if self.elitism:
			n_elite = max(1, self.popsize // 20)  # top 5% pasa directamente sin modificarse
			for ch, f in evaluated[:n_elite]:
				key = ''.join(ch)
				if key not in seen:
					new_population.append(list(ch))
					seen.add(key)

		# Normalizar para selección.
		# Nota: con torneo (que solo usa el orden), la normalización es un no-op.
		# Solo afecta de verdad si se cambia a selección por ruleta.
		sel_eval = self.normalize_fitness(evaluated) if self.normalize else evaluated

		# Rellenar el resto con cruce + mutación
		attempts = 0
		while len(new_population) < self.popsize and attempts < self.popsize * 10:
			p1 = self.tournament_selection(sel_eval)
			p2 = self.tournament_selection(sel_eval)

			c1, c2 = self.crossover(p1, p2)  # cruce: combina genes de dos padres
			c1 = self.mutate(c1)              # mutación: introduce variación
			c2 = self.mutate(c2)

			for child in [c1, c2]:
				if len(new_population) >= self.popsize:
					break
				key = ''.join(child)
				if self.unique and key in seen:
					attempts += 1
					continue
				seen.add(key)
				new_population.append(child)
				attempts = 0

		# Si no podemos relledar por unicidad, añadiños random
		while len(new_population) < self.popsize:
			ch = self.random_chromosome()  # relleno con individuos aleatorios si no hay suficientes únicos
			key = ''.join(ch)
			if key not in seen:
				new_population.append(ch)
				seen.add(key)

		return new_population

	def run(self, generations=100):
		"""Run the genetic algorithm for a number of generations."""
		print(f"=== Genetic Algorithm ===")
		print(f"Population: {self.popsize} | Generations: {generations} | "
			  f"Mutation: {self.pmut} | Type: {self.chrom_type}")
		print(f"Alphabet: {self.alphabet}")
		print(f"{'='*60}")

		population = self.init_population()
		best_ever = None
		best_ever_fit = -1

		for gen in range(generations):
			t0 = time.time()
			hits_before = self.cache_hits
			evaluated = self.evaluate(population)  # evalúa toda la población (parte más costosa)
			gen_hits = self.cache_hits - hits_before  # batallas que nos hemos ahorrado en esta gen

			# Encontrar el mejor en la generación 
			evaluated.sort(key=lambda x: x[1], reverse=True)
			best_ch, best_fit = evaluated[0]
			avg_fit = sum(f for _, f in evaluated) / len(evaluated)
			worst_fit = evaluated[-1][1]

			self.best_fitness_history.append(best_fit)
			self.avg_fitness_history.append(avg_fit)

			
			if best_fit > best_ever_fit:
				best_ever = list(best_ch)  # guarda el mejor de toda la evolución, no solo de esta generación
				best_ever_fit = best_fit

			elapsed = time.time() - t0

			# Mostramos los resultados
			if gen % self.trace == 0 or gen == generations - 1:
				phenotype = ''.join(best_ch)
				print(f"Gen {gen:4d} | Best: {best_fit:.4f} | Avg: {avg_fit:.4f} | "
					  f"Worst: {worst_fit:.4f} | Len: {len(best_ch):3d} | "
					  f"Time: {elapsed:.1f}s | Cache: {gen_hits}/{self.popsize} | "
					  f"{phenotype[:60]}")

			# Early stopping si el fitness es perfecto
			if best_fit >= 0.99:
				print(f"\n*** Near-perfect fitness reached at generation {gen}! ***")
				break  # no tiene sentido seguir si ya domina el 99% del tablero

			# Crear la siguiente generación
			population = self.next_generation(evaluated)

		# Evaluamos la última población generada (la creada al final de la última
		# iteración nunca se evaluó dentro del bucle) y actualizamos best_ever
		# por si contiene un individuo mejor — si no, perderíamos el mejor real.
		evaluated = self.evaluate(population)
		evaluated.sort(key=lambda x: x[1], reverse=True)
		if evaluated[0][1] > best_ever_fit:
			best_ever = list(evaluated[0][0])
			best_ever_fit = evaluated[0][1]

		# Reporte final
		print(f"\n{'='*60}")
		print(f"BEST EVER: fitness = {best_ever_fit:.4f}")
		print(f"Chromosome: {''.join(best_ever)}")
		print(f"Length: {len(best_ever)}")
		print(f"{'='*60}")

		# Mostrar los top 10 resultados únicos
		print(f"\nTop 10 in final population:")
		for i, (ch, f) in enumerate(evaluated[:10]):
			print(f"  {i+1}. fit={f:.4f} len={len(ch):3d} {''.join(ch)[:80]}")

		return best_ever, best_ever_fit  # devuelve el mejor cromosoma encontrado en toda la evolución
import numpy as np
import random


class Turmite:
	"""Represents a single turmite (generalized Langton's ant)."""
	# Índices para leer los campos de la tupla de acción: (estado, color, acción)
	STATE = 0
	COLOR = 1
	ACTION = 2

	def set(self, table, x=None, y=None, head=2):
		self.x = x if x is not None else self.w // 2  # posición inicial: centro del tablero
		self.y = y if y is not None else self.h // 2
		self.head = head  # dirección: 0=sur, 1=oeste, 2=norte, 3=este
		self.state = 0
		self.table = table  # tabla de transición: (estado, color) → (estado, color, acción)

	def __init__(self, table={}, x=None, y=None, head=2, w=800, h=600):
		# table: (state, color) -> (state, color, action)
		self.w = w
		self.h = h
		self.set(table, x, y, head)

	def step(self, c):
		"""Do one step with color read c; return the new color to paint."""
		# If the turmite reads a color not in its table, treat as background (0)
		if (self.state, c) not in self.table:
			c = 0

		action = self.table[(self.state, c)]
		self.state = action[Turmite.STATE]
		self.head = (self.head + action[Turmite.ACTION]) % 4  # giro: suma mod 4 → 4 direcciones posibles

		# Update coordinates based on heading
		if self.head == 0:
			self.y += 1
		elif self.head == 1:
			self.x -= 1
		elif self.head == 2:
			self.y -= 1
		elif self.head == 3:
			self.x += 1

		# BUG FIX: Separate x and y toroidal wrapping (was elif chain)
		# Con elif, si x salía del borde no se comprobaba y → ahora son dos bloques independientes
		if self.x < 0:
			self.x = self.w - 1
		elif self.x >= self.w:
			self.x = 0

		if self.y < 0:
			self.y = self.h - 1
		elif self.y >= self.h:
			self.y = 0

		return action[Turmite.COLOR]  # nuevo color a pintar en el píxel actual

	def build_turk(self, RL):
		"""Build transition table from RL syntax string.
		L=left(90°), R=right(270°), F=forward(0°), B=backwards(180°)
		"""
		c = 0
		table = {}
		s = RL.strip().upper()
		for ch in s:
			if ch == 'R':
				action = 3
			elif ch == 'L':
				action = 1
			elif ch == 'F':
				action = 0
			elif ch == 'B':
				action = 2
			else:
				continue  # Skip invalid characters
			table[(0, c)] = (0, c + 1, action)  # al leer color c → pinta c+1 y gira según letra
			c += 1
		if c > 0:
			table[(0, c - 1)] = (0, 0, action)  # Last points back to first: el último color vuelve al 0 (ciclo)
		self.set(table)


def build_colors(until=256, seed=None):
	if seed:
		random.seed(seed)  # semilla fija → paleta reproducible entre ejecuciones
	res = []
	for i in range(until):
		# BUG FIX: was randint(0,256) → max valid is 255
		r = random.randint(0, 255)
		g = random.randint(0, 255)
		b = random.randint(0, 255)
		res.append(f"#{r:02x}{g:02x}{b:02x}")
	random.seed()  # resetea la semilla para no afectar al resto del programa
	return res


class World:
	"""Represents a list of turmites operating on the same board."""
	# Paleta de 256 colores: 8 nombrados + 248 aleatorios con semilla fija (reproducible)
	COLORS = ['black', 'white', 'red', 'green', 'blue', 'cyan', 'magenta', 'yellow']
	COLORS += build_colors(256 - 8, 3746)

	def __init__(self, w, h):
		self.w = w
		self.h = h
		self.x = w // 2
		self.y = h // 2
		self.reset()
		self.mode = 1  # 0: normal; 1: battle

	def clear(self):
		self.board  = np.zeros([self.w, self.h], dtype=np.uint8)  # color actual de cada píxel
		self.battle = np.zeros([self.w, self.h], dtype=np.uint8)  # índice de la turmita que pisó cada píxel por última vez

	def reset(self):
		self.clear()
		self.turmites = []

	def colorize(self):
		World.COLORS = build_colors(256)  # regenera la paleta con colores aleatorios nuevos

	def get_color(self, x, y):
		return self.board[x, y]

	def plot(self, img, x, y, c):
		img.put(c, (x, y))  # pinta un píxel directamente en el PhotoImage de tkinter

	def step(self, img=None):
		i = 1  # índice de turmita (1-based; 0 = fondo sin reclamar)
		for t in self.turmites:
			c = self.get_color(t.x, t.y)
			x = t.x
			y = t.y
			newc = t.step(c)        # avanza la turmita y obtiene el nuevo color a pintar
			self.board[x, y] = newc

			if img:
				if self.mode == 0:
					self.plot(img, x, y, self.COLORS[newc % len(self.COLORS)])  # modo normal: color real del píxel
				else:
					self.plot(img, x, y, self.COLORS[i % len(self.COLORS)])     # modo batalla: color de la turmita (para ver territorios)
			if self.mode == 1:
				self.battle[x, y] = i  # marca qué turmita domina este píxel
			i += 1

	def account(self):
		"""Account for territory of each turmite."""
		# acc[0]=fondo, acc[1]=turmita1, acc[2]=turmita2, ...
		# Vectorizado con np.bincount → ~100× más rápido que el doble bucle Python
		n = len(self.turmites) + 1
		counts = np.bincount(self.battle.ravel(), minlength=n)
		return counts[:n].tolist()

	def teleport(self):
		for t in self.turmites:
			t.x = random.randrange(0, t.w)  # recoloca cada turmita en posición aleatoria
			t.y = random.randrange(0, t.h)

	def add(self, t):
		self.turmites.append(t)
		n = len(self.turmites)
		if n > 2:
			self.teleport()  # con >2 turmitas: posiciones aleatorias para todas
		elif n > 1:
			# Con exactamente 2: posiciones simétricas a izquierda y derecha del centro
			self.turmites[0].x = self.w // 4
			self.turmites[0].y = self.h // 2
			self.turmites[0].head = 2
			self.turmites[1].x = self.w * 3 // 4
			self.turmites[1].y = self.h // 2
			self.turmites[1].head = 0

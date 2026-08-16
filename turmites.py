"""
Turmites GUI Application
Interactive visualization of turmites (generalized Langton's ant).
"""

from turmite import *  # importa Turmite, World y build_colors

from tkinter import *
import tkinter.messagebox
from tkinter.filedialog import asksaveasfilename

import threading  # permite correr la simulación sin congelar la GUI
from PIL import Image


# tkinter helper widgets 
# Funciones auxiliares que crean pares etiqueta+widget y devuelven la variable ligada

def create_info(frame, row, text):
	"""Create a pair: label + info label."""
	Label(frame, text=text).grid(row=row, column=0, sticky=E)
	variable = StringVar()
	variable.set('')
	obj = Label(frame, width=8, textvariable=variable)  # solo lectura (muestra iteraciones)
	obj.grid(row=row, column=1)
	return variable


def create_box(frame, row, text, value='', callback=None):
	"""Create a pair: label + Entry textfield."""
	Label(frame, text=text).grid(row=row, column=0, sticky=E)
	variable = StringVar()
	variable.set(value)
	obj = Entry(frame, width=20, textvariable=variable)  # editable (Limit, Result)
	if callback:
		obj.bind('<Key-Return>', callback)
	obj.grid(row=row, column=1)
	return variable


def create_check(frame, row, col, text, callback=None):
	"""Create a checkbutton."""
	variable = IntVar()
	obj = Checkbutton(frame, width=8, text=text, variable=variable, command=callback)  # checkbox Battle
	obj.grid(row=row, column=col)
	return variable


class Turmite_app(Frame):
	version = 'Turmites v0.4'

	def __init__(self, master):
		Frame.__init__(self)
		self.master = master
		self.master.title(self.version)
		self.grid(column=0, row=0, columnspan=5, rowspan=3)

		self.w = 800
		self.h = 600
		self.canvas = Canvas(self, bg='#000000', width=self.w - 5, height=self.h - 5)  # lienzo negro donde se dibuja
		self.canvas.grid(column=0, row=0, rowspan=20, sticky=(N, W, E, S))

		self.world = World(self.w, self.h)  # tablero toroidal que contiene las turmitas
		self.active = False  # controla si la simulación está corriendo
		self.ite = 0
		self.clear()

		# Control Panel 
		f1 = Frame(self, bd=3, relief=SUNKEN)
		Label(f1, text="Paste turmite code").grid(row=0, column=0, columnspan=2)
		self.code = Text(f1, height=8, width=30)  # cuadro donde se pega el código RL
		self.code.grid(row=2, column=0, columnspan=3)
		Button(f1, text='Load', width=10, command=self.load).grid(row=4, column=0)      # carga tabla Python explícita
		Button(f1, text='LoadRL', width=10, command=self.loadRL).grid(row=4, column=1)  # carga notación RL
		Button(f1, text='Reset', width=10, command=self.reset).grid(row=6, column=0)
		Button(f1, text='Clear', width=10, command=self.clear).grid(row=6, column=1)
		Button(f1, text='Save', width=10, command=self.save).grid(row=8, column=0)
		self.brun = Button(f1, text='Run', width=10, command=self.run)
		self.brun.grid(row=8, column=1)
		Button(f1, text='Teleport', width=10, command=self.world.teleport).grid(row=7, column=0)  # recoloca turmitas al azar
		Button(f1, text='Colorize', width=10, command=self.world.colorize).grid(row=7, column=1)  # regenera paleta de colores

		# Info Panel 
		f2 = Frame(self, bd=2, relief=SUNKEN)
		self.bite = create_info(f2, 0, 'Iterations')
		self.bite.set("0")
		self.usebattle = create_check(f2, 1, 0, "Battle")  # activa modo batalla (rastrea territorio)
		self.blimit = create_box(f2, 2, 'Limit')
		self.blimit.set('0')  # 0 = sin límite; cualquier otro valor para automáticamente al llegar
		self.res = create_box(f2, 4, 'Result')  # muestra ej: [45.2, 54.8] al terminar

		# Bottom
		f3 = Frame(self)
		Button(f3, text='Quit', width=10, command=self.quit).grid(row=0, column=1, sticky=SE)

		f1.grid(row=0, column=1)
		f2.grid(row=1, column=1)
		f3.grid(row=2, column=1, sticky=SE)
		self.master.bind('<<NewData>>', self.step)  # el hilo secundario dispara este evento para avanzar un paso

	def step(self, event):
		self.world.step(self.img)  # avanza 1 iteración y pinta el píxel cambiado en el canvas
		self.ite += 1
		if self.ite % 10000 == 0:
			self.update_battle()  # refresca porcentajes de territorio cada 10k pasos
		if self.ite % 1000 == 0:
			self.bite.set(f"{self.ite}")
			root.update_idletasks()
			if self.limit != 0 and self.ite >= self.limit:
				self.active = False  # para la simulación al alcanzar el límite

	def loop(self):
		# Corre en un hilo separado; genera eventos en lugar de llamar a tkinter directamente
		while self.active:
			root.event_generate('<<NewData>>', when='now')
		self.update_battle(end=True)  # muestra resultado final al terminar
		self.brun['text'] = 'Run'
		root.bell()

	def update_battle(self, end=False):
		if self.world.mode == 0:
			return  # solo opera en modo batalla
		acc = self.world.account()  # lista: [fondo, turmita1, turmita2, ...]
		acc = acc[1:]  # remove background
		total = sum(acc)
		if total == 0:
			return
		percent = [round(e / total * 100, 1) for e in acc]  # convierte píxeles a porcentajes
		self.res.set(f"{percent}")
		if end:
			print(acc)
			print(percent)

	def run(self):
		self.active = not self.active  # toggle: Run / Stop
		if self.active:
			self.res.set("")
			self.brun['text'] = 'Stop'
			self.world.mode = int(self.usebattle.get())  # 0=normal, 1=batalla
			self.limit = int(self.blimit.get())
			t = threading.Thread(target=self.loop, daemon=True)  # hilo demonio: muere si se cierra la app
			t.start()

	def reset(self):
		self.world.reset()
		self.clear()

	def save(self):
		name = asksaveasfilename(title='Image file', defaultextension='', filetypes=[])
		if not name:
			return
		import os
		name = os.path.splitext(name)[0]
		head, tail = os.path.split(name)
		tmp = os.path.join(head, 'tmp.eps')

		self.canvas.postscript(file=tmp)  # tkinter solo exporta a EPS nativamente

		img = Image.open(tmp)
		img.save(name + '.png', 'png')  # Pillow convierte EPS → PNG
		os.remove(tmp)

	def clear(self):
		self.ite = 0
		self.canvas.create_rectangle(0, 0, self.w, self.h, fill='black')
		self.img = PhotoImage(width=self.w, height=self.h)  # imagen en memoria donde world.step() pinta píxeles
		self.canvas.create_image((self.w / 2, self.h / 2), image=self.img)
		self.world.clear()
		root.bell()

	def load(self):
		# Carga una turmita desde una tabla de transición Python explícita
		# Formato: {(estado, color): (nuevo_estado, nuevo_color, acción)}
		self.clear()
		code = self.code.get('1.0', END)
		try:
			d = eval(code)
			t = Turmite(d)
			self.world.add(t)
		except Exception as e:
			tkinter.messagebox.showerror('Error', f'State table is wrong: {e}')

	def loadRL(self):
		# Carga turmitas desde notación RL, una por línea
		# Si se cargan >2, World.add() las teleporta a posiciones aleatorias
		self.clear()
		code = self.code.get('1.0', END)
		codes = code.strip().split('\n')
		for rl in codes:
			rl = rl.strip()
			if not rl:
				continue
			try:
				t = Turmite(w=self.w, h=self.h)
				t.build_turk(rl)  # convierte el string RL en tabla de transición
				print(f"Loaded: {rl} → {t.table}")
				self.world.add(t)
			except Exception as e:
				tkinter.messagebox.showerror('Error', f'State table is wrong: {e}')


if __name__ == '__main__':
	root = Tk()
	root.wm_resizable(0, 0)

	import os.path
	if os.path.exists('icon.png'):
		try:
			img = PhotoImage(file='icon.png')  # PhotoImage soporta PNG nativamente en tkinter
			root.tk.call('wm', 'iconphoto', root._w, img)
		except Exception:
			pass  # icono opcional, no es crítico

	bg = '#abd4c5'
	root.option_add('*Foreground', '#000000')
	root.option_add('*Background', bg)
	root.option_add('*Button*HighlightBackground', bg)
	root.option_add('*selectBackground', 'gold')
	root.option_add('*selectForeground', 'black')

	app = Turmite_app(root)
	root.mainloop()  # bucle principal de eventos de tkinter

'''
RL Codes Reference:
  RLR
  RLLR            # turmite clásico
  RRLL            # cerebro (simetría perfecta)
  LLLLRRRR        # cerebro2
  RRLLLRRL        # estrella de mar
  LLRRRLRLRLLR    # regalo
  RLLRRLLR        # turk coloreado
  RRLRR           # cuadrado
  FFRFFL          # la bestia de las batallas
  LLRLRLL         # triángulo
  LLRLRRLLL       # pirámide
  LRRRRLLLRRR     # espiral de Arquímedes

See: https://en.wikipedia.org/wiki/Langton%27s_ant
'''

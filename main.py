#!/usr/bin/python
# -*- coding: utf8 -*-

# Python & XSB Prolog Battleship
# ------------------------------
# Marin Rukavina <marin_at_shinyshell_dot_net>
# 22.10.2013

import wx
import pygame

# pyxf is a module by Markus Schatten for getting output from
# XSB (Prolog engine) in a Python-friendly format.
import pyxf as xf

import math
import os, sys
import re


class BattleshipGame:
	XSB_PATH = "/home/marin/Software/XSB/bin/xsb"
	hits = [[0 for x in xrange(10)] for y in xrange(10)]
	turns = 0
	lastsunk = None

	def __init__(self):
		self.xsb = xf.xsb(self.XSB_PATH)
		self.xsb.load('prolog/game.P')
		
		self.NewGame()
		
	def NewGame(self):
		self.xsb.query('start')

		self.turns = 0
		self.hits = [[0 for x in xrange(10)] for y in xrange(10)]
		self.lastsunk = None

	def Fire(self, position):
		self.turns += 1
		cell = BattleshipGame.GetDefinedPosition(position)
		
		status = self._TryFire(cell)
		if status != BattleshipHits.SUNK:
			self.hits[cell[0] - 1][cell[1] - 1] = status
		
		return status
		
	def _TryFire(self, position):
		# swap position to get Prolog coords
		coords = (position[1], position[0])

		res = self.xsb.query("gadjaj(%d, %d, Brod)" % coords)

		if not res:
			return BattleshipHits.MISS

		potopljen = self.xsb.query("potopljen(%s)" % res[0]["Brod"])
		
		if potopljen:
			self.lastsunk = res[0]["Brod"]
			ploca = self.xsb.query("ploca(P)")

			for i in xrange(1, 10):
				for j in xrange(1, 10):
					s = re.search("polje\(%d,%d,[a-z]+,([^\)]+)" % (j,i), ploca[0]["P"])
					if s is not None:
						if s.group(1) == res[0]["Brod"]:
							self.hits[i - 1][j - 1] = BattleshipHits.SUNK
			return BattleshipHits.SUNK
		return BattleshipHits.HIT

	def GameOver(self):
		pok = self.xsb.query("igragotova(BrojPokusaja)")
		if pok:
			return int(pok[0]["BrojPokusaja"])
		return False
		
	def IsUnknown(self, position):
		cell = BattleshipGame.GetDefinedPosition(position)
		if self.hits[cell[0] - 1][cell[1] - 1] is BattleshipHits.UNKNOWN:
			return True
		return False
		
	def GetHits(self):
		allhits = []
		
		for rowindex, row in enumerate(self.hits):
			for hitindex, hit in enumerate(row):
				if hit == 1:
					allhits += [(rowindex, hitindex)]
		
		return allhits
	
	@staticmethod
	def GetCellFromPosition(position):
		if position == None:
			return None
		return (ord(position[0]) - 64, position[1])
	
	@staticmethod
	def GetDefinedPosition(position):
		cell = position
		if (type(cell[0]) == str):
			cell = BattleshipGame.GetCellFromPosition(position)
		return cell

class BattleshipColors:
	paleblue = (180,205,232)
	darkblue = (145,180,217)
	blackish = (76,76,76)
	whiteish = (249, 251, 251)
	red = (210, 44, 0)
	
	def __init__(self):
		pass

class BattleshipHits:
	UNKNOWN = 0
	HIT = 1
	MISS = 2
	SUNK = 3
	
	def __init__(self):
		pass

class PygameDisplay(wx.Window):
	def __init__(self, parent, id, **options):
		wx.Window.__init__(self, parent, id, **options)
		self.parent = parent
		
		pygame.init()
		self.size = self.GetSizeTuple()
		self.size_dirty = True
	   
		self.timer = wx.Timer(self)
		self.Bind(wx.EVT_PAINT, self.OnPaint)
		self.Bind(wx.EVT_TIMER, self.Update, self.timer)
		self.Bind(wx.EVT_SIZE, self.OnSize)
		self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftClick)
	   
		self.fps = 60.0
		self.timespacing = 1000.0 / self.fps
		self.timer.Start(self.timespacing, False)
		
		self.linespacing = 5
		
		self.game = BattleshipGame()

	def Update(self, event):
		# Any update tasks would go here (moving sprites, advancing animation frames etc.)
		if (self.size_dirty):
			self.Redraw()
		
		pos = pygame.mouse.get_pos() 
		pressed = pygame.mouse.get_pressed()
		
		if not pressed:
			print (pos)
		
		self.Redraw()

	def Redraw(self):
		if self.size_dirty:
			#self.screen = pygame.image.load("battleship.png")
			#self.size_dirty = False
			self.screen = pygame.Surface(self.size, 0, 32)
			self.size_dirty = False
		
		self.screen.fill(BattleshipColors.darkblue)
		
		fieldinfo = self.GetMarginAndCellsize()
		
		for i in xrange(10):
			offset = fieldinfo['margin'] + i * fieldinfo['cellsize']
			
			pygame.draw.rect(
				self.screen,
				BattleshipColors.paleblue,
				pygame.Rect(
					(offset + i, fieldinfo['margin']),
					(fieldinfo['cellsize'], self.size[1])
					#(offset, margin),
					#(offset, self.size[1])
				)
			)
		
		verdanafont = pygame.font.Font("verdana.ttf", 16)
		
		for i in xrange(10):
			offset = fieldinfo['margin'] + i * fieldinfo['cellsize']
			
			letter = verdanafont.render(chr(65 + i), 1, BattleshipColors.blackish)
			number = verdanafont.render(str(i + 1), 1, BattleshipColors.blackish)
			self.screen.blit(letter, (12, offset + i + 4))
			self.screen.blit(number, (offset + i + 6, 6))
			
			pygame.draw.line(
				self.screen,
				BattleshipColors.blackish,
				(offset + i - 1, 0),
				(offset + i - 1, self.size[1])
			)
			pygame.draw.line(
				self.screen,
				BattleshipColors.blackish,
				(0, offset + i - 1),
				(self.size[0], offset + i - 1)
			)
		
		#hits = self.game.GetHits()
		for rowindex, row in enumerate(self.game.hits):
			for cellindex, cell in enumerate(row):
				if cell is not BattleshipHits.UNKNOWN:
					self.BlitDot((rowindex + 1, cellindex + 1), cell)
		
		
		s = pygame.image.tostring(self.screen, 'RGB')  # Convert the surface to an RGB string
		img = wx.ImageFromData(self.size[0], self.size[1], s)  # Load this string into a wx image
		bmp = wx.BitmapFromImage(img)  # Get the image in bitmap form
		dc = wx.ClientDC(self)  # Device context for drawing the bitmap
		dc.DrawBitmap(bmp, 0, 0, False)  # Blit the bitmap image to the display
		del dc
 
	def OnPaint(self, event):
		self.Redraw()
		event.Skip()  # Make sure the parent frame gets told to redraw as well
 
	def OnSize(self, event):
		self.size = self.GetSizeTuple()
		self.size_dirty = True
	
	def OnLeftClick(self, event):
		(x, y) = event.GetPositionTuple()
		field =  self.CalculateField(x,y)
		if field is not None and self.game.IsUnknown(field):
			hitType = self.game.Fire(field)
			
			if hitType == BattleshipHits.MISS:
				self.parent.AddToStatusBox(u"%s: Ništa nije pogođeno na %s%s." % (self.game.turns, field[0], field[1]))
			elif hitType == BattleshipHits.HIT:
				self.parent.AddToStatusBox(u"%s: Pogodak na %s%s!" % (self.game.turns, field[0], field[1]))
			elif hitType == BattleshipHits.SUNK:
				self.parent.AddToStatusBox(u"%s: Potopljen brod \"%s\" pogotkom na %s%s!" % (self.game.turns, self.game.lastsunk.capitalize(), field[0], field[1]))
			
			turnsWon = self.game.GameOver()
			if turnsWon:
				self.parent.AddToStatusBox(u"KRAJ: Pobijedili ste! Igra je završena u %d pokušaja!" % (turnsWon,))


	def CalculateField(self, x, y):
		fieldinfo = self.GetMarginAndCellsize()
		margin = math.floor(self.size[0] / 10)
		cellsize = math.floor((self.size[0] - margin) / 10)
		
		if x < fieldinfo['margin'] or y < fieldinfo['margin']:
			return None
		
		sx = x - fieldinfo['margin']
		sy = y - fieldinfo['margin']
		
		dx = math.floor(sx / fieldinfo['cellsize'])
		dy = math.floor(sy / fieldinfo['cellsize'])
		
		return (
			chr(65 + int(math.floor((sy - dy) / fieldinfo['cellsize']))),
			int(math.floor((sx - dx) / fieldinfo['cellsize']) + 1)
		)
	
	def BlitDot(self, cell, hitType):
		fieldinfo = self.GetMarginAndCellsize()
		
		if cell == None:
			return
		
		hitcell = (
			int(fieldinfo['margin'] + (fieldinfo['cellsize'] * (cell[1])) + cell[1]) - int(math.floor(fieldinfo['cellsize'] / 2)),
			int(fieldinfo['margin'] + (fieldinfo['cellsize'] * (cell[0])) + cell[0]) - int(math.floor(fieldinfo['cellsize'] / 2))
		)
		
		pygame.draw.circle(self.screen, BattleshipColors.blackish, hitcell, 7)
		
		if hitType is BattleshipHits.HIT:
			pygame.draw.circle(self.screen, BattleshipColors.red, hitcell, 6)
			
		elif hitType is BattleshipHits.MISS:
			pygame.draw.circle(self.screen, BattleshipColors.whiteish, hitcell, 6)
			
		elif hitType is BattleshipHits.SUNK:
			pygame.draw.circle(self.screen, BattleshipColors.blackish, hitcell, 6)
		
	def GetMarginAndCellsize(self):
		margin = math.floor(self.size[0] / 10)
		cellsize = math.floor((self.size[0] - margin) / 10)
		
		return { 'margin': margin, 'cellsize':cellsize }
	
	def Kill(self, event):
		# Make sure Pygame can't be asked to redraw /before/ quitting by unbinding all methods which
		# call the Redraw() method
		# (Otherwise wx seems to call Draw between quitting Pygame and destroying the frame)
		# This may or may not be necessary now that Pygame is just drawing to surfaces
		self.Unbind(event = wx.EVT_PAINT, handler = self.OnPaint)
		self.Unbind(event = wx.EVT_TIMER, handler = self.Update, source = self.timer)



class BattleshipWindow(wx.Frame):
	menu = {}
	menuitem = {}
	ime = None
	
	def __init__(self, parent, id, title = "Potapanje brodova", **options):
		options['style'] = (wx.DEFAULT_FRAME_STYLE | wx.TRANSPARENT_WINDOW) & (~wx.RESIZE_BORDER)
		wx.Frame.__init__( *(self, parent, id, title), **options)
		
		# bind events
		self.Bind(wx.EVT_CLOSE, self.Kill)
		
		# menubar
		self.menubar = wx.MenuBar()
		
		self.menu['game'] = wx.Menu()
		self.menu['player'] = wx.Menu()
		
		self.menuitem['newgame'] = self.menu['game'].Append(wx.NewId(), 'Nova igra', 'Započni novu igru')
		self.menuitem['quit'] = self.menu['game'].Append(wx.NewId(), 'Izađi', 'Izađi iz aplikacije')
		self.menuitem['changeuser'] = self.menu['player'].Append(wx.NewId(), 'Novi korisnik', 'Novi korisnik')
		self.menuitem['submitscore'] = self.menu['player'].Append(wx.NewId(), 'Pošalji rezultat na ljestvicu', 'Pošalji rezultat na ljestvicu')
		self.menuitem['viewleaderboard'] = self.menu['player'].Append(wx.NewId(), 'Posjeti ljestvicu', 'Posjeti ljestvicu')
		
		
		self.menubar.Append(self.menu['game'], '&Igra')
		self.menubar.Append(self.menu['player'], 'I&grač')
		
		# events
		self.Bind(wx.EVT_MENU, self.onNewGame,		self.menuitem["newgame"])
		self.Bind(wx.EVT_MENU, self.onExit,			self.menuitem["quit"])
		self.Bind(wx.EVT_MENU, self.onCreateUser,	self.menuitem["changeuser"])
		
		self.SetMenuBar(self.menubar)
		
		# pygame surface
		self.display = PygameDisplay(self, -1, size=(350,350))
		
		# other widgets
		self.line = wx.StaticLine(self)
		self.statusbox = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(350,130))
		
		#self.timer = wx.Timer(self)
		#self.timer.Start((1000.0 / self.display.fps))
		
		self.sizer = wx.BoxSizer(wx.VERTICAL)
		self.sizer.Add(self.display, 1, flag=wx.EXPAND)
		self.sizer.Add(self.line, 0, flag=wx.EXPAND | wx.ALL, border=10)
		self.sizer.Add(self.statusbox, 0, flag=wx.EXPAND)
		
		self.SetSizer(self.sizer)
		
	def AddToStatusBox(self, text):
		self.statusbox.AppendText("%s\n" % (text,))
	
	def Kill(self, event):
		self.display.Kill(event)
		self.Destroy()
	
	def onNewGame(self, event):
		self.display.game.NewGame()
		self.display.Redraw()
		self.statusbox.Clear()

	def onExit(self, event):
		self.Close()
		
	def onCreateUser(self, event):
		dlg = wx.TextEntryDialog(None, "Unesite ime:", "Novi korisnik", " ")
		answer = dlg.ShowModal()
	
		korisnikovoime = None
		if answer == wx.ID_OK:
			korisnikovoime = dlg.GetValue()
			print korisnikovoime
			
		dlg.Destroy()
		
		if korisnikovoime is not None:
			self.ime = korisnikovoime
			self.menubar.SetMenuLabel(1, korisnikovoime)

class MyApp(wx.App):
	def OnInit(self):
		frame = BattleshipWindow(None, -1, size=(350,500))
		frame.Show(True)
		return True

app = MyApp(0)
app.MainLoop()





























import sys
import re
import copy
import time

def match(text, regex):
	m = re.search("("+regex+")", text)
	if m:
		if m.group(1):
			return True
	return False
def tokenise(text):
	result = re.sub(r'\s+',r' ',text)
	result = re.sub(r'^\s*',r'',result)
	result = re.sub(r'\s*$',r'',result)
	return result.split(" ")


class MemorySegment():
	def __init__(self,name,size):
		self.name = name
		self.size = size
		self.data = [0]*size
	def write(self, address, data):
		if address < 0 and address > self.size-1:
			self.raiseError("Attempt to access non-existant memory")
		elif type(data) == list:
			if address + len(data) > self.size-1:
				self.raiseError("Attempt to write to beyond memory bounds")
			c = 0
			for i in range(address,address+len(data)):
				self.data[i] = int(data[c])
				c = c + 1
		else:
			self.data[address] = int(data)
	def read(self, address):
		if address >= 0 and address <= self.size-1:
			return self.data[address]
		else:
			self.raiseError("Attempt to access non-existant memory")
	def raiseError(self, msg):
		message = "[Memory Segment: "+self.name+"] "+msg
		raise ValueError(message)

class VM():
	# Initalise the VM
	# size will set up a initial segment of memory
	# maxCycles defines at how many cycles the vm will stop running
	#    set this as 1000 or something to allow a large amount of 
	#    code to run but to stop any infinite loops
	def __init__(self, size, maxCycles):
		self.memorySegments = {}
		self.memorySegments['main'] = MemorySegment('main', size)
		self.memory = self.memorySegments['main']
		self.maxCycles = maxCycles
		self.size = size
		self.code = []
		self.pc = 0
		self.finished = False
		self.functions = {}
		self.inDefinition = None
		self.numRegisters = 8
		self.registers = {
			'R0' : 0,
			'R1' : 0,
			'R2' : 0,
			'R3' : 0,
			'R4' : 0,
			'R5' : 0,
			'R6' : 0,
			'R7' : 0
		}
		self.cycles = 0
		self.skipCurr = False
		self.debug = False
	# Load in some code
	def loadCode(self, code):
		codeArray = code.split('\n')
		for line in codeArray:
			if not line or match(line, r'^\s*$'):
				continue
			tokens = tokenise(line)
			strArray = "['"+"','".join(tokens[1:])+"']"
			self.code.append("self."+tokens[0]+"("+strArray+")")

	# Run the code that's been loaded in
	def run(self):
		if len(self.code) == 0:
			self.raiseError("Virtual Machine has no code loaded in to run")
		while self.finished == False:
			self.incCycles()
			if self.skipCurr == True:
				self.skipCurr = False
			elif self.code[self.pc] == "self.end([''])":
				eval(self.code[self.pc])
			elif self.inDefinition != None:
				self.functions[self.inDefinition].append(self.code[self.pc])
			else:
				eval(self.code[self.pc])
			self.pc = self.pc + 1
			if self.pc > len(self.code)-1:
				self.finished = True
	# Commands
	def jump(self, params):
		n = self.getVal(params[0])
		if self.pc+n > len(self.code)-1 or self.pc+n < 0:
			self.raiseError('Attempt to jump out of bounds')
		self.pc = self.pc + n
	def set(self, params):
		a = params[0]
		b = params[1]
		self.setVal(a, self.getVal(b))
	def sub(self, params):
		a = params[0]
		b = params[1]
		c = params[2]
		self.setVal(c, self.getVal(a) - self.getVal(b))
	def add(self, params):
		a = params[0]
		b = params[1]
		c = params[2]
		self.setVal(c, self.getVal(a) + self.getVal(b))
	def memLoad(self, params):
		address = params[0]
		self.setVal(address, params[1:])
	def cmp(self, params):
		a = self.getVal(params[0])
		b = params[1]
		c = self.getVal(params[2])
		sub = [params[3]]
		if b == '>' and a > c:
			self.runFunction(sub)
		elif b == '<=' and a <= c:
			self.runFunction(sub)
		elif b == '=' and a == c:
			self.runFunction(sub)

		if b != '=' and b != '<=' and b != '>':
			self.raiseError("Invalid comparator")
	def runFunction(self, params):
		sub = params[0]
		if sub not in self.functions:
			self.raiseError("Attempt to call non existant function")
		for line in self.functions[sub]:
			if self.skipCurr == True:
				self.skipCurr = False
				continue
			eval(line)
	def incCycles(self):
		self.cycles = self.cycles + 1
		if self.cycles > self.maxCycles:
			raise ValueError("Machine surpassed max cycles, possible infinite loop")
	def setVal(self, param, data):
		# reference
		if match(param, r'^\*\d+\:.*$'):
			param = re.sub(r'\*',r'',param)
			a = int(param.split(':')[0])
			n = param.split(':')[1]
			if n == "":
				memseg = self.memory
			else:
				if n not in self.memorySegments:
					self.raiseError("Attempt to access non-existant memory segment")
				memseg = self.memorySegments[n]
			address = memseg.read(a)
			memseg.write(address, data)

		# register reference
		elif match(param, r'\*[rR]\d:$'):
			try:
				num = param.split('r')[1]
				num = num.split(':')[0]
			except:
				num = param.split('R')[1]
				num = num.split(':')[0]
			if int(num) > self.numRegisters-1:
				self.raiseError('Attempt to access non-existant register')
			reg = param.upper()
			reg = reg.split(":")[0]
			reg = reg.split("*")[1]
			address = self.memory.read(self.registers[reg])
			return self.memory.write(address, data)
		# register address
		elif match(param, r'^[rR]\d\:$'):
			try:
				num = param.split('r')[1]
				num = num.split(':')[0]
			except:
				num = param.split('R')[1]
				num = num.split(':')[0]
			if int(num) > self.numRegisters-1:
				self.raiseError('Attempt to access non-existant register')
			reg = param.upper()
			reg = reg.split(":")[0]
			return self.memory.write(self.registers[reg], data)	
		# register
		elif match(param, r'^[rR]\d$') :
			try:
				num = param.split('r')[1]
			except:
				num = param.split('R')[1]
			if int(num) > self.numRegisters-1:
				self.raiseError('Attempt to access non-existant register')
			self.registers[param.upper()] = data
		# address
		elif match(param, r'^\d+\:.*$'):
			a = int(param.split(':')[0])
			n = param.split(':')[1]
			if n == "":
				memseg = self.memory
			else:
				if n not in self.memorySegments:
					self.raiseError("Attempt to access non-existant memory segment")
				memseg = self.memorySegments[n]
			memseg.write(a, data)
		else:
			self.raiseError("Command refused input: " + param)
	def skip(self, params):
		data = self.getVal(params[0])
		if data != 0:
			self.skipCurr = True
	def newMemSeg(self, params):
		name = params[0]
		size = int(params[1])
		if name in self.memorySegments:
			self.raiseError("Memory segment label already in use")
		self.memorySegments[name] = MemorySegment(name, size)
	def setMemSeg(self, name):
		if name not in self.memorySegments:
			self.raiseError("Attempt to access non-existant memory segment")
		else:
			self.memory = self.memorySegments[name]
	def define(self, params):
		self.inDefinition = params[0]
		self.functions[params[0]] = []
	def end(self, params):
		self.inDefinition = None
	def memLoad(self, params):
		a = self.getVal(params[0])
		self.memory.write(a, params[1:])
	def getState(self):
		d = {}
		d['cycles'] = self.cycles
		d['pc'] = self.pc
		d['registers'] = self.registers
		d['memory'] = {}
		for seg in self.memorySegments:
			d['memory'][seg] = self.memorySegments[seg].data
		return d
	def showState(self):
		state = self.getState()
		print("-------- Virtual Machine State @ " + time.strftime("%d/%m/%Y %H:%M:%S")+" --------")
		print("Registers")
		for r in sorted(state['registers'].keys()):
			sys.stdout.write(r+":"+str(state['registers'][r])+"    ")
		print("")
		print("")
		print("PC"+" "*52+"CYCLES")
		space = 60 - len(str(state['pc'])) - len(str(state['cycles']))
		print(str(state['pc']) + " "*space + str(state['cycles']))
		print("")
		for seg in sorted(state['memory'].keys()):
			print(seg)
			print("")
			terminal = []
			temp = []
			rowSize = 11
			for i,d in enumerate(state['memory'][seg]):
				if i%rowSize == 0:
					if len(temp) != 0:
						terminal.append(temp)
					temp = []
					temp.append(i)
				temp.append(d)
			while len(temp) <= rowSize:
				temp.append(-1)
			terminal.append(temp)
			for line in terminal:
				print("{:3}  {:5}{:5}{:5}{:5}{:5}{:5}{:5}{:5}{:5}{:5}{:5}".format(line[0],line[1],line[2],line[3],line[4],line[5],line[6],line[7],line[8],line[9],line[10],line[11]))
			print("")
	# Get the value of a paramter
	def getVal(self, param):
		# reference
		if match(param, r'^\*\d+\:.*$'):
			param = re.sub(r'\*',r'',param)
			a = int(param.split(':')[0])
			n = param.split(':')[1]
			if n == "":
				memseg = self.memory
			else:
				if n not in self.memorySegments:
					self.raiseError("Attempt to access non-existant memory segment")
				memseg = self.memorySegments[n]
			address = memseg.read(a)
			return memseg.read(address)
		# register reference
		elif match(param, r'\*[rR]\d:$'):
			try:
				num = param.split('r')[1]
				num = num.split(':')[0]
			except:
				num = param.split('R')[1]
				num = num.split(':')[0]
			if int(num) > self.numRegisters-1:
				self.raiseError('Attempt to access non-existant register')
			reg = param.upper()
			reg = reg.split(":")[0]
			reg = reg.split("*")[1]
			address = self.memory.read(self.registers[reg])
			return self.memory.read(address)
		# register address
		elif match(param, r'^[rR]\d\:$'):
			try:
				num = param.split('r')[1]
				num = num.split(':')[0]
			except:
				num = param.split('R')[1]
				num = num.split(':')[0]
			if int(num) > self.numRegisters-1:
				self.raiseError('Attempt to access non-existant register')
			reg = param.upper()
			reg = reg.split(":")[0]
			return self.memory.read(self.registers[reg])
		# register normal
		elif match(param, r'^[rR]\d$'):
			try:
				num = param.split('r')[1]
			except:
				num = param.split('R')[1]
			if int(num) > self.numRegisters-1:
				self.raiseError('Attempt to access non-existant register')
			return self.registers[param.upper()]
		# address
		elif match(param, r'^\d+\:.*$'):
			a = int(param.split(':')[0])
			n = param.split(':')[1]
			if n == "":
				memseg = self.memory
			else:
				if n not in self.memorySegments:
					self.raiseError("Attempt to access non-existant memory segment")
				memseg = self.memorySegments[n]
			return memseg.read(a)
		# immediate
		elif match(param, r'^\-?\d+$'):
			return int(param)
		else:
			self.raiseError("Command refused input: " + param)

	def raiseError(self, msg, **optional):
		line = self.code[self.pc].split('.')[1]
		line = re.sub(r'[\[\]\(\)\',]',r' ',line)
		line = re.sub(r'\s+',r' ',line)
		line = re.sub(r'\s*$',r'',line)
		message = msg + " ("+line+")"
		raise ValueError(message)
if __name__ == "__main__":
	vm = VM(50, 1000) # 500 cells of memory and a max of 1000 cycles
	vm.loadCode("set 0: 5")
	vm.run()
	vm.showState()
import types #please don't deprecate...
from Line import Line, DataLine #class of Line.py used for storing each line of assembly code
from RegisterFile import RegisterFile, Register, FloatRegister  # class of RegisterFile.py used to store the registers of the register file
from RegisterFile import MemoryManager #used to manage memory
import sqlite3 as sql #needed for any and all required sqlite operations (custom mnemonics)
import os #needed to open files in the "Databases" subdirectory

#this class handles checking the syntax of an assembly file passed to it by parsing into Line objects
class Program:
    def __init__(self, file, regFile: RegisterFile):
        self.file = file
        self.lines: list = [] #list of Line and DataLine objects
        self.data: list[DataLine] = [] #list of just DataLine objects (for better optimization)
        self.segments: list[Line] = [] #list of segment headers (for better optimization)
        self.regFile: RegisterFile = regFile
        self.memorySegments: list[str] = [] #list of taken memory address names

        #call the 'CallAssembler' function to initialize the fields
        self.CallAssembler()

        #close the file (to avoid any data corruption from it being accessed after it is no longer needed)
        self.file.close()

    #function to perform the initial read into each line object
    def CallAssembler(self) -> None:
        counter: int = 1 #counter to give each line a number (address)
        globalCounter: int = 0 #counter to give line a global line number (line number in the file)
        foundDataSegment: bool = False #have we found the data segment?
        foundTextSegment: bool = False #have we found the text segment? (temporary)
        foundTextSegmentGlobal: bool = False #have we found the text segment? (persistent)
        #create all the lines, any other raised exceptions are found in those segments
        for line in self.file:
            globalCounter += 1  #increment the global line counter

            #if the first character found (non-whitespace) is '#' or line is whitespace only, then ignore it since the whole line is a comment
            if(len(str(line).strip()) == 0):
                continue
            if(str(line).strip()[0] == '#'):
                continue

            #split the line to remove any comments
            if(".asciiz" in line): #this is the case we need to make sure # is not in quotes
                protoLine = ""
                quotesFound = 0
                for i in range(len(line)):
                    protoLine = protoLine + line[i]
                    if(line[i] == "\""):
                        quotesFound = quotesFound + 1
                    if (quotesFound == 2):
                        break #force all other things after the second quote to disappear
                line = protoLine
            else:
                line = str(line).strip().split('#')[0]

            #if the line is the start of the data segment
            if(self.IsDataSegment(str(line))):
                foundDataSegment = True
                foundTextSegment = False
                self.lines.append(DataLine(line, counter, globalCounter))
                counter += 1
                continue
            #if the line is the start of the text (code) segment
            elif(self.IsTextSegment(str(line))):
                foundTextSegment = True
                foundTextSegmentGlobal = True
                foundDataSegment = False
                self.lines.append(Line(line, counter, globalCounter))
                counter += 1
                continue

            #we found a segment header before we start the text segment (syntax error program not valid)
            elif(str(line).strip()[len(str(line).strip()) - 1] == ':' and not foundTextSegment):
                raise Exception("Fatal Error -- Segment header before text segment")

            #depending on if we find the data segment (might not exist), and text segment (must exist)
            if(foundDataSegment): #in the data segment
                self.lines.append(DataLine(line, counter, globalCounter))
                counter += 1
            elif(foundTextSegment):
                self.lines.append(Line(line, counter, globalCounter))
                counter += 1

        #if there was no text segment raise an error (syntax error program not valid)
        if(not foundTextSegmentGlobal):
            raise Exception("Fatal Error -- Text segment not found")

        #set up the other two lists for optimization
        for i in range(len(self.lines)):
            if(isinstance(self.lines[i], DataLine)):
                self.data.append(self.lines[i])
            else:
                if(self.lines[i].segType == "header"):
                    self.segments.append(self.lines[i])

    #function to determine if a line is the .data segment
    def IsDataSegment(self, line: str) -> bool:
        line = line.strip()
        if(len(line) < 5):
            return False
        return (line[0] == '.' and line[1] == 'd' and line[2] == 'a' and line[3] == 't' and line[4] == 'a')

    #function to determine if a line is the .text segment
    def IsTextSegment(self, line: str) -> bool:
        line = line.strip()
        if (len(line) < 5):
            return False
        return (line[0] == '.' and line[1] == 't' and line[2] == 'e' and line[3] == 'x' and line[4] == 't')

    #function to 'run' the program
    def RunAssemblyProgram(self) -> bool:
        #set the ip (instruction pointer to the first line)
        self.regFile.ProgramCounter = 1

        #set a boolean flag so the loop knows if it should break early (from a syscall exit)
        exitFlag: bool = False
        #while the ip is less than the number of lines or until syscall exit, continue running the program
        while(self.regFile.ProgramCounter < len(self.lines)):
            #figure out what the line type is and call the corresponding function below to perform the operation
            if(isinstance(self.lines[self.regFile.ProgramCounter], DataLine)): #skip empty instruction lines
                self.regFile.ProgramCounter += 1
                continue
            if (isinstance(self.lines[self.regFile.ProgramCounter].instruction, types.NoneType)):  # skip empty instruction lines
                self.regFile.ProgramCounter += 1
                continue
            match (self.lines[self.regFile.ProgramCounter].instruction.strip()):
                case "syscall": #call the syscall function
                    exitFlag = self.Syscall()
                    self.regFile.ProgramCounter += 1
                case "li": #call the load immediate function
                    self.LoadImmediate()
                    self.regFile.ProgramCounter += 1
                case "la": #call the load address function
                    self.LoadAddress()
                    self.regFile.ProgramCounter += 1
                case "add":
                    self.Add()
                    self.regFile.ProgramCounter += 1
                case "sub":
                    self.Sub()
                    self.regFile.ProgramCounter += 1
                case "mul":
                    self.Mul()
                    self.regFile.ProgramCounter += 1
                case "mult":
                    self.Mult()
                    self.regFile.ProgramCounter += 1
                case "div":
                    self.Div()
                    self.regFile.ProgramCounter += 1
                case "move":
                    self.Move()
                    self.regFile.ProgramCounter += 1
                case "sgt":
                    self.SetGreaterThan()
                    self.regFile.ProgramCounter += 1
                case "beqz":
                    self.BranchIfEqualZero()
                case "seq":
                    self.SetEqual()
                    self.regFile.ProgramCounter += 1
                case "j":
                    self.J()
                case "blt":
                    self.BranchIfLessThan()
                case "bgt":
                    self.BranchIfGreaterThan()
                case "ble":
                    self.BranchIfLessThanEqual()
                case "bgtz":
                    self.BranchIfGreaterThanZero()
                case "sw":
                    self.StoreWord()
                    self.regFile.ProgramCounter += 1
                case "s.s":
                    self.StoreWordSinglePrecision()
                    self.regFile.ProgramCounter += 1
                case "jal":
                    self.JumpAndLink()
                case "bge":
                    self.BranchIfGreaterThanEqual()
                case "lw":
                    self.LoadWord()
                    self.regFile.ProgramCounter += 1
                case "jr":
                    self.JumpRegister()
                case "beq":
                    self.BranchIfEqual()
                case "bltz":
                    self.BranchIfLessThanZero()
                case "bnez":
                    self.BranchIfNotEqualZero()
                case "mfhi":
                    self.MoveFromHi()
                    self.regFile.ProgramCounter += 1
                case "mflo":
                    self.MoveFromLo()
                    self.regFile.ProgramCounter += 1
                case "l.s":
                    self.LoadSinglePrecision()
                    self.regFile.ProgramCounter += 1
                case "lwc1":
                    self.LoadWordCoproc()
                    self.regFile.ProgramCounter += 1
                case "mul.s":
                    self.MulSinglePrecision()
                    self.regFile.ProgramCounter += 1
                case "sub.s":
                    self.SubSinglePrecision()
                    self.regFile.ProgramCounter += 1
                case "abs.s":
                    self.AbsSinglePrecision()
                    self.regFile.ProgramCounter += 1
                case "abs":
                    self.Abs()
                    self.regFile.ProgramCounter += 1
                case "c.lt.s":
                    self.CoprocIfLessThanSinglePrecision()
                    self.regFile.ProgramCounter += 1
                case "c.eq.s":
                    self.CoprocIfEqualSinglePrecision()
                    self.regFile.ProgramCounter += 1
                case "bc1t":
                    self.BranchIfCoprocFlagTrue()
                case "mov.s":
                    self.MoveSinglePrecision()
                    self.regFile.ProgramCounter += 1
                case "add.s":
                    self.AddSinglePrecision()
                    self.regFile.ProgramCounter += 1
                case "div.s":
                    self.DivSinglePrecision()
                    self.regFile.ProgramCounter += 1
                case "addi":
                    self.AddImmediate()
                    self.regFile.ProgramCounter += 1
                case "subi":
                    self.SubImmediate()
                    self.regFile.ProgramCounter += 1
                case "dbct":
                    self.DatabaseConnect()
                    self.regFile.ProgramCounter += 1
                case "dbcl":
                    self.DatabaseClose()
                    self.regFile.ProgramCounter += 1
                case "dbs":
                    self.DatabaseSelect()
                    self.regFile.ProgramCounter += 1
                case "dbi":
                    self.DatabaseInsert()
                    self.regFile.ProgramCounter += 1
                case "dbd":
                    self.DatabaseDelete()
                    self.regFile.ProgramCounter += 1
                case "dbt":
                    self.DatabaseTable()
                    self.regFile.ProgramCounter += 1
                case "dbu":
                    self.DatabaseUpdate()
                    self.regFile.ProgramCounter += 1
                case "dbit":
                    self.DatabaseIterate()
                    self.regFile.ProgramCounter += 1

                case _: #default case was either .data, .text, .glbl, or a segment/data label
                    self.regFile.ProgramCounter += 1

            #print(self.regFile.ProgramCounter) #print the line number to ensure the program is moving along

            #if the exitFlag was set true by the syscall, then exit the function by returning true
            if(exitFlag):
                return exitFlag

    #function to figure out what register is referenced by a given string
    def GetRegister(self, registerString: str) -> Register | FloatRegister:
        match (registerString):
            case "$at":
                return self.regFile.AT
            case "$v0":
                return self.regFile.V0
            case "$v1":
                return self.regFile.V1
            case "$zero":
                return self.regFile.ZERO
            case "$a0":
                return self.regFile.A[0]
            case "$a1":
                return self.regFile.A[1]
            case "$a2":
                return self.regFile.A[2]
            case "$a3":
                return self.regFile.A[3]
            case "$t0":
                return self.regFile.T[0]
            case "$t1":
                return self.regFile.T[1]
            case "$t2":
                return self.regFile.T[2]
            case "$t3":
                return self.regFile.T[3]
            case "$t4":
                return self.regFile.T[4]
            case "$t5":
                return self.regFile.T[5]
            case "$t6":
                return self.regFile.T[6]
            case "$t7":
                return self.regFile.T[7]
            case "$t8":
                return self.regFile.T[8]
            case "$t9":
                return self.regFile.T[9]
            case "$s0":
                return self.regFile.S[0]
            case "$s0":
                return self.regFile.S[0]
            case "$s1":
                return self.regFile.S[1]
            case "$s2":
                return self.regFile.S[2]
            case "$s3":
                return self.regFile.S[3]
            case "$s4":
                return self.regFile.S[4]
            case "$s5":
                return self.regFile.S[5]
            case "$s6":
                return self.regFile.S[6]
            case "$s7":
                return self.regFile.S[7]
            case "$k0":
                return self.regFile.K0
            case "$k1":
                return self.regFile.K1
            case "$gp":
                return self.regFile.GP
            case "$sp":
                return self.regFile.SP
            case "$fp":
                return self.regFile.FP
            case "$ra":
                return self.regFile.RA
            case "$f0":
                return self.regFile.F[0]
            case "$f1":
                return self.regFile.F[1]
            case "$f2":
                return self.regFile.F[2]
            case "$f3":
                return self.regFile.F[3]
            case "$f4":
                return self.regFile.F[4]
            case "$f5":
                return self.regFile.F[5]
            case "$f6":
                return self.regFile.F[6]
            case "$f7":
                return self.regFile.F[7]
            case "$f8":
                return self.regFile.F[8]
            case "$f9":
                return self.regFile.F[9]
            case "$f10":
                return self.regFile.F[10]
            case "$f11":
                return self.regFile.F[11]
            case "$f12":
                return self.regFile.F[12]
            case "$f13":
                return self.regFile.F[13]
            case "$f14":
                return self.regFile.F[14]
            case "$f15":
                return self.regFile.F[15]
            case "$f16":
                return self.regFile.F[16]
            case "$f17":
                return self.regFile.F[17]
            case "$f18":
                return self.regFile.F[18]
            case "$f19":
                return self.regFile.F[19]
            case "$f20":
                return self.regFile.F[20]
            case "$f21":
                return self.regFile.F[21]
            case "$f22":
                return self.regFile.F[22]
            case "$f23":
                return self.regFile.F[23]
            case "$f24":
                return self.regFile.F[24]
            case "$f25":
                return self.regFile.F[25]
            case "$f26":
                return self.regFile.F[26]
            case "$f27":
                return self.regFile.F[27]
            case "$f28":
                return self.regFile.F[28]
            case "$f29":
                return self.regFile.F[29]
            case "$f30":
                return self.regFile.F[30]
            case "$f31":
                return self.regFile.F[31]
            case _: #default case where the register did not exist/was not a valid name
                raise Exception("Fatal Error -- Register parameter not valid")

    #function to determine if a parameter is a valid segment header (label)
    def IsLabel(self, possibleLabel: str) -> bool:
        for i in range(len(self.segments)):
            if possibleLabel == self.segments[i].instruction:
                return True
        return False

    #function to determine if a parameter is a valid data segment address name (variable name)
    def IsVariableName(self, possibleName: str) -> bool:
        for i in range(len(self.data)):
            if(possibleName == self.data[i].contentName):
                return True
        return False

    #function to return the value found at a specified data segment address name (variable name)
    def GetVariableValue(self, variableName: str):
        for i in range(len(self.lines)):
            if(not isinstance(self.lines[i], DataLine)): #make sure the line is part of the DataLine class
                continue
            if(variableName == self.lines[i].contentName):
                return self.lines[i].value
        raise Exception("Fatal Error -- Data segment name could not be found")

    #function to determine if a string (parameter) is any valid register (not including $zero)
    def IsRegister(self, parameter: str) -> bool:
        registers: list[str] = ["$at", "$v0", "$v1", "$a0", "$a1", "$a2", "$a3", "$t0", "$t1",
                                "$t2", "$t3", "$t4", "$t5", "$t6", "$t7", "$t8", "$t9", "$s0", "$s1",
                                "$s2", "$s3", "$s4", "$s5", "$s6", "$s7", "$s8", "$s9", "$k0", "$k1",
                                "$gp", "$sp", "$ra", "$fp", "$f0", "$f1", "$f2", "$f3", "$f4", "$f5",
                                "$f6", "$f7", "$f8", "$f9", "$f10", "$f11", "$f12", "$f13", "$f14", "$f15",
                                "$f16", "$f17", "$f18", "$f19", "$f20", "$f21", "$f22", "$f23", "$f24", "$f25",
                                "$f26", "$f27", "$f29", "$f30", "$f31"]  #reserved register names

        if (parameter.strip() in registers):
            return True
        return False

    #function to determine if a string (parameter) is a valid flop register
    def IsFlopRegister(self, parameter: str) -> bool:
        registers: list[str] = ["$f0", "$f1", "$f2", "$f3", "$f4", "$f5", "$f6", "$f7", "$f8", "$f9", "$f10",
                                "$f11", "$f12", "$f13", "$f14", "$f15", "$f16", "$f17", "$f18", "$f19", "$f20",
                                "$f21", "$f22", "$f23", "$f24", "$f25", "$f26", "$f27", "$f29", "$f30",
                                "$f31"]  #reserved register names

        if (parameter.strip() in registers):
            return True
        return False

#------------------------------ALL FUNCTIONS BELOW HERE ARE THE INSTRUCTION FUNCTIONS (ex. add or li)------------------------------------
    #function to perform the syscall function stored in the $v0 register
    def Syscall(self) -> bool:
        memManager: MemoryManager._MemoryManagerImpl = MemoryManager() #memory manager used for finding memory address(es)

        #get the number in the $v0 for the instruction
        match (self.regFile.V0.value):
            case 1: #print integer (in $a0)
                if(not isinstance(self.regFile.A[0].value, int) or self.regFile.A[0].value == None): #raise an error if the value is not a string
                    raise Exception("Fatal Error -- Syscall function 1 requires an integer at line:", str(self.regFile.ProgramCounter))
                print(str(self.regFile.A[0].value), end="")

            case 2: #print float (in $f12)
                if (not isinstance(self.regFile.F[12].value, float) or self.regFile.F[12].value == None):  #raise an error if the value is not a float
                    raise Exception("Fatal Error -- Syscall function 2 requires a float at line:", str(self.regFile.ProgramCounter))
                print(str(self.regFile.F[12].value), end="")

            case 4: #print string (in $a0)
                if(not memManager.containsAddress(hex(self.regFile.A[0].value))): #raise an error if the value is not a hex address
                    raise Exception("Fatal Error -- Syscall function 4 requires $a0 to store a valid address at line:", str(self.regFile.ProgramCounter))

                #print the line
                print(bytes(memManager.get_address(hex(self.regFile.A[0].value)), "utf-8").decode("unicode_escape"), end="")

            case 5: #get user integer input
                self.regFile.V0.value = input()
                try:
                    int(self.regFile.V0.value)
                except ValueError:
                    raise Exception("Fatal Error -- Invalid syscall input (syscall 5, integer expected)")

            case 6: #get user float input (goes into $f0)
                self.regFile.F[0].value = input()
                try:
                    float(self.regFile.F[0].value)
                except ValueError:
                    raise Exception("Fatal Error -- Invalid syscall input (syscall 6, float expected)")

            case 8: #get user string input
                #see if the buffer input in $a0 exists
                inputExist: bool = False
                labelName = False
                for i in range(len(self.lines)):
                    if(not isinstance(self.lines[i], DataLine)):
                        continue
                    if(str(self.lines[i].value) != "None"):
                        if(str(int(str(self.lines[i].value), 16)) == str(self.regFile.A[0].value) and str(self.lines[i].contentType) == ".space"):
                            inputExist = True
                            labelName = self.lines[i]
                            break

                if(not inputExist):
                    raise Exception("Fatal Error -- Address in $a0 does not exist in .data or is not a .space")

                #see if the buffer size in $a1 exists (is a value entered using lw)
                inputBufferExist: bool = False
                bufferSize: int = 0
                for i in range(len(self.lines)):
                    if(not isinstance(self.lines[i], DataLine)):
                        continue
                    if(str(self.lines[i].value) != "None"):
                        if (memManager.get_address(hex(int(self.lines[i].value, 16))) == str(self.regFile.A[1].value) and str(self.lines[i].contentType) == ".word"):
                            inputBufferExist = True
                            bufferSize = self.lines[i]
                            break

                if (not inputBufferExist):
                    raise Exception("Fatal Error -- Buffer size in $a1 does not exist in .data or is not a .word")

                size: int = int(self.regFile.A[1].value)

                #get the user input
                stringInput: str = input()
                input_buffer = stringInput[:size] #truncate the input to the buffer size

                #put the buffer size of the input into the DataLine of $a0 and into $a0
                if(size > len(input_buffer)):
                    memManager.setAddress(labelName.value, input_buffer)
                else:
                    raise Exception("Fatal Error -- Input caused buffer overflow at line:", self.lines[self.regFile.ProgramCounter].globalLineNumber)

            case 9: #allocation $a0 bytes into memory
                if(not isinstance(self.regFile.A[0], int) or self.regFile.A[0].value == None):
                    raise Exception("Fatal Error -- value must be integer at line:",self.lines[self.regFile.ProgramCounter].globalLineNumber)
                #get the next address from the memManager and stash it into the $v0 register
                self.regFile.V0.value = hex(int(str(memManager.mostRecentAddress), 16) + 4)

                #enfore that the number should be divisible by 4
                bytes1: int = self.regFile.A[0].value
                while(bytes1 % 4 != 0):
                    bytes1 += 1

                #begin adding the number of data segments required
                for i in range(bytes1 // 4):
                    memManager.add_address() #memory is unitialized 

            case 10: #exit the program
                return True

            case _: #default case, throw an error
                raise Exception("Fatal Error -- No such function for code:\'" + str(self.regFile.V0.value) + "\' at line:" + str(self.regFile.ProgramCounter))

        return False #in any other case other than 10 and default, ensure the exitFlag remains False so that the program continues running

    #function to load the number of the second parameter into the register of the first parameter
    def LoadImmediate(self) -> None:
        #get the register that will get the immediate loaded into it
        register: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0])

        #place the value of the second parameter into the register
        register.value = int(self.lines[self.regFile.ProgramCounter].parameters[1])

    #function to load the address (place the string) into a register
    def LoadAddress(self) -> None:
        #get the register that will get the variable loaded into it
        register: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0])

        #check if the variable label makes sense
        if(not self.IsVariableName(self.lines[self.regFile.ProgramCounter].parameters[1])):
            raise Exception("Fatal Error -- Variable name not found in .data segment")
        #find the DataLine that has this variable name
        for i in range(len(self.data)):
            if (str(self.data[i].contentName) == self.lines[self.regFile.ProgramCounter].parameters[1]):
                #place the base address into the register
                register.value = int(str(self.data[i].value), 16) #value stores the base address
                break

    #function to load a data word (32-bit) into a register from a place in memory
    def LoadWord(self) -> None:
        memManager: MemoryManager._MemoryManagerImpl = MemoryManager()  #memory manager used for finding memory address(es)

        #get the register that will get the word loaded into it
        register: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0])

        #lw $reg, label
        if(self.IsVariableName(self.lines[self.regFile.ProgramCounter].parameters[1])):
            #find the DataLine with this name and set the value of the register to the value of the line
            found: bool = False
            for i in range(len(self.data)):
                if(str(self.data[i].contentName) == str(self.lines[self.regFile.ProgramCounter].parameters[1]) and (self.data[i].contentType == ".word" or self.data[i].contentType == ".space")):
                    found = True
                    if (not memManager.containsAddress(hex(int(self.data[i].value, 16)))):
                        raise Exception("Fatal Error -- base address (in label) name not found in memory")

                    register.value = memManager.get_address(hex(int(self.data[i].value, 16)))
                    break

            if(not found):
                raise Exception("Fatal Error -- Variable name not found in .data segment or is not a .word or .space")
        else:
            #lw $reg, ($reg)
            if(self.lines[self.regFile.ProgramCounter].parameters[1].strip()[0] == '('):
                if(self.IsRegister(self.lines[self.regFile.ProgramCounter].parameters[1].strip()[1:-1])):
                    baseAddress: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1].strip()[1:-1])

                    try:
                        if (not memManager.containsAddress(hex(baseAddress.value))):
                            raise Exception("Fatal Error -- base address (in register) name not found in memory")

                        register.value = memManager.get_address(hex(baseAddress.value))
                    except:
                        if (not memManager.containsAddress(hex(int(str(baseAddress.value), 16)))):
                            raise Exception("Fatal Error -- base address (in register) name not found in memory")

                        register.value = memManager.get_address(hex(int(str(baseAddress.value), 16)))

                #lw $reg, (label)
                elif (self.lines[self.regFile.ProgramCounter].parameters[1].strip()[0] == '('):
                    if (self.IsVariableName(self.lines[self.regFile.ProgramCounter].parameters[1].strip()[1:-1])):
                        #find the DataLine with this name and set the value of the register to the value of the line
                        found: bool = False
                        for i in range(len(self.data)):
                            if (str(self.data[i].contentName) == str(self.lines[self.regFile.ProgramCounter].parameters[1]) and (self.data[i].contentType == ".word" or self.data[i].contentType == ".space")):
                                found = True
                                if (not memManager.containsAddress(hex(int(self.data[i].value, 16)))):
                                    raise Exception("Fatal Error -- base address (from label) not found in memory")

                                register.value = memManager.get_address(hex(int(self.data[i].value, 16)))
                                break

                        if (not found):
                            raise Exception("Fatal Error -- Variable name not found in .data segment or is not a .word or .space")

                else:
                    raise Exception("Fatal Error -- Load word syntax incorrect at line:", str(self.lines[self.regFile.ProgramCounter].globalLineNumber))
            #first character is not '('
            else:
                #lw $reg, label($reg)
                if(self.IsVariableName(self.lines[self.regFile.ProgramCounter].parameters[1].split('(')[0].strip())):
                    #find the DataLine with this name and set the value of the register to the value of the line
                    found: bool = False
                    for i in range(len(self.data)):
                        if(self.data[i].contentName is not None):
                            if (str(self.data[i].contentName.strip()) == str(self.lines[self.regFile.ProgramCounter].parameters[1].split('(')[0].strip()) and (self.data[i].contentType == ".word" or self.data[i].contentType == ".space")):
                                found = True
                                if(self.IsRegister(self.lines[self.regFile.ProgramCounter].parameters[1].split('(')[1].strip()[:-1])):
                                    offsetRegister: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1].split('(')[1].strip()[:-1])
                                    if (not memManager.containsAddress(hex(int(self.data[i].value, 16) + offsetRegister.value))):
                                        raise Exception("Fatal Error -- base address (from label($reg)) not found in memory")

                                    register.value = memManager.get_address(hex(int(self.data[i].value, 16) + offsetRegister.value))
                                    break
                                else:
                                    raise Exception("Fatal Error -- offset register not valid")

                    if (not found):
                        raise Exception("Fatal Error -- Variable name not found in .data segment or is not a .word or .space at line:", self.lines[self.regFile.ProgramCounter].globalLineNumber)
                else:
                    offset: int = int(self.lines[self.regFile.ProgramCounter].parameters[1].split('(')[0].strip())

                    #lw $reg, offset(label) is valid (offset it an immediate in this case)
                    if(self.IsVariableName(self.lines[self.regFile.ProgramCounter].parameters[1].split('(')[1].strip()[1:-1])):
                        #find the DataLine with this name and set the value of the register to the value of the line
                        found: bool = False
                        for i in range(len(self.data)):
                            if (str(self.data[i].contentName) == str(self.lines[self.regFile.ProgramCounter].parameters[1]) and (self.data[i].contentType == ".word" or self.data[i].contentType == ".space")):
                                found = True
                                if (not memManager.containsAddress(hex(int(self.data[i].value, 16) + offset))):
                                    raise Exception("Fatal Error -- base address (in offset(label)) name not found in memory")

                                register.value = memManager.get_address(hex(int(self.data[i].value, 16) + offset))
                                break

                        if (not found):
                            raise Exception("Fatal Error -- Variable name not found in .data segment or is not a .word or .space")
                    #lw $reg, offset($reg) is valid (offset is an immediate in this case)
                    elif(self.IsRegister(self.lines[self.regFile.ProgramCounter].parameters[1].split('(')[1].strip()[1:-1])):
                        baseAddress: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1].split('(')[1].strip()[1:-1])

                        if (not memManager.containsAddress(hex(int(baseAddress.value, 16) + offset))):
                            raise Exception("Fatal Error -- base address (in offset($reg)) name not found in memory")

                        register.value = memManager.get_address(hex(int(baseAddress.value, 16) + offset))
                    else:
                        raise Exception("Fatal Error -- Load word syntax incorrect at line:", str(self.lines[self.regFile.ProgramCounter].globalLineNumber))

    #function to set a place in memory to an offset of a word (from a place in memory or register)
    def StoreWord(self):
        memManager: MemoryManager._MemoryManagerImpl() = MemoryManager()

        #get the register of the first parameter (what will be stored as the given memory address)
        sourceRegister: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0].strip())

        #sw $reg, label
        if(self.IsVariableName(self.lines[self.regFile.ProgramCounter].parameters[1].strip())):
            #find the DataLine with this name and set the value of the register to the value of the line
            found: bool = False
            for i in range(len(self.data)):
                if (str(self.data[i].contentName) == str(self.lines[self.regFile.ProgramCounter].parameters[1])):
                    found = True
                    if (not memManager.containsAddress(hex(int(self.data[i].value, 16)))):
                        raise Exception("Fatal Error -- base address (label) name not found in memory")

                    if(self.data[i].contentType == ".float" and not isinstance(sourceRegister, FloatRegister)):
                        raise Exception("Fatal Error -- trying to store non-float in float memory")

                    memManager.setAddress(hex(int(self.data[i].value, 16)), value=sourceRegister.value)
                    break

            if (not found):
                raise Exception("Fatal Error -- Variable name not found in .data segment or is not a .word")
        else:
            #sw $reg, label($reg)
            if(self.IsVariableName(self.lines[self.regFile.ProgramCounter].parameters[1].strip().split('(')[0].strip())):
                if(self.IsRegister(self.lines[self.regFile.ProgramCounter].parameters[1].split('(')[1].strip()[:-1])):
                    offsetRegister: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1].split('(')[1].strip()[:-1])

                    #find the DataLine with this name and set the value of the register to the value of the line
                    found: bool = False
                    for i in range(len(self.data)):
                        if (str(self.data[i].contentName) == str(self.lines[self.regFile.ProgramCounter].parameters[1].strip().split('(')[0].strip())):
                            found = True
                            if (not memManager.containsAddress(hex(int(self.data[i].value, 16) + offsetRegister.value))):
                                raise Exception("Fatal Error -- address not found in memory")

                            if (self.data[i].contentType == ".float" and not isinstance(sourceRegister, FloatRegister)):
                                raise Exception("Fatal Error -- trying to store non-float in float memory")

                            memManager.setAddress(hex(int(self.data[i].value, 16) + offsetRegister.value), value=sourceRegister.value)
                            break
                else:
                    raise Exception("Fatal Error -- offset register is not a valid register")
            #sw $reg, offset($reg (base address))
            else:
                try:
                    offset: int = int(self.lines[self.regFile.ProgramCounter].parameters[1].split('(')[0].strip())
                    if (self.IsRegister(self.lines[self.regFile.ProgramCounter].parameters[1].split('(')[1].strip()[:-1])):
                        baseRegister: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1].split('(')[1].strip()[:-1])

                        if(memManager.containsAddress(hex(int(baseRegister.value, 16) + offset))):
                            #determine if the line type is .flaot (for extra protection)
                            for i in range(len(self.data)):
                                if (str(self.data[i].value) == str(baseRegister.value)): #if the base addresses are the same (it is the line we are after)
                                    if (self.data[i].contentType == ".float" and not isinstance(sourceRegister, FloatRegister)):
                                        raise Exception("Fatal Error -- trying to store non-float in float memory")
                                    break

                            memManager.setAddress(hex(int(baseRegister.value, 16) + offset), value=baseRegister.value)
                        else:
                            raise Exception("Fatal Error -- base register + offset not found in memory")

                except ValueError:
                    raise Exception("Fatal Error -- offset value not valid integer")

        #temporary for debugging purposes
        #memManager.memoryDump()

    #function to move (copy) a value from one register to another
    def Move(self):
        #get the two registers in question
        dest: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0])
        src: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1])

        #set the dest value to the src value
        try:
            if isinstance(src.value, int):
                dest.value = src.value
            else:
                dest.value = int(src.value, 10)
        except:
            dest.value = int(str(src.value), 16)

    #function to add two registers (or immediates) and place the result in a register
    def Add(self):
        #get the destination register
        dest: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0])

        #init beforehand
        value_1: int = 0
        value_2: int = 0

        #determine if the second parameter is an immediate or a register
        if(self.IsRegister(str(self.lines[self.regFile.ProgramCounter].parameters[1])) or self.lines[self.regFile.ProgramCounter].parameters[1] == "$zero"):
            try:
                if (isinstance(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1]), FloatRegister)):
                    raise ValueError
                value_1 = int(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1]).value)
            except ValueError:
                raise Exception("Fatal Error -- register value was not an integer")
        else:
            try:
                self.lines[self.regFile.ProgramCounter].parameters[1] = int(self.lines[self.regFile.ProgramCounter].parameters[1])
                if(not isinstance(self.lines[self.regFile.ProgramCounter].parameters[1], int)):
                    raise ValueError()
                value_1 = int(self.lines[self.regFile.ProgramCounter].parameters[1])
            except ValueError:
                raise Exception("Fatal Error -- immediate value was not an integer")

        #determine if the third parameter is an immediate or a register
        if (self.IsRegister(str(self.lines[self.regFile.ProgramCounter].parameters[2])) or self.lines[self.regFile.ProgramCounter].parameters[2] == "$zero"):
            try:
                if (isinstance(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[2]), FloatRegister)):
                    raise ValueError
                value_2 = int(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[2]).value)
            except ValueError:
                raise Exception("Fatal Error -- register value was not an integer")
        else:
            try:
                self.lines[self.regFile.ProgramCounter].parameters[2] = int(self.lines[self.regFile.ProgramCounter].parameters[2])
                if (not isinstance(self.lines[self.regFile.ProgramCounter].parameters[2], int)):
                    raise ValueError()
                value_2 = int(self.lines[self.regFile.ProgramCounter].parameters[2])
            except ValueError:
                raise Exception("Fatal Error -- immediate value was not an integer")

        #set the destination register's value to the addition of those two values
        dest.value = value_1 + value_2

    #function to subtract two registers (or immediates) and place the result in a register
    def Sub(self):
        #get the destination register
        dest: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0])

        #init beforehand
        value_1: int = 0
        value_2: int = 0

        #determine if the second parameter is an immediate or a register
        if(self.IsRegister(str(self.lines[self.regFile.ProgramCounter].parameters[1])) or self.lines[self.regFile.ProgramCounter].parameters[1] == "$zero"):
            try:
                if (isinstance(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1]), FloatRegister)):
                    raise ValueError
                value_1 = int(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1]).value)
            except ValueError:
                raise Exception("Fatal Error -- register value was not an integer")
        else:
            try:
                self.lines[self.regFile.ProgramCounter].parameters[1] = int(self.lines[self.regFile.ProgramCounter].parameters[1])
                if(not isinstance(self.lines[self.regFile.ProgramCounter].parameters[1], int)):
                    raise ValueError()
                value_1 = int(self.lines[self.regFile.ProgramCounter].parameters[1])
            except ValueError:
                raise Exception("Fatal Error -- immediate value was not an integer")

        #determine if the third parameter is an immediate or a register
        if (self.IsRegister(str(self.lines[self.regFile.ProgramCounter].parameters[2])) or self.lines[self.regFile.ProgramCounter].parameters[2] == "$zero"):
            try:
                if (isinstance(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[2]), FloatRegister)):
                    raise ValueError
                value_2 = int(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[2]).value)
            except ValueError:
                raise Exception("Fatal Error -- register value was not an integer")
        else:
            try:
                self.lines[self.regFile.ProgramCounter].parameters[2] = int(self.lines[self.regFile.ProgramCounter].parameters[2])
                if (not isinstance(self.lines[self.regFile.ProgramCounter].parameters[2], int)):
                    raise ValueError()
                value_2 = int(self.lines[self.regFile.ProgramCounter].parameters[2])
            except ValueError:
                raise Exception("Fatal Error -- immediate value was not an integer")

        #set the destination register's value to the addition of those two values
        dest.value = value_1 - value_2

    #function to multiply two registers (or immediates) and place the result in a register
    def Mul(self):
        #get the destination register
        dest: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0])

        #init beforehand
        value_1: int = 0
        value_2: int = 0

        #determine if the second parameter is an immediate or a register
        if (self.IsRegister(str(self.lines[self.regFile.ProgramCounter].parameters[1])) or self.lines[self.regFile.ProgramCounter].parameters[1] == "$zero"):
           try:
                if (isinstance(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1]), FloatRegister)):
                    raise ValueError
                value_1 = int(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1]).value)
           except ValueError:
                raise Exception("Fatal Error -- register value was not an integer")
        else:
            try:
                self.lines[self.regFile.ProgramCounter].parameters[1] = int(self.lines[self.regFile.ProgramCounter].parameters[1])
                if (not isinstance(self.lines[self.regFile.ProgramCounter].parameters[1], int)):
                    raise ValueError()
                value_1 = int(self.lines[self.regFile.ProgramCounter].parameters[1])
            except ValueError:
                raise Exception("Fatal Error -- immediate value was not an integer")

        #determine if the third parameter is an immediate or a register
        if (self.IsRegister(str(self.lines[self.regFile.ProgramCounter].parameters[2])) or self.lines[self.regFile.ProgramCounter].parameters[2] == "$zero"):
            try:
                if (isinstance(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[2]), FloatRegister)):
                    raise ValueError
                value_2 = int(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[2]).value)
            except ValueError:
                raise Exception("Fatal Error -- register value was not an integer")
        else:
            try:
                self.lines[self.regFile.ProgramCounter].parameters[2] = int(self.lines[self.regFile.ProgramCounter].parameters[2])
                if (not isinstance(self.lines[self.regFile.ProgramCounter].parameters[2], int)):
                    raise ValueError()
                value_2 = int(self.lines[self.regFile.ProgramCounter].parameters[2])
            except ValueError:
                raise Exception("Fatal Error -- immediate value was not an integer")

        #set the destination register's value to the addition of those two values
        dest.value = value_1 * value_2

    #function to multiply two registers (or immediates) and place the results into the hi and lo registers
    def Mult(self):
        #init beforehand
        value_1: int = 0
        value_2: int = 0

        #determine if the second parameter is an immediate or a register
        if (self.IsRegister(str(self.lines[self.regFile.ProgramCounter].parameters[1])) or self.lines[self.regFile.ProgramCounter].parameters[1] == "$zero"):
            try:
                if (isinstance(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1]), FloatRegister)):
                    raise ValueError
                value_1 = int(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1]).value)
            except ValueError:
                raise Exception("Fatal Error -- register value was not an integer")
        else:
            try:
                self.lines[self.regFile.ProgramCounter].parameters[1] = int(
                    self.lines[self.regFile.ProgramCounter].parameters[1])
                if (not isinstance(self.lines[self.regFile.ProgramCounter].parameters[1], int)):
                    raise ValueError()
                value_1 = int(self.lines[self.regFile.ProgramCounter].parameters[1])
            except ValueError:
                raise Exception("Fatal Error -- immediate value was not an integer")

        #determine if the third parameter is an immediate or a register
        if (self.IsRegister(str(self.lines[self.regFile.ProgramCounter].parameters[2])) or self.lines[self.regFile.ProgramCounter].parameters[2] == "$zero"):
            try:
                if (isinstance(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[2]), FloatRegister)):
                    raise ValueError
                value_2 = int(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[2]).value)
            except ValueError:
                raise Exception("Fatal Error -- register value was not an integer")
        else:
            try:
                self.lines[self.regFile.ProgramCounter].parameters[2] = int(self.lines[self.regFile.ProgramCounter].parameters[2])
                if (not isinstance(self.lines[self.regFile.ProgramCounter].parameters[2], int)):
                    raise ValueError()
                value_2 = int(self.lines[self.regFile.ProgramCounter].parameters[2])
            except ValueError:
                raise Exception("Fatal Error -- immediate value was not an integer")

        #get the binary string value (for the registers)
        value: str = str(bin(value_1 * value_2)[2:])
        while(len(value) < 64):
            value = '0' + value

        #get the lower 32 for lo and the upper 32 for hi
        self.regFile.LO.value = int(value[:32], 2)
        self.regFile.HI.value = int(value[32:], 2)

    #function to divide two registers (or immediates) and place the results into the hi and lo registers, and result into dest if applicable
    def Div(self):
        #if we have three parameters
        if(len(self.lines[self.regFile.ProgramCounter].parameters) == 3):
            #get the destination register
            dest: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0])

            #init beforehand
            value_1: int = 0
            value_2: int = 0

            #determine if the second parameter is an immediate or a register
            if (self.IsRegister(str(self.lines[self.regFile.ProgramCounter].parameters[1])) or self.lines[self.regFile.ProgramCounter].parameters[1] == "$zero"):
                try:
                    if (isinstance(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1]), FloatRegister)):
                        raise ValueError
                    value_1 = int(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1]).value)
                except ValueError:
                    raise Exception("Fatal Error -- register value was not an integer")
            else:
                try:
                    self.lines[self.regFile.ProgramCounter].parameters[1] = int(self.lines[self.regFile.ProgramCounter].parameters[1])
                    if (not isinstance(self.lines[self.regFile.ProgramCounter].parameters[1], int)):
                        raise ValueError()
                    value_1 = int(self.lines[self.regFile.ProgramCounter].parameters[1])
                except ValueError:
                    raise Exception("Fatal Error -- immediate value was not an integer")

            #determine if the third parameter is an immediate or a register
            if (self.IsRegister(str(self.lines[self.regFile.ProgramCounter].parameters[2])) or self.lines[self.regFile.ProgramCounter].parameters[2] == "$zero"):
                try:
                    if (isinstance(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[2]), FloatRegister)):
                        raise ValueError
                    value_2 = int(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[2]).value)
                except ValueError:
                    raise Exception("Fatal Error -- register value was not an integer")
            else:
                try:
                    self.lines[self.regFile.ProgramCounter].parameters[2] = int(self.lines[self.regFile.ProgramCounter].parameters[2])
                    if (not isinstance(self.lines[self.regFile.ProgramCounter].parameters[2], int)):
                        raise ValueError()
                    value_2 = int(self.lines[self.regFile.ProgramCounter].parameters[2])
                except ValueError:
                    raise Exception("Fatal Error -- immediate value was not an integer")

            # set the destination registers' value to the addition of those two values
            self.regFile.HI.value = value_1 % value_2
            self.regFile.LO.value = value_1 // value_2
            dest.value = self.regFile.LO.value
        #otherwise if we have 2 parameters
        else:
            #init beforehand
            value_1: int = 0
            value_2: int = 0

            #determine if the second parameter is an immediate or a register
            if (self.IsRegister(str(self.lines[self.regFile.ProgramCounter].parameters[0])) or self.lines[self.regFile.ProgramCounter].parameters[0] == "$zero"):
                try:
                    if (isinstance(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1]), FloatRegister)):
                        raise ValueError
                    value_1 = int(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0]).value)
                except ValueError:
                    raise Exception("Fatal Error -- register value was not an integer")
            else:
                try:
                    self.lines[self.regFile.ProgramCounter].parameters[1] = int(self.lines[self.regFile.ProgramCounter].parameters[1])
                    if (not isinstance(self.lines[self.regFile.ProgramCounter].parameters[0], int)):
                        raise ValueError()
                    value_1 = int(self.lines[self.regFile.ProgramCounter].parameters[1])
                except ValueError:
                    raise Exception("Fatal Error -- immediate value was not an integer")

            #determine if the third parameter is an immediate or a register
            if (self.IsRegister(str(self.lines[self.regFile.ProgramCounter].parameters[1])) or self.lines[self.regFile.ProgramCounter].parameters[1] == "$zero"):
                try:
                    if (isinstance(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1]), FloatRegister)):
                        raise ValueError
                    value_2 = int(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1]).value)
                except ValueError:
                    raise Exception("Fatal Error -- register value was not an integer")
            else:
                try:
                    self.lines[self.regFile.ProgramCounter].parameters[1] = int(self.lines[self.regFile.ProgramCounter].parameters[1])
                    if (not isinstance(self.lines[self.regFile.ProgramCounter].parameters[1], int)):
                        raise ValueError()
                    value_2 = int(self.lines[self.regFile.ProgramCounter].parameters[1])
                    if(value_2 == 0):
                        raise Exception("Fatal Error -- divide by zero is NaN")
                except ValueError:
                    raise Exception("Fatal Error -- immediate value was not an integer")

            #set the destination registers' value to the addition of those two values
            self.regFile.HI.value = value_1 % value_2
            self.regFile.LO.value = value_1 // value_2

    #function to jump (j) to the line number of the label
    def J(self):
        #see if the label exists, if so get its lineNumber
        jumpTo: int = -1
        for i in range(len(self.segments)):
            if(self.segments[i].segment == self.lines[self.regFile.ProgramCounter].parameters[0]):
                jumpTo = self.segments[i].lineNumber
                break

        if(jumpTo == -1):
            raise Exception("Fatal Error -- Jump to unknown segment was found")

        self.regFile.ProgramCounter = jumpTo

    #function to branch to the label if the registers (or immediates) are equal
    def BranchIfEqual(self):
        #see if the label exists, if so get its lineNumber
        jumpTo: int = -1
        for i in range(len(self.segments)):
            if (self.segments[i].segment == self.lines[self.regFile.ProgramCounter].parameters[2]):
                jumpTo = self.segments[i].lineNumber
                break

        if (jumpTo == -1):
            raise Exception("Fatal Error -- Jump to unknown segment was found at line:", self.lines[self.regFile.ProgramCounter].globalLineNumber)

        #see if the two values are equal
        # init beforehand
        value_1: int = 0
        value_2: int = 0

        #determine if the second parameter is an immediate or a register
        if (self.IsRegister(str(self.lines[self.regFile.ProgramCounter].parameters[0])) or self.lines[self.regFile.ProgramCounter].parameters[0] == "$zero"):
            try:
                value_1 = int(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0]).value)
            except ValueError:
                raise Exception("Fatal Error -- register value was not an integer")
        else:
            try:
                self.lines[self.regFile.ProgramCounter].parameters[1] = int(self.lines[self.regFile.ProgramCounter].parameters[1])
                if (not isinstance(self.lines[self.regFile.ProgramCounter].parameters[0], int)):
                    raise ValueError()
                value_1 = int(self.lines[self.regFile.ProgramCounter].parameters[1])
            except ValueError:
                raise Exception("Fatal Error -- immediate value was not an integer")

        #determine if the third parameter is an immediate or a register
        if (self.IsRegister(str(self.lines[self.regFile.ProgramCounter].parameters[1])) or self.lines[self.regFile.ProgramCounter].parameters[1] == "$zero"):
            try:
                value_2 = int(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1]).value)
            except ValueError:
                raise Exception("Fatal Error -- register value was not an integer")
        else:
            try:
                self.lines[self.regFile.ProgramCounter].parameters[1] = int(self.lines[self.regFile.ProgramCounter].parameters[1])
                if (not isinstance(self.lines[self.regFile.ProgramCounter].parameters[1], int)):
                    raise ValueError()
                value_2 = int(self.lines[self.regFile.ProgramCounter].parameters[1])
            except ValueError:
                raise Exception("Fatal Error -- immediate value was not an integer")

        if(value_1 == value_2):
            self.regFile.ProgramCounter = jumpTo
        else: #otherwise go to the next instruction
            self.regFile.ProgramCounter += 1

    #function to set the register to 1 if left is greater than right, 0 otherwise
    def SetGreaterThan(self):
        #get the dest. register
        dest: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0])

        #see if the two values are equal
        #init beforehand
        value_1: int = 0
        value_2: int = 0

        #determine if the second parameter is an immediate or a register
        if (self.IsRegister(str(self.lines[self.regFile.ProgramCounter].parameters[1])) or self.lines[self.regFile.ProgramCounter].parameters[1] == "$zero"):
            try:
                value_1 = int(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1]).value)
            except ValueError:
                raise Exception("Fatal Error -- register value was not an integer")
        else:
            try:
                self.lines[self.regFile.ProgramCounter].parameters[1] = int(
                    self.lines[self.regFile.ProgramCounter].parameters[1])
                if (not isinstance(self.lines[self.regFile.ProgramCounter].parameters[1], int)):
                    raise ValueError()
                value_1 = int(self.lines[self.regFile.ProgramCounter].parameters[1])
            except ValueError:
                raise Exception("Fatal Error -- immediate value was not an integer")

        #determine if the third parameter is an immediate or a register
        if (self.IsRegister(str(self.lines[self.regFile.ProgramCounter].parameters[2])) or self.lines[self.regFile.ProgramCounter].parameters[2] == "$zero"):
            try:
                value_2 = int(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[2]).value)
            except ValueError:
                raise Exception("Fatal Error -- register value was not an integer")
        else:
            try:
                self.lines[self.regFile.ProgramCounter].parameters[2] = int(self.lines[self.regFile.ProgramCounter].parameters[2])
                if (not isinstance(self.lines[self.regFile.ProgramCounter].parameters[2], int)):
                    raise ValueError()
                value_2 = int(self.lines[self.regFile.ProgramCounter].parameters[2])
            except ValueError:
                raise Exception("Fatal Error -- immediate value was not an integer")

        if (value_1 > value_2):
            dest.value = 1
        else:
            dest.value = 0

    #function to set the register to 1 if left is greater than right, 0 otherwise
    def SetEqual(self):
        #get the dest. register
        dest: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0])

        #see if the two values are equal
        #init beforehand
        value_1: int = 0
        value_2: int = 0

        #determine if the second parameter is an immediate or a register
        if (self.IsRegister(str(self.lines[self.regFile.ProgramCounter].parameters[1])) or self.lines[self.regFile.ProgramCounter].parameters[1] == "$zero"):
            try:
                value_1 = int(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1]).value)
            except ValueError:
                raise Exception("Fatal Error -- register value was not an integer")
        else:
            try:
                self.lines[self.regFile.ProgramCounter].parameters[1] = int( self.lines[self.regFile.ProgramCounter].parameters[1])
                if (not isinstance(self.lines[self.regFile.ProgramCounter].parameters[1], int)):
                    raise ValueError()
                value_1 = int(self.lines[self.regFile.ProgramCounter].parameters[1])
            except ValueError:
                raise Exception("Fatal Error -- immediate value was not an integer")

        #determine if the third parameter is an immediate or a register
        if (self.IsRegister(str(self.lines[self.regFile.ProgramCounter].parameters[2])) or self.lines[self.regFile.ProgramCounter].parameters[2] == "$zero"):
            try:
                value_2 = int(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[2]).value)
            except ValueError:
                raise Exception("Fatal Error -- register value was not an integer")
        else:
            try:
                self.lines[self.regFile.ProgramCounter].parameters[2] = int(
                    self.lines[self.regFile.ProgramCounter].parameters[2])
                if (not isinstance(self.lines[self.regFile.ProgramCounter].parameters[2], int)):
                    raise ValueError()
                value_2 = int(self.lines[self.regFile.ProgramCounter].parameters[2])
            except ValueError:
                raise Exception("Fatal Error -- immediate value was not an integer")

        if (value_1 == value_2):
            dest.value = 1
        else:
            dest.value = 0

    #function to branch to the label if the register (or immediate) is equal to 0
    def BranchIfEqualZero(self):
        #see if the label exists, if so get its lineNumber
        jumpTo: int = -1
        for i in range(len(self.segments)):
            if (self.segments[i].segment == self.lines[self.regFile.ProgramCounter].parameters[1]):
                jumpTo = self.segments[i].lineNumber
                break

        if (jumpTo == -1):
            raise Exception("Fatal Error -- Jump to unknown segment was found")

        #see if the value is 0
        #init beforehand
        value_1: int = 0

        #determine if the second parameter is an immediate or a register
        if (self.IsRegister(str(self.lines[self.regFile.ProgramCounter].parameters[0])) or self.lines[self.regFile.ProgramCounter].parameters[0] == "$zero"):
            try:
                value_1 = int(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0]).value)
            except ValueError:
                raise Exception("Fatal Error -- register value was not an integer")
        else:
            try:
                self.lines[self.regFile.ProgramCounter].parameters[1] = int(self.lines[self.regFile.ProgramCounter].parameters[1])
                if (not isinstance(self.lines[self.regFile.ProgramCounter].parameters[0], int)):
                    raise ValueError()
                value_1 = int(self.lines[self.regFile.ProgramCounter].parameters[1])
            except ValueError:
                raise Exception("Fatal Error -- immediate value was not an integer")

        if (value_1 == 0):
            self.regFile.ProgramCounter = jumpTo
        else: #otherwise go to the next instruction
            self.regFile.ProgramCounter += 1


    #function to jump and link the $ra to the line number of the label
    def JumpAndLink(self):
        #see if the label exists, if so get its lineNumber
        jumpTo: int = -1
        for i in range(len(self.segments)):
            if(self.segments[i].segment == self.lines[self.regFile.ProgramCounter].parameters[0]):
                jumpTo = self.segments[i].lineNumber
                break

        if(jumpTo == -1):
            raise Exception("Fatal Error -- Jump to unknown segment was found")

        self.regFile.RA.value = self.regFile.ProgramCounter + 1 #the next line after this one (so that it runs immediately)
        self.regFile.ProgramCounter = jumpTo

    #function to jump and link the $ra to the line number of the label
    def JumpRegister(self):
        #get the parameter register
        jumpTo: int = -1
        link: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0])
        jumpTo = link.value

        if(jumpTo <= 0 or jumpTo > len(self.lines)): #validation
            raise Exception("Fatal Error -- Jump to unknown line was found")

        self.regFile.RA.value = self.regFile.ProgramCounter + 1 #the next line after this one (so that it runs immediately)
        self.regFile.ProgramCounter = jumpTo

    #function to branch to the label if the left register is less than the right register
    def BranchIfLessThan(self):
        #see if the label exists, if so get its lineNumber
        jumpTo: int = -1
        for i in range(len(self.segments)):
            if (self.segments[i].segment == self.lines[self.regFile.ProgramCounter].parameters[2]):
                jumpTo = self.segments[i].lineNumber
                break

        if (jumpTo == -1):
            raise Exception("Fatal Error -- Jump to unknown segment was found")

        #see if the two values are equal
        # init beforehand
        value_1: int = 0
        value_2: int = 0

        #determine if the second parameter is an immediate or a register
        if (self.IsRegister(str(self.lines[self.regFile.ProgramCounter].parameters[0])) or self.lines[self.regFile.ProgramCounter].parameters[0] == "$zero"):
            try:
                value_1 = int(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0]).value)
            except ValueError:
                raise Exception("Fatal Error -- register value was not an integer")
        else:
            try:
                self.lines[self.regFile.ProgramCounter].parameters[1] = int(self.lines[self.regFile.ProgramCounter].parameters[1])
                if (not isinstance(self.lines[self.regFile.ProgramCounter].parameters[0], int)):
                    raise ValueError()
                value_1 = int(self.lines[self.regFile.ProgramCounter].parameters[1])
            except ValueError:
                raise Exception("Fatal Error -- immediate value was not an integer")

        #determine if the third parameter is an immediate or a register
        if (self.IsRegister(str(self.lines[self.regFile.ProgramCounter].parameters[1])) or self.lines[self.regFile.ProgramCounter].parameters[1] == "$zero"):
            try:
                value_2 = int(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1]).value)
            except ValueError:
                raise Exception("Fatal Error -- register value was not an integer")
        else:
            try:
                self.lines[self.regFile.ProgramCounter].parameters[1] = int(self.lines[self.regFile.ProgramCounter].parameters[1])
                if (not isinstance(self.lines[self.regFile.ProgramCounter].parameters[1], int)):
                    raise ValueError()
                value_2 = int(self.lines[self.regFile.ProgramCounter].parameters[1])
            except ValueError:
                raise Exception("Fatal Error -- immediate value was not an integer")

        if(value_1 < value_2):
            self.regFile.ProgramCounter = jumpTo
        else: #otherwise go to the next instruction
            self.regFile.ProgramCounter += 1

    #function to branch to the label if the left register is greater than the right register
    def BranchIfGreaterThan(self):
        #see if the label exists, if so get its lineNumber
        jumpTo: int = -1
        for i in range(len(self.segments)):
            if (self.segments[i].segment == self.lines[self.regFile.ProgramCounter].parameters[2]):
                jumpTo = self.segments[i].lineNumber
                break

        if (jumpTo == -1):
            raise Exception("Fatal Error -- Jump to unknown segment was found")

        #see if the two values are equal
        # init beforehand
        value_1: int = 0
        value_2: int = 0

        #determine if the second parameter is an immediate or a register
        if (self.IsRegister(str(self.lines[self.regFile.ProgramCounter].parameters[0])) or self.lines[self.regFile.ProgramCounter].parameters[0] == "$zero"):
            try:
                value_1 = int(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0]).value)
            except ValueError:
                raise Exception("Fatal Error -- register value was not an integer")
        else:
            try:
                self.lines[self.regFile.ProgramCounter].parameters[1] = int(self.lines[self.regFile.ProgramCounter].parameters[1])
                if (not isinstance(self.lines[self.regFile.ProgramCounter].parameters[0], int)):
                    raise ValueError()
                value_1 = int(self.lines[self.regFile.ProgramCounter].parameters[1])
            except ValueError:
                raise Exception("Fatal Error -- immediate value was not an integer")

        #determine if the third parameter is an immediate or a register
        if (self.IsRegister(str(self.lines[self.regFile.ProgramCounter].parameters[1])) or self.lines[self.regFile.ProgramCounter].parameters[1] == "$zero"):
            try:
                value_2 = int(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1]).value)
            except ValueError:
                raise Exception("Fatal Error -- register value was not an integer")
        else:
            try:
                self.lines[self.regFile.ProgramCounter].parameters[1] = int(self.lines[self.regFile.ProgramCounter].parameters[1])
                if (not isinstance(self.lines[self.regFile.ProgramCounter].parameters[1], int)):
                    raise ValueError()
                value_2 = int(self.lines[self.regFile.ProgramCounter].parameters[1])
            except ValueError:
                raise Exception("Fatal Error -- immediate value was not an integer")

        if(value_1 > value_2):
            self.regFile.ProgramCounter = jumpTo
        else: #otherwise go to the next instruction
            self.regFile.ProgramCounter += 1

    #function to branch to the label if the left register is greater than or equal to the right register
    def BranchIfGreaterThanEqual(self):
        #see if the label exists, if so get its lineNumber
        jumpTo: int = -1
        for i in range(len(self.segments)):
            if (self.segments[i].segment == self.lines[self.regFile.ProgramCounter].parameters[2]):
                jumpTo = self.segments[i].lineNumber
                break

        if (jumpTo == -1):
            raise Exception("Fatal Error -- Jump to unknown segment was found")

        #see if the two values are equal
        # init beforehand
        value_1: int = 0
        value_2: int = 0

        #determine if the second parameter is an immediate or a register
        if (self.IsRegister(str(self.lines[self.regFile.ProgramCounter].parameters[0])) or self.lines[self.regFile.ProgramCounter].parameters[0] == "$zero"):
            try:
                value_1 = int(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0]).value)
            except ValueError:
                raise Exception("Fatal Error -- register value was not an integer")
        else:
            try:
                self.lines[self.regFile.ProgramCounter].parameters[1] = int(self.lines[self.regFile.ProgramCounter].parameters[1])
                if (not isinstance(self.lines[self.regFile.ProgramCounter].parameters[0], int)):
                    raise ValueError()
                value_1 = int(self.lines[self.regFile.ProgramCounter].parameters[1])
            except ValueError:
                raise Exception("Fatal Error -- immediate value was not an integer")

        #determine if the third parameter is an immediate or a register
        if (self.IsRegister(str(self.lines[self.regFile.ProgramCounter].parameters[1])) or self.lines[self.regFile.ProgramCounter].parameters[1] == "$zero"):
            try:
                value_2 = int(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1]).value)
            except ValueError:
                raise Exception("Fatal Error -- register value was not an integer")
        else:
            try:
                self.lines[self.regFile.ProgramCounter].parameters[1] = int(self.lines[self.regFile.ProgramCounter].parameters[1])
                if (not isinstance(self.lines[self.regFile.ProgramCounter].parameters[1], int)):
                    raise ValueError()
                value_2 = int(self.lines[self.regFile.ProgramCounter].parameters[1])
            except ValueError:
                raise Exception("Fatal Error -- immediate value was not an integer")

        if(value_1 >= value_2):
            self.regFile.ProgramCounter = jumpTo
        else: #otherwise go to the next instruction
            self.regFile.ProgramCounter += 1

    #function to branch to the label if the left register is less than or equal to the right register
    def BranchIfLessThanEqual(self):
        #see if the label exists, if so get its lineNumber
        jumpTo: int = -1
        for i in range(len(self.segments)):
            if (self.segments[i].segment == self.lines[self.regFile.ProgramCounter].parameters[2]):
                jumpTo = self.segments[i].lineNumber
                break

        if (jumpTo == -1):
            raise Exception("Fatal Error -- Jump to unknown segment was found")

        #see if the two values are equal
        # init beforehand
        value_1: int = 0
        value_2: int = 0

        #determine if the second parameter is an immediate or a register
        if (self.IsRegister(str(self.lines[self.regFile.ProgramCounter].parameters[0])) or self.lines[self.regFile.ProgramCounter].parameters[0] == "$zero"):
            try:
                value_1 = int(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0]).value)
            except ValueError:
                raise Exception("Fatal Error -- register value was not an integer")
        else:
            try:
                self.lines[self.regFile.ProgramCounter].parameters[1] = int(self.lines[self.regFile.ProgramCounter].parameters[1])
                if (not isinstance(self.lines[self.regFile.ProgramCounter].parameters[0], int)):
                    raise ValueError()
                value_1 = int(self.lines[self.regFile.ProgramCounter].parameters[1])
            except ValueError:
                raise Exception("Fatal Error -- immediate value was not an integer")

        #determine if the third parameter is an immediate or a register
        if (self.IsRegister(str(self.lines[self.regFile.ProgramCounter].parameters[1])) or self.lines[self.regFile.ProgramCounter].parameters[1] == "$zero"):
            try:
                value_2 = int(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1]).value)
            except ValueError:
                raise Exception("Fatal Error -- register value was not an integer")
        else:
            try:
                self.lines[self.regFile.ProgramCounter].parameters[1] = int(self.lines[self.regFile.ProgramCounter].parameters[1])
                if (not isinstance(self.lines[self.regFile.ProgramCounter].parameters[1], int)):
                    raise ValueError()
                value_2 = int(self.lines[self.regFile.ProgramCounter].parameters[1])
            except ValueError:
                raise Exception("Fatal Error -- immediate value was not an integer")

        if(value_1 <= value_2):
            self.regFile.ProgramCounter = jumpTo
        else: #otherwise go to the next instruction
            self.regFile.ProgramCounter += 1

    #function to branch to the label if the register (or immediate) is greater than 0
    def BranchIfGreaterThanZero(self):
        #see if the label exists, if so get its lineNumber
        jumpTo: int = -1
        for i in range(len(self.segments)):
            if (self.segments[i].segment == self.lines[self.regFile.ProgramCounter].parameters[1]):
                jumpTo = self.segments[i].lineNumber
                break

        if (jumpTo == -1):
            raise Exception("Fatal Error -- Jump to unknown segment was found")

        #see if the value is 0
        #init beforehand
        value_1: int = 0

        #determine if the second parameter is an immediate or a register
        if (self.IsRegister(str(self.lines[self.regFile.ProgramCounter].parameters[0])) or self.lines[self.regFile.ProgramCounter].parameters[0] == "$zero"):
            try:
                value_1 = int(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0]).value)
            except ValueError:
                raise Exception("Fatal Error -- register value was not an integer")
        else:
            try:
                self.lines[self.regFile.ProgramCounter].parameters[1] = int(self.lines[self.regFile.ProgramCounter].parameters[1])
                if (not isinstance(self.lines[self.regFile.ProgramCounter].parameters[0], int)):
                    raise ValueError()
                value_1 = int(self.lines[self.regFile.ProgramCounter].parameters[1])
            except ValueError:
                raise Exception("Fatal Error -- immediate value was not an integer")

        if (value_1 > 0):
            self.regFile.ProgramCounter = jumpTo
        else: #otherwise go to the next instruction
            self.regFile.ProgramCounter += 1

    #function to branch to the label if the value in the register is not equal to zero
    def BranchIfNotEqualZero(self):
        #see if the label exists, if so get its lineNumber
        jumpTo: int = -1
        for i in range(len(self.segments)):
            if (self.segments[i].segment == self.lines[self.regFile.ProgramCounter].parameters[1]):
                jumpTo = self.segments[i].lineNumber
                break

        if (jumpTo == -1):
            raise Exception("Fatal Error -- Jump to unknown segment was found")

        #see if the value is 0
        #init beforehand
        value_1: int = 0

        #determine if the second parameter is an immediate or a register
        if (self.IsRegister(str(self.lines[self.regFile.ProgramCounter].parameters[0])) or self.lines[self.regFile.ProgramCounter].parameters[0] == "$zero"):
            try:
                value_1 = int(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0]).value)
            except ValueError:
                raise Exception("Fatal Error -- register value was not an integer")
        else:
            try:
                self.lines[self.regFile.ProgramCounter].parameters[1] = int(self.lines[self.regFile.ProgramCounter].parameters[1])
                if (not isinstance(self.lines[self.regFile.ProgramCounter].parameters[0], int)):
                    raise ValueError()
                value_1 = int(self.lines[self.regFile.ProgramCounter].parameters[1])
            except ValueError:
                raise Exception("Fatal Error -- immediate value was not an integer")

        if (value_1 != 0):
            self.regFile.ProgramCounter = jumpTo
        else: #otherwise go to the next instruction
            self.regFile.ProgramCounter += 1

    #function to branch to the label if the register (or immediate) is less than 0
    def BranchIfLessThanZero(self):
        #see if the label exists, if so get its lineNumber
        jumpTo: int = -1
        for i in range(len(self.segments)):
            if (self.segments[i].segment == self.lines[self.regFile.ProgramCounter].parameters[1]):
                jumpTo = self.segments[i].lineNumber
                break

        if (jumpTo == -1):
            raise Exception("Fatal Error -- Jump to unknown segment was found")

        #see if the value is 0
        #init beforehand
        value_1: int = 0

        #determine if the second parameter is an immediate or a register
        if (self.IsRegister(str(self.lines[self.regFile.ProgramCounter].parameters[0])) or self.lines[self.regFile.ProgramCounter].parameters[0] == "$zero"):
            try:
                value_1 = int(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0]).value)
            except ValueError:
                raise Exception("Fatal Error -- register value was not an integer")
        else:
            try:
                self.lines[self.regFile.ProgramCounter].parameters[1] = int(self.lines[self.regFile.ProgramCounter].parameters[1])
                if (not isinstance(self.lines[self.regFile.ProgramCounter].parameters[0], int)):
                    raise ValueError()
                value_1 = int(self.lines[self.regFile.ProgramCounter].parameters[1])
            except ValueError:
                raise Exception("Fatal Error -- immediate value was not an integer")

        if (value_1 < 0):
            self.regFile.ProgramCounter = jumpTo
        else: #otherwise go to the next instruction
            self.regFile.ProgramCounter += 1

    #function to branch to a label if the flag of coproc 1 is set true
    def BranchIfCoprocFlagTrue(self):
        #see if the label exists, if so get its lineNumber
        jumpTo: int = -1
        for i in range(len(self.segments)):
            if(self.segments[i].segment == self.lines[self.regFile.ProgramCounter].parameters[0]):
                jumpTo = self.segments[i].lineNumber
                break

        if(jumpTo == -1):
            raise Exception("Fatal Error -- Jump to unknown segment was found")

        if(self.regFile.Fcc):
            self.regFile.ProgramCounter = jumpTo
        else: #otherwise go to the next instruction
            self.regFile.ProgramCounter += 1

    #function to perform add immediate
    def AddImmediate(self):
        #get the destination register
        dest: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0])

        #init beforehand
        value_1: int = 0
        value_2: int = 0

        #determine if the second parameter is a valid register
        if (self.IsRegister(str(self.lines[self.regFile.ProgramCounter].parameters[1])) or self.lines[self.regFile.ProgramCounter].parameters[1] == "$zero"):
            try:
                if(isinstance(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1]), FloatRegister)):
                    raise ValueError
                value_1 = int(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1]).value)
            except ValueError:
                raise Exception("Fatal Error -- register value was not an integer")

        #determine if the third parameter is a valid immediate
        if (self.IsRegister(str(self.lines[self.regFile.ProgramCounter].parameters[2])) or self.lines[self.regFile.ProgramCounter].parameters[2] == "$zero"):
            raise Exception("Fatal Error -- addi third parameter must be an integer")
        else:
            try:
                self.lines[self.regFile.ProgramCounter].parameters[2] = int(self.lines[self.regFile.ProgramCounter].parameters[2])
                if (not isinstance(self.lines[self.regFile.ProgramCounter].parameters[2], int)):
                    raise ValueError()
                value_2 = int(self.lines[self.regFile.ProgramCounter].parameters[2])
            except ValueError:
                raise Exception("Fatal Error -- immediate value was not an integer")

        #set the destination register's value to the addition of those two values
        dest.value = value_1 + value_2

    #function to perform sub immediate
    def SubImmediate(self):
        #get the destination register
        dest: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0])

        # init beforehand
        value_1: int = 0
        value_2: int = 0

        #determine if the second parameter is a valid register
        if (self.IsRegister(str(self.lines[self.regFile.ProgramCounter].parameters[1])) or self.lines[self.regFile.ProgramCounter].parameters[1] == "$zero"):
            try:
                if (isinstance(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1]), FloatRegister)):
                    raise ValueError
                value_1 = int(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1]).value)
            except ValueError:
                raise Exception("Fatal Error -- register value was not an integer")

        #determine if the third parameter is a valid immediate
        if (self.IsRegister(str(self.lines[self.regFile.ProgramCounter].parameters[2])) or self.lines[self.regFile.ProgramCounter].parameters[2] == "$zero"):
            raise Exception("Fatal Error -- subi third parameter must be an integer")
        else:
            try:
                self.lines[self.regFile.ProgramCounter].parameters[2] = int(self.lines[self.regFile.ProgramCounter].parameters[2])
                if (not isinstance(self.lines[self.regFile.ProgramCounter].parameters[2], int)):
                    raise ValueError()
                value_2 = int(self.lines[self.regFile.ProgramCounter].parameters[2])
            except ValueError:
                raise Exception("Fatal Error -- immediate value was not an integer")

        #set the destination register's value to the addition of those two values
        dest.value = value_1 - value_2

    #function to perform move from register hi
    def MoveFromHi(self):
        #get the register in question
        dest: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0])

        #set the dest value to the hi value
        dest.value = int(self.regFile.HI.value)

    #function to perform move from register lo
    def MoveFromLo(self):
        #get the register in question
        dest: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0])

        #set the dest value to the hi value
        dest.value = int(self.regFile.LO.value)

    #function to perform load single precision
    def LoadSinglePrecision(self):
        self.LoadWordCoproc() #these act the same, one is just lower level (hence why it is called directly here)

    #function to perform load word coproc 1
    def LoadWordCoproc(self):
        memManager: MemoryManager._MemoryManagerImpl = MemoryManager()

        #get the dest. register
        dest: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0])
        if(not isinstance(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0]), FloatRegister)):
            raise Exception("Fatal Error -- register must be a valid floating point register")

        #get the .float line from the label
        found: bool= False
        for i in range(len(self.data)):
            if(self.data[i].contentName == self.lines[self.regFile.ProgramCounter].parameters[1].strip() and self.data[i].contentType == ".float"):
                found = True
                if(not memManager.containsAddress(hex(int(self.data[i].value, 16)))):
                    raise Exception("Fatal Error -- memory address not located")
                dest.value = memManager.get_address(hex(int(self.data[i].value, 16)))
                break

        if(not found):
            raise Exception("Fatal Error -- variable name not found")

    #function to perform multiplication single precision
    def MulSinglePrecision(self):
        #get the dest. register and the two operand registers
        dest: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0])
        src1: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1])
        src2: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[2])

        if (not isinstance(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0]), FloatRegister) or not isinstance(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1]), FloatRegister) or not isinstance(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[2]), FloatRegister)):
            raise Exception("Fatal Error -- register(s) must be a valid floating point register")

        dest.value = float(src1.value) * float(src2.value)

    #function to perform subtraction single precision
    def SubSinglePrecision(self):
        #get the dest. register and the two operand registers
        dest: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0])
        src1: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1])
        src2: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[2])

        if (not isinstance(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0]), FloatRegister) or not isinstance(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1]), FloatRegister) or not isinstance(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[2]), FloatRegister)):
            raise Exception("Fatal Error -- register(s) must be a valid floating point register")

        dest.value = float(src1.value) - float(src2.value)

    #function to perform absolute value single precision
    def AbsSinglePrecision(self):
        #get the dest. register and the src. register
        dest: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0])
        src: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1])

        if(not isinstance(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0]), FloatRegister) or not isinstance(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1]), FloatRegister)):
            raise Exception("Fatal Error -- register(s) must be a valid floating point register")

        #if the value is less than zero, flip the sign, either way place into the dest. register
        if(src.value < 0):
            dest.value = -1 * float(src.value)
        else:
            dest.value = float(src.value)

    #function to perform absolute value single precision
    def Abs(self):
        #get the dest. register and the src. register
        dest: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0])
        src: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1])

        if (isinstance(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0]), FloatRegister) or isinstance(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1]), FloatRegister)):
                raise Exception("Fatal Error -- register(s) must be a valid non-floating point register")

        #if the value is less than zero, flip the sign, either way place into the dest. register
        if (src.value < 0):
            dest.value = -1 * int(src.value)
        else:
            dest.value = int(src.value)

    #function to perform coproc flag true if less than single precision
    def CoprocIfLessThanSinglePrecision(self):
        #get the two registers for the comparison
        r1: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0])
        r2: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1])

        if (not isinstance(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0]), FloatRegister) or not isinstance(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1]), FloatRegister)):
            raise Exception("Fatal Error -- register(s) must be a valid floating point register")

        if(float(r1.value) < float(r2.value)):
            self.regFile.Fcc = True
        else:
            self.regFile.Fcc = False

    #function to perform coproc flag true if equal single precision
    def CoprocIfEqualSinglePrecision(self):
        #get the two registers for the comparison
        r1: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0])
        r2: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1])

        if (not isinstance(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0]), FloatRegister) or not isinstance(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1]), FloatRegister)):
            raise Exception("Fatal Error -- register(s) must be a valid floating point register")

        if (r1.value == r2.value):
            self.regFile.Fcc = True
        else:
            self.regFile.Fcc = False

    #function to perform move single precision
    def MoveSinglePrecision(self):
        #get the dest. register and the src. register
        dest: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0])
        src: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1])

        if (not isinstance(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0]), FloatRegister) or not isinstance(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1]), FloatRegister)):
            raise Exception("Fatal Error -- register(s) must be a valid floating point register")

        dest.value = float(src.value)

    #function to perform addition single precision
    def AddSinglePrecision(self):
        #get the dest. register and the two operand registers
        dest: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0])
        src1: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1])
        src2: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[2])

        if (not isinstance(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0]), FloatRegister) or not isinstance(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1]), FloatRegister) or not isinstance(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[2]), FloatRegister)):
            raise Exception("Fatal Error -- register(s) must be a valid floating point register")

        dest.value = float(src1.value) + float(src2.value)

    #function to perform division single precision
    def DivSinglePrecision(self):
        #get the dest. register and the two operand registers
        dest: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0])
        src1: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1])
        src2: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[2])

        if (not isinstance(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0]), FloatRegister) or not isinstance(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1]), FloatRegister) or not isinstance(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[2]), FloatRegister)):
            raise Exception("Fatal Error -- register(s) must be a valid floating point register")

        dest.value = float(src1.value) / float(src2.value)

    #function to perform database connect
    def DatabaseConnect(self):
        memManager: MemoryManager._MemoryManagerImpl = MemoryManager()

        #get the connection and cursor registers
        connRegister: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0])
        cursorRegister: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1])

        #get the string from the address in the third parameter register
        addressRegister: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[2])
        if(not memManager.containsAddress(hex(addressRegister.value))):
            raise Exception("Fatal Error -- register did not contain a valid memory address")
        fileLocation: str = str(memManager.get_address(hex(addressRegister.value)))
        fileLocation = os.path.normpath("Databases/" + fileLocation) #force whatever file it is to be in the Databases subdirectory

        #connect to the database (create if not there)
        connRegister.value = sql.connect(fileLocation)

        #enable foreign key constraints (off by default)
        connRegister.value.execute("PRAGMA foreign_keys = ON;")

        #create the cursor
        cursorRegister.value = connRegister.value.cursor()

    #function to perform database close
    def DatabaseClose(self):
        #get the connection and cursor registers
        connRegister: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0])
        cursorRegister: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1])

        if(not isinstance(connRegister.value, sql.Connection)):
            raise Exception("Fatal Error -- register did not contain a valid connection")
        if(not isinstance(cursorRegister.value, sql.Cursor)):
            raise Exception("Fatal Error -- register did not contain a valid cursor")

        #close the cursor then connection handles
        cursorRegister.value.close()
        connRegister.value.close()

    #function to perform database select
    def DatabaseSelect(self):
        memManager: MemoryManager._MemoryManagerImpl = MemoryManager()

        #get the rowCount dest. register
        rowCount: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0])

        #get the cursor register
        cursorRegister: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1])

        #get the query register
        queryRegister: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[2])

        #get the list of parameter register(s)
        params: tuple = tuple()
        for i in range(3, len(self.lines[self.regFile.ProgramCounter].parameters)):
            try:
                if(memManager.containsAddress(hex(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[i]).value))):
                    params = params + (memManager.get_address(hex(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[i]).value)),)
                else:
                    params = params + (self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[i]).value,)
            except:
                params = params + (self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[i]).value,)

        #perform the query on the cursor
        if(not memManager.containsAddress(hex(queryRegister.value))):
            raise Exception("Fatal Error -- register did not contain a valid memory address")
        query: str = str(memManager.get_address(hex(queryRegister.value)))
        cursorRegister.value.execute(query, params)
        results = cursorRegister.value.fetchall()

        #set the dest. register value to the rowCount (of the list)
        rowCount.value = len(results)
        memManager.results = results

    #function to perform database insert
    def DatabaseInsert(self):
        memManager: MemoryManager._MemoryManagerImpl = MemoryManager()

        #get the connection register
        connRegister: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0])

        #get the cursor register
        cursorRegister: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1])

        #get the query register
        queryRegister: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[2])

        #get the list of parameter register(s)
        params: tuple = tuple()
        for i in range(3, len(self.lines[self.regFile.ProgramCounter].parameters)):
            if (memManager.containsAddress(hex(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[i]).value))):
                params = params + (memManager.get_address(hex(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[i]).value)),)
            else:
                raise Exception("Fatal Error -- Database Insert parameter not valid memory address")

        #perform the query on the cursor
        if (not memManager.containsAddress(hex(queryRegister.value))):
            raise Exception("Fatal Error -- register did not contain a valid memory address")
        query: str = str(memManager.get_address(hex(queryRegister.value)))
        cursorRegister.value.execute(query, params)
        connRegister.value.commit()

    #function to perform database delete
    def DatabaseDelete(self):
        memManager: MemoryManager._MemoryManagerImpl = MemoryManager()

        #get the connection register
        connRegister: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0])

        #get the cursor register
        cursorRegister: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1])

        #get the query register
        queryRegister: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[2])

        #get the list of parameter register(s)
        params: tuple = tuple()
        for i in range(3, len(self.lines[self.regFile.ProgramCounter].parameters)):
            try:
                if (memManager.containsAddress(hex(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[i]).value))):
                    params = params + (memManager.get_address(hex(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[i]).value)),)
                else:
                    params = params + (self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[i]).value,)
            except:
                params = params + (self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[i]).value,)

        #perform the query on the cursor
        if (not memManager.containsAddress(hex(queryRegister.value))):
            raise Exception("Fatal Error -- register did not contain a valid memory address")
        query: str = str(memManager.get_address(hex(queryRegister.value)))
        cursorRegister.value.execute(query, params)
        connRegister.value.commit()

    #function to perform database table
    def DatabaseTable(self):
        #get the connection and cursor registers
        connRegister: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0])
        cursorRegister: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1])

        #get the register with the sql query
        sqlRegister: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[2])

        if (not isinstance(connRegister.value, sql.Connection)):
            raise Exception("Fatal Error -- register did not contain a valid connection")
        if (not isinstance(cursorRegister.value, sql.Cursor)):
            raise Exception("Fatal Error -- register did not contain a valid cursor")

        #get the string containing the sql from memory using the address in the sqlRegister
        memManager: MemoryManager._MemoryManagerImpl = MemoryManager()
        if(not memManager.containsAddress(hex(sqlRegister.value))):
            raise Exception("Fatal Error -- register did not contain a valid memory address")
        sqlQuery: str = str(memManager.get_address(hex(sqlRegister.value)))

        #perform the query (on the cursor)
        cursorRegister.value.execute(sqlQuery)

        #commit the change(s) (through the connection)
        connRegister.value.commit()

    #function to perform database update
    def DatabaseUpdate(self):
        memManager: MemoryManager._MemoryManagerImpl = MemoryManager()

        #get the connection register
        connRegister: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0])

        #get the cursor register
        cursorRegister: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1])

        #get the query register
        queryRegister: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[2])

        #get the list of parameter register(s)
        params: tuple = tuple()
        for i in range(3, len(self.lines[self.regFile.ProgramCounter].parameters)):
            try:
                if (memManager.containsAddress(hex(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[i]).value))):
                    params = params + (memManager.get_address(hex(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[i]).value)),)
                else:
                    params = params + (self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[i]).value,)
            except:
                params = params + (self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[i]).value,)

        #perform the query on the cursor
        if (not memManager.containsAddress(hex(queryRegister.value))):
            raise Exception("Fatal Error -- register did not contain a valid memory address")
        query: str = str(memManager.get_address(hex(queryRegister.value)))
        cursorRegister.value.execute(query, params)
        connRegister.value.commit()

    #function to perform database iterate
    def DatabaseIterate(self):
        memManager: MemoryManager._MemoryManagerImpl = MemoryManager()

        #get the row number register
        rowNum: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0])

        #get the cursor register
        cursorRegister: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1])

        #get the dest. register(s)
        destRegs: list[Register] = []
        for i in range(2, len(self.lines[self.regFile.ProgramCounter].parameters)):
            destRegs.append(self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[i]))

        #get the query results
        if(memManager.results == None):
            raise Exception("Fatal Error -- no query results located")
        results = memManager.results

        #handle result register and memory shenanigans
        if(rowNum.value >= len(results)):
            raise Exception("Fatal Error -- row number provided exceeded actual number of rows (index error)")
        row = results[rowNum.value]

        memManager.setAllAvailable() #ensure all db memory is freed/available
        for i in range(len(row)):
            #SQLite returns the data type closest to the attribute data type (ex. FLOAT -> float, INTEGER -> INT)
            #if the value is a float, place the float into the register
            #place the memory address into the register
            if(isinstance(row[i], float)):
                if (memManager.hasAvailable()):
                    destRegs[i].value = memManager.getFirstAvailable()
                    memManager.setAddress(memManager.getFirstAvailable(), row[i])
                else:
                    memManager.add_address(memType="db")
                    destRegs[i].value = memManager.getFirstAvailable()
                    memManager.setAddress(memManager.getFirstAvailable(), row[i])
                destRegs[i].value = memManager.get_address(hex(int(destRegs[i].value, 16)))
            #if the value is otherwise a string, perform memory check for first available db memory slot (add if none present)
            #place the memory address into the register
            elif(isinstance(row[i], str)):
                if(memManager.hasAvailable()):
                    destRegs[i].value = memManager.getFirstAvailable()
                    memManager.setAddress(memManager.getFirstAvailable(), row[i])
                else:
                    memManager.add_address(memType="db")
                    destRegs[i].value = memManager.getFirstAvailable()
                    memManager.setAddress(memManager.getFirstAvailable(), row[i])

            #if the value is an int (must be checked after float), place into register
            elif(isinstance(row[i], int)):
                if(memManager.hasAvailable()):
                    destRegs[i].value = memManager.getFirstAvailable()
                    memManager.setAddress(memManager.getFirstAvailable(), row[i])
                else:
                    memManager.add_address(memType="db")
                    destRegs[i].value = memManager.getFirstAvailable()
                    memManager.setAddress(memManager.getFirstAvailable(), row[i])
            else:
                raise Exception(f"Fatal Error -- Datatype {str(type(row[i]))} not supported")

    #function to set a place in memory to an offset of a word (from a place in memory or register)
    def StoreWordSinglePrecision(self):
        memManager: MemoryManager._MemoryManagerImpl() = MemoryManager()

        #get the register of the first parameter (what will be stored as the given memory address)
        sourceRegister: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[0].strip())
        if(not isinstance(sourceRegister, FloatRegister)):
            raise Exception("Fatal Error -- s.s source register should be a valid floating point register")

        #sw $reg, label
        if(self.IsVariableName(self.lines[self.regFile.ProgramCounter].parameters[1].strip())):
            #find the DataLine with this name and set the value of the register to the value of the line
            found: bool = False
            for i in range(len(self.data)):
                if (str(self.data[i].contentName) == str(self.lines[self.regFile.ProgramCounter].parameters[1])):
                    found = True
                    if (not memManager.containsAddress(hex(int(self.data[i].value, 16)))):
                        raise Exception("Fatal Error -- base address (label) name not found in memory")

                    if(self.data[i].contentType == ".float" and not isinstance(sourceRegister, FloatRegister)):
                        raise Exception("Fatal Error -- trying to store non-float in float memory")

                    memManager.setAddress(hex(int(self.data[i].value, 16)), value=sourceRegister.value)
                    break

            if (not found):
                raise Exception("Fatal Error -- Variable name not found in .data segment or is not a .word")
        else:
            #sw $reg, label($reg)
            if(self.IsVariableName(self.lines[self.regFile.ProgramCounter].parameters[1].strip().split('(')[0].strip())):
                if(self.IsRegister(self.lines[self.regFile.ProgramCounter].parameters[1].split('(')[1].strip()[:-1])):
                    offsetRegister: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1].split('(')[1].strip()[:-1])

                    #find the DataLine with this name and set the value of the register to the value of the line
                    found: bool = False
                    for i in range(len(self.data)):
                        if (str(self.data[i].contentName) == str(self.lines[self.regFile.ProgramCounter].parameters[1].strip().split('(')[0].strip())):
                            found = True
                            if (not memManager.containsAddress(hex(int(self.data[i].value, 16) + offsetRegister.value))):
                                raise Exception("Fatal Error -- address not found in memory")

                            if (self.data[i].contentType == ".float" and not isinstance(sourceRegister, FloatRegister)):
                                raise Exception("Fatal Error -- trying to store non-float in float memory")

                            memManager.setAddress(hex(int(self.data[i].value, 16) + offsetRegister.value), value=sourceRegister.value)
                            break
                else:
                    raise Exception("Fatal Error -- offset register is not a valid register")
            #sw $reg, offset($reg (base address))
            else:
                try:
                    offset: int = int(self.lines[self.regFile.ProgramCounter].parameters[1].split('(')[0].strip())
                    if (self.IsRegister(self.lines[self.regFile.ProgramCounter].parameters[1].split('(')[1].strip()[:-1])):
                        baseRegister: Register = self.GetRegister(self.lines[self.regFile.ProgramCounter].parameters[1].split('(')[1].strip()[:-1])

                        if(memManager.containsAddress(hex(int(baseRegister.value, 16) + offset))):
                            #determine if the line type is .flaot (for extra protection)
                            for i in range(len(self.data)):
                                if (str(self.data[i].value) == str(baseRegister.value)): #if the base addresses are the same (it is the line we are after)
                                    if (self.data[i].contentType == ".float" and not isinstance(sourceRegister, FloatRegister)):
                                        raise Exception("Fatal Error -- trying to store non-float in float memory")
                                    break

                            memManager.setAddress(hex(int(baseRegister.value, 16) + offset), value=baseRegister.value)
                        else:
                            raise Exception("Fatal Error -- base register + offset not found in memory")

                except ValueError:
                    raise Exception("Fatal Error -- offset value not valid integer")

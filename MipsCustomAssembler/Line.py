from RegisterFile import MemoryManager #used to manage memory

#this class handles each individual line of the program, stored within the Program class
class Line:
    def __init__(self, content: str, lineNumber: int, globalLineNumber: int):
        #get the mnemonic and any parameters such as dest. register, src. register(s), or data segment variables
        self.lineNumber = lineNumber
        self.globalLineNumber = globalLineNumber
        self.content = content
        self.parameters = [] #list of parameter(s)
        self.instruction = None #the mnemonic of the instruction

        if(self.IsTextSegment(content)): #is the line .text
            self.segType: str = ".text"
            self.segment = None
        elif(self.IsGlobalSegment(content)): #is the line .globl with a segment name
            self.segType: str = ".globl"
        elif(':' in self.content): #is the line a segment header
            self.segType = 'header'
            self.segment = self.content.strip().split(':')[0]
            if(len(list(filter(None, self.content.strip().split(':')))) > 1):
                raise Exception("Fatal Error -- Segment header should end after \':\'at line:", self.globalLineNumber)
        else:
            self.segType = None
            self.segment = None
            #get the mnemonic and parameters now that we know the line isn't .globl or .text
            self.instruction = self.content.strip().split(' ')[0] #mnemonic
            self.parameters = [item.strip().strip(',').strip() for item in self.content.strip().split(' ') if item.strip().strip(',').strip() != '' and item.strip().strip(',').strip() != self.instruction.strip()]

            #determine if the mnemonic is real and the number of parameters (and their contents) make sense
            self.CheckInstruction()

    #function to determine if a line is the .text segment
    def IsTextSegment(self, line: str) -> bool:
        line = line.strip()
        if (len(line) < 5):
            return False
        return (line[0] == '.' and line[1] == 't' and line[2] == 'e' and line[3] == 'x' and line[4] == 't')

    #function to determine if a line is the .globl segment
    def IsGlobalSegment(self, line: str) -> bool:
        if(not line.strip().startswith(".globl")):
            return False

        # get the name of the segment to be made global
        self.segment:str = line.split(".globl")[1].strip()

        #make sure that the segment has no spaces, make sure it does not start with a number, make sure it is not a reserved word
        if(' ' in self.segment):
            raise Exception("Fatal Error -- Segment name " + self.segment + " contains an invalid character at line:", self.globalLineNumber)
        if(self.segment.startswith('0') or self.segment.startswith('1') or self.segment.startswith('2') or self.segment.startswith('3') or self.segment.startswith('4') or self.segment.startswith('5') or self.segment.startswith('6') or self.segment.startswith('7') or self.segment.startswith('8') or self.segment.startswith('9')):
            raise Exception("Fatal Error -- Segment name " + self.segment + " contains an invalid character at line:", self.globalLineNumber)
        badNames: list[str] = []  # reserved register names
        if (self.segment in badNames):
            raise Exception("Fatal Error -- Segment name " + self.segment + " is a reserved word at line:", self.globalLineNumber)
        return True

    #function to check the mnemonic and parameters to ensure they make sense (in all cases)
    def CheckInstruction(self):
        match(self.instruction.strip()): #branch to get all mnemonic cases, case-sensitive so check directly
            case "syscall": #run the function that corresponds with the int in the $v0 register
                #make sure there's no parameters (only needed check at this point in time)
                if(len(self.parameters) != 0):
                    raise Exception("Fatal Error -- syscall should not have any parameters at line:", self.globalLineNumber)

            case "li": #load immediate into a register
                #make sure there's two parameters (a register to the left and a number to the right)
                if(len(self.parameters) != 2):
                    raise Exception("Fatal Error -- load immediate should have 2 parameters at line:", self.globalLineNumber)
                if(not self.IsRegister(self.parameters[0]) or self.parameters[0] == "$zero" or self.IsFlopRegister(self.parameters[0])): #to the left
                    raise Exception("Fatal Error -- load immediate parameter 1 should be a valid register at line:", self.globalLineNumber)
                if(not self.IsWholeNumber(self.parameters[1])):
                    raise Exception("Fatal Error -- load immediate parameter 2 should be an integer at line:", self.globalLineNumber)

            case "la": #load address (used for loading strings from .data)
                #make sure there's two parameters (a register and some label which doesn't need to be checked until just before runtime)
                if(len(self.parameters) != 2):
                    raise Exception("Fatal Error -- load address should have 2 parameters at line:", self.globalLineNumber)
                if(not self.IsRegister(self.parameters[0]) or self.parameters[0] == "$zero" or self.IsFlopRegister(self.parameters[0])):
                    raise Exception("Fatal Error -- load address parameter 1 should be a valid register at line:", self.globalLineNumber)
                if (self.IsRegister(self.parameters[1]) or self.parameters[1] == "$zero" or self.IsFlopRegister(self.parameters[1])):
                    raise Exception("Fatal Error -- load address parameter 2 should not be a register at line:", self.globalLineNumber)

            case "add": #addition of integers
                #make sure there's three parameters (3 registers)
                if(len(self.parameters) != 3):
                    raise Exception("Fatal Error -- add should have 3 parameters at line:", self.globalLineNumber)
                if(not self.IsRegister(self.parameters[0]) or self.parameters[0] == "$zero" or self.IsFlopRegister(self.parameters[0])):
                    raise Exception("Fatal Error -- add parameter 1 should be a valid register at line:", self.globalLineNumber)
                if ((not self.IsRegister(self.parameters[1]) and not self.IsWholeNumber(self.parameters[1].strip()) and self.parameters[1].strip() != "$zero") or self.IsFlopRegister(self.parameters[1])):
                    try:
                        int(self.parameters[1])
                    except ValueError:
                        raise Exception("Fatal Error -- add parameter 2 should be either an integer or a valid register at line:", self.globalLineNumber)
                if ((not self.IsRegister(self.parameters[2]) and not self.IsWholeNumber(self.parameters[2].strip()) and self.parameters[2].strip() != "$zero") or self.IsFlopRegister(self.parameters[2])):
                    try:
                        int(self.parameters[2])
                    except ValueError:
                        raise Exception("Fatal Error -- add parameter 3 should be either an integer or a valid register at line:", self.globalLineNumber)

            case "sub":#subtraction of integers
                #make sure there's three parameters (3 registers)
                if(len(self.parameters) != 3):
                    raise Exception("Fatal Error -- subtract should have 3 parameters at line:", self.globalLineNumber)
                if(not self.IsRegister(self.parameters[0]) or self.parameters[0] == "$zero" or self.IsFlopRegister(self.parameters[0])):
                    raise Exception("Fatal Error -- subtract parameter 1 should be a valid register at line:", self.globalLineNumber)
                if((not self.IsRegister(self.parameters[1]) and not self.IsWholeNumber(self.parameters[1].strip()) and self.parameters[1].strip() != "$zero") or self.IsFlopRegister(self.parameters[1])):
                    try:
                        int(self.parameters[1])
                    except ValueError:
                        raise Exception("Fatal Error -- subtract parameter 2 should be either an integer or a valid register at line:", self.globalLineNumber)
                if((not self.IsRegister(self.parameters[2]) and not self.IsWholeNumber(self.parameters[2].strip()) and self.parameters[2].strip() != "$zero") or self.IsFlopRegister(self.parameters[2])):
                    try:
                        int(self.parameters[2])
                    except ValueError:
                        raise Exception("Fatal Error -- subtract parameter 3 should be either an integer or a valid register at line:", self.globalLineNumber)

            case "mul": #multiplication of integers
                #make sure there's three parameters (3 registers)
                if(len(self.parameters) != 3):
                    raise Exception("Fatal Error -- (mul) multiply should have 3 parameters at line:", self.globalLineNumber)
                if(not self.IsRegister(self.parameters[0]) or self.parameters[0] == "$zero" or self.IsFlopRegister(self.parameters[0])):
                    raise Exception("Fatal Error -- (mul) multiply parameter 1 should be a valid register at line:", self.globalLineNumber)
                if((not self.IsRegister(self.parameters[1]) and self.parameters[1].strip() != "$zero") or self.IsFlopRegister(self.parameters[1])):
                    try:
                        int(self.parameters[1])
                    except ValueError:
                        raise Exception("Fatal Error -- (mul) multiply parameter 2 should be either an integer or a valid register at line:", self.globalLineNumber)
                if((not self.IsRegister(self.parameters[2]) and self.parameters[2].strip() != "$zero") or self.IsFlopRegister(self.parameters[2])):
                    try:
                        int(self.parameters[2])
                    except ValueError:
                        raise Exception("Fatal Error -- (mul) multiply parameter 3 should be either an integer or a valid register at line:", self.globalLineNumber)

            case "mult": #multiplication of integers (2 operands, upper 32 bits goes to hi, lower 32 bits goes to lo)
                #make sure there's two parameters (both can be either an integer or a register)
                if (len(self.parameters) != 2):
                    raise Exception("Fatal Error -- (mult) multiply should have 2 parameters at line:", self.globalLineNumber)
                if ((not self.IsRegister(self.parameters[0]) and not self.IsWholeNumber(self.parameters[0].strip()) and self.parameters[0].strip() != "$zero") or self.IsFlopRegister(self.parameters[0])):
                    try:
                        int(self.parameters[0])
                    except ValueError:
                        raise Exception("Fatal Error -- (mult) multiply parameter 1 should be either an integer or a valid register at line:", self.globalLineNumber)
                if ((not self.IsRegister(self.parameters[1]) and not self.IsWholeNumber(self.parameters[1].strip()) and self.parameters[1].strip() != "$zero") or self.IsFlopRegister(self.parameters[1])):
                    try:
                        int(self.parameters[1])
                    except ValueError:
                        raise Exception("Fatal Error -- (mult) multiply parameter 2 should be either an integer or a valid register at line:", self.globalLineNumber)

            case "div": #division of integers (2 operands, quotient to Lo, remainder to Hi)
                #make sure there's two or three parameters (both can be either an integer or a register),(left most is a register, others can be either integer or a register)
                if (len(self.parameters) == 2):
                    if ((not self.IsRegister(self.parameters[0]) and not self.IsWholeNumber(self.parameters[0].strip())) or self.parameters[0] == "$zero" or self.IsFlopRegister(self.parameters[0])):
                        raise Exception("Fatal Error -- divide parameter 1 should be either an integer or a valid register at line:", self.globalLineNumber)
                    if ((not self.IsRegister(self.parameters[1]) and not self.IsWholeNumber(self.parameters[1].strip())) or self.parameters[1] == "$zero" or self.IsFlopRegister(self.parameters[1])):
                        raise Exception("Fatal Error -- divide parameter 2 should be either an integer or a valid register at line:", self.globalLineNumber)
                elif(len(self.parameters) == 3):
                    if (not self.IsRegister(self.parameters[0]) or self.parameters[0] == "$zero" or self.IsFlopRegister(self.parameters[0])):
                        raise Exception("Fatal Error -- divide parameter 1 should be either an integer or a valid register at line:", self.globalLineNumber)
                    if ((not self.IsRegister(self.parameters[1]) and not self.IsWholeNumber(self.parameters[1].strip()) and self.parameters[1].strip() != "$zero") or self.IsFlopRegister(self.parameters[0])):
                        raise Exception("Fatal Error -- divide parameter 2 should be either an integer or a valid register at line:", self.globalLineNumber)
                    if ((not self.IsRegister(self.parameters[2]) and not self.IsWholeNumber(self.parameters[2].strip())) or self.parameters[2].strip() == "$zero") or self.IsFlopRegister(self.parameters[0]):
                        raise Exception("Fatal Error -- divide parameter 3 should be either an integer or a valid register at line:", self.globalLineNumber)
                else:
                    raise Exception("Fatal Error -- divide should have either 2 or 3 parameters at line:", self.globalLineNumber)

            case "move": #move something into a register
                #make sure there's two parameters (2 registers)
                if (len(self.parameters) != 2):
                    raise Exception("Fatal Error -- move should have 2 parameters at line:", self.globalLineNumber)
                if (not self.IsRegister(self.parameters[0]) or self.parameters[0] == "$zero" or self.IsFlopRegister(self.parameters[0])):
                    raise Exception("Fatal Error -- move parameter 1 should be a valid register at line:", self.globalLineNumber)
                if ((not self.IsRegister(self.parameters[1]) or self.IsFlopRegister(self.parameters[1])) and self.parameters[1].strip() != "$zero"):
                    raise Exception("Fatal Error -- move parameter 2 should be a valid register at line:", self.globalLineNumber)

            case "sgt": #set r1 to 1 if r2 greater than r3, otherwise set r1 0
                #make sure there's three parameters (3 registers)
                if (len(self.parameters) != 3):
                    raise Exception("Fatal Error -- set if greater than should have 3 parameters at line:", self.globalLineNumber)
                if (not self.IsRegister(self.parameters[0]) or self.parameters[0] == "$zero" or self.IsFlopRegister(self.parameters[0])):
                    raise Exception("Fatal Error -- set if greater than parameter 1 should be a valid register at line:", self.globalLineNumber)
                if ((not self.IsRegister(self.parameters[1]) or self.IsFlopRegister(self.parameters[1])) and self.parameters[1] != "$zero"):
                    raise Exception("Fatal Error -- set if greater than parameter 2 should be a valid register at line:", self.globalLineNumber)
                if ((not self.IsRegister(self.parameters[2]) or self.IsFlopRegister(self.parameters[2])) and self.parameters[2] != "$zero"):
                    raise Exception("Fatal Error -- set if greater than parameter 3 should be a valid register at line:", self.globalLineNumber)

            case "beqz": #branch if equal to zero
                #make sure there's two parameters (1 register and the other a label)
                if (len(self.parameters) != 2):
                    raise Exception("Fatal Error -- branch if equal to zero should have 2 parameters at line:", self.globalLineNumber)
                if ((not self.IsRegister(self.parameters[0]) or self.IsFlopRegister(self.parameters[0])) and self.parameters[0] != "$zero" and not self.IsWholeNumber(self.parameters[0])):
                    raise Exception("Fatal Error -- branch if equal to zero parameter 1 should be a valid register at line:", self.globalLineNumber)
                if (self.IsRegister(self.parameters[1]) or self.parameters[1] == "$zero" or self.IsFlopRegister(self.parameters[1])):
                    raise Exception("Fatal Error -- branch if equal to zero parameter 2 should be a valid label at line:",  self.globalLineNumber)

            case "seq": #set 1 if equal to, 0 if not
                #make sure there's three parameters (3 registers)
                if (len(self.parameters) != 3):
                    raise Exception("Fatal Error -- set if equal to should have 3 parameters at line:", self.globalLineNumber)
                if ((not self.IsRegister(self.parameters[0]) or self.IsFlopRegister(self.parameters[0])) and self.parameters[0] != "$zero"):
                    raise Exception("Fatal Error -- set if equal to parameter 1 should be a valid register at line:", self.globalLineNumber)
                if ((not self.IsRegister(self.parameters[1]) or self.IsFlopRegister(self.parameters[1])) and self.parameters[1] != "$zero"):
                    raise Exception( "Fatal Error -- set if equal to parameter 2 should be a valid register at line:", self.globalLineNumber)
                if ((not self.IsRegister(self.parameters[2]) or self.IsFlopRegister(self.parameters[2])) and self.parameters[2] != "$zero"):
                    raise Exception("Fatal Error -- set if equal to parameter 3 should be a valid register at line:", self.globalLineNumber)

            case "j": #jump to a segment header
                #make sure there's 1 parameter (a label) parameter checked just before runtime
                if (len(self.parameters) != 1):
                    raise Exception("Fatal Error -- (j) jump should have 1 parameter at line:", self.globalLineNumber)
                if(self.IsRegister(self.parameters[0]) or self.IsFlopRegister(self.parameters[0]) or self.parameters[0] == "$zero"):
                    raise Exception("Fatal Error -- (j) jump parameter 1 should be a valid label at line:", self.globalLineNumber)

            case "blt": #branch if less than
                #make sure there's three parameters (2 registers and the other a label)
                if (len(self.parameters) != 3):
                    raise Exception("Fatal Error -- branch if less than should have 3 parameters at line:", self.globalLineNumber)
                if ((not self.IsRegister(self.parameters[0]) or self.IsFlopRegister(self.parameters[0])) and self.parameters[0].strip() != "$zero" and not self.IsWholeNumber(self.parameters[0])):
                    raise Exception("Fatal Error -- branch if less than parameter 1 should be a valid register at line:", self.globalLineNumber)
                if ((not self.IsRegister(self.parameters[1]) or self.IsFlopRegister(self.parameters[1])) and self.parameters[1].strip() != "$zero" and not self.IsWholeNumber(self.parameters[1])):
                    raise Exception("Fatal Error -- branch if less than parameter 2 should be a valid register at line:", self.globalLineNumber)
                if (self.IsRegister(self.parameters[2]) or self.parameters[2] == "$zero" or self.IsFlopRegister(self.parameters[2])):
                    raise Exception("Fatal Error -- branch if less than parameter 3 should be a valid label at line:", self.globalLineNumber)

            case "bgt": #branch if greater than
                #make sure there's three parameters (2 registers and the other a label)
                if (len(self.parameters) != 3):
                    raise Exception("Fatal Error -- branch if greater than should have 3 parameters at line:", self.globalLineNumber)
                if ((not self.IsRegister(self.parameters[0]) or self.IsFlopRegister(self.parameters[0])) and self.parameters[0].strip() != "$zero" and not self.IsWholeNumber(self.parameters[0])):
                    raise Exception("Fatal Error -- branch if greater than parameter 1 should be a valid register at line:", self.globalLineNumber)
                if ((not self.IsRegister(self.parameters[1]) or self.IsFlopRegister(self.parameters[1])) and self.parameters[1].strip() != "$zero" and not self.IsWholeNumber(self.parameters[1])):
                    raise Exception("Fatal Error -- branch if greater than parameter 2 should be a valid register at line:", self.globalLineNumber)
                if (self.IsRegister(self.parameters[2]) or self.parameters[2] == "$zero" or self.IsFlopRegister(self.parameters[2])):
                    raise Exception("Fatal Error -- branch if greater than parameter 3 should be a valid label at line:", self.globalLineNumber)

            case "ble": #branch if less than or equal to
                #make sure there's three parameters (2 registers and the other a label)
                if (len(self.parameters) != 3):
                    raise Exception("Fatal Error -- branch if less than or equal to should have 3 parameters at line:", self.globalLineNumber)
                if ((not self.IsRegister(self.parameters[0]) or self.IsFlopRegister(self.parameters[0])) and self.parameters[0].strip() != "$zero" and not self.IsWholeNumber(self.parameters[0])):
                    raise Exception("Fatal Error -- branch if less than or equal to parameter 1 should be a valid register at line:", self.globalLineNumber)
                if ((not self.IsRegister(self.parameters[1]) or self.IsFlopRegister(self.parameters[1])) and self.parameters[1].strip() != "$zero" and not self.IsWholeNumber(self.parameters[1])):
                    raise Exception("Fatal Error -- branch if less than or equal to parameter 2 should be a valid register at line:", self.globalLineNumber)
                if (self.IsRegister(self.parameters[2]) or self.parameters[2] == "$zero" or self.IsFlopRegister(self.parameters[2])):
                    raise Exception("Fatal Error -- branch if less than or equal to parameter 3 should be a valid label at line:", self.globalLineNumber)

            case "bgtz": #branch if greater than zero
                #make sure there's two parameters (1 register and the other a label)
                if (len(self.parameters) != 2):
                    raise Exception("Fatal Error -- branch if greater than zero should have 3 parameters at line:", self.globalLineNumber)
                if ((not self.IsRegister(self.parameters[0]) or self.IsFlopRegister(self.parameters[0])) and self.parameters[0].strip() != "$zero" and not self.IsWholeNumber(self.parameters[0])):
                    raise Exception("Fatal Error -- branch if greater than zero parameter 1 should be a valid register at line:", self.globalLineNumber)
                if (self.IsRegister(self.parameters[1]) or self.parameters[1] == "$zero" or self.IsFlopRegister(self.parameters[1])):
                    raise Exception("Fatal Error -- branch if greater than zero parameter 3 should be a valid label at line:", self.globalLineNumber)

            case "sw": #set word
                #make sure there's two parameters (2 registers)
                if (len(self.parameters) != 2):
                    raise Exception("Fatal Error -- set word should have 2 parameters at line:", self.globalLineNumber)
                if ((not self.IsRegister(self.parameters[0]) and not self.parameters[0] == "$zero") or self.IsFlopRegister(self.parameters[0])):
                    raise Exception("Fatal Error -- set word parameter 1 should be a valid register at line:", self.globalLineNumber)
                if (self.IsRegister(self.parameters[1]) or self.IsFlopRegister(self.parameters[1]) or self.parameters[1] == "$zero"):
                    raise Exception("Fatal Error -- set word parameter 2 should be a valid data address reference at line:", self.globalLineNumber)

            case "s.s": #set word single-precision
                # make sure there's two parameters (2 registers)
                if (len(self.parameters) != 2):
                    raise Exception("Fatal Error -- set word single-precision should have 2 parameters at line:", self.globalLineNumber)
                if (not self.IsFlopRegister(self.parameters[0])):
                    raise Exception("Fatal Error -- set word single-precision parameter 1 should be a valid register at line:", self.globalLineNumber)
                if (self.IsRegister(self.parameters[1]) or self.IsFlopRegister(self.parameters[1]) or self.parameters[1] == "$zero"):
                    raise Exception("Fatal Error -- set word single-precision parameter 2 should be a valid data address reference at line:", self.globalLineNumber)

            case "jal": #jump and link (link to the $ra) parameter checked just before runtime
                #make sure there's 1 parameter (a label)
                if (len(self.parameters) != 1):
                    raise Exception("Fatal Error -- (jal) jump and link should have 1 parameter at line:", self.globalLineNumber)
                if (self.IsFlopRegister(self.parameters[0]) or self.parameters[0] == "$zero" or self.IsRegister(self.parameters[0])):
                    raise Exception("Fatal Error -- (jal) jump and link parameter 1 should be a valid label at line:", self.globalLineNumber)

            case "bge": #branch if greater than or equal to
                #make sure there's three parameters (two registers and the other a label)
                if (len(self.parameters) != 3):
                    raise Exception("Fatal Error -- branch greater than or equal should have 3 parameters at line:", self.globalLineNumber)
                if ((not self.IsRegister(self.parameters[0]) or self.IsFlopRegister(self.parameters[0])) and self.parameters[0].strip() != "$zero" and not self.IsWholeNumber(self.parameters[0])):
                    raise Exception("Fatal Error -- branch greater than or equal parameter 1 should be a valid register at line:", self.globalLineNumber)
                if ((not self.IsRegister(self.parameters[1]) or self.IsFlopRegister(self.parameters[1])) and self.parameters[1].strip() != "$zero" and not self.IsWholeNumber(self.parameters[1])):
                    raise Exception("Fatal Error -- branch greater than or equal parameter 2 should be a valid register at line:", self.globalLineNumber)
                if (self.IsRegister(self.parameters[2]) or self.parameters[2] == "$zero" or self.IsFlopRegister(self.parameters[2])):
                    raise Exception("Fatal Error -- branch greater than or equal parameter 3 should be a valid label at line:", self.globalLineNumber)

            case "lw": #load word
                #make sure there's two parameters (2 registers)
                if (len(self.parameters) != 2):
                    raise Exception("Fatal Error -- load word should have 2 parameters at line:", self.globalLineNumber)
                if (not self.IsRegister(self.parameters[0]) or self.parameters[0] == "$zero" or self.IsFlopRegister(self.parameters[0])):
                    raise Exception("Fatal Error -- load word parameter 1 should be a valid register at line:", self.globalLineNumber)
                if (self.IsRegister(self.parameters[1]) or self.IsFlopRegister(self.parameters[1]) or self.parameters[1].strip() == "$zero"):
                    raise Exception("Fatal Error -- set word parameter 2 should be a valid data address reference offset at line:", self.globalLineNumber)

            case "jr": #jump register (only the $ra register)
                #make sure there is only 1 parameter (the ra register)
                if (len(self.parameters) != 1):
                    raise Exception("Fatal Error -- jump register should have 1 parameter at line:", self.globalLineNumber)
                if (self.parameters[0].strip() != "$ra"):
                    raise Exception("Fatal Error -- jump register parameter 1 should be the $ra:", self.globalLineNumber)

            case "beq": #branch if equal to
                #make sure there's three parameters (two registers and the other a label)
                if (len(self.parameters) != 3):
                    raise Exception("Fatal Error -- branch if equal should have 3 parameters at line:", self.globalLineNumber)
                if ((not self.IsRegister(self.parameters[0]) or self.IsFlopRegister(self.parameters[0])) and self.parameters[0].strip() != "$zero" and not self.IsWholeNumber(self.parameters[0])):
                    raise Exception("Fatal Error -- branch if equal parameter 1 should be a valid register line:", self.globalLineNumber)
                if ((not self.IsRegister(self.parameters[1]) or self.IsFlopRegister(self.parameters[1])) and self.parameters[1].strip() != "$zero" and not self.IsWholeNumber(self.parameters[1])):
                    raise Exception("Fatal Error -- branch if equal parameter 2 should be a valid register at line:", self.globalLineNumber)
                if (self.IsRegister(self.parameters[2]) or self.parameters[2] == "$zero" or self.IsFlopRegister(self.parameters[2])):
                    raise Exception("Fatal Error -- branch if equal parameter 3 should be a valid label at line:", self.globalLineNumber)

            case "bltz": #branch if less than zero
                #make sure there's two parameters (one register and the other a label)
                if (len(self.parameters) != 2):
                    raise Exception("Fatal Error -- branch less than zero should have 2 parameters at line:", self.globalLineNumber)
                if ((not self.IsRegister(self.parameters[0]) or self.IsFlopRegister(self.parameters[0])) and self.parameters[0].strip() != "$zero" and not self.IsWholeNumber(self.parameters[0])):
                    raise Exception("Fatal Error -- branch less than zero parameter 1 should be a valid register at line:", self.globalLineNumber)
                if (self.IsRegister(self.parameters[1]) or self.parameters[1] == "$zero" or self.IsFlopRegister(self.parameters[1])):
                    raise Exception("Fatal Error -- branch less than zero parameter 2 should be a valid label at line:", self.globalLineNumber)

            case "bnez": #branch if not equal to zero
                #make sure there's two parameters (one register and the other a label)
                if (len(self.parameters) != 2):
                    raise Exception("Fatal Error -- branch not equal to zero should have 2 parameters at line:", self.globalLineNumber)
                if ((not self.IsRegister(self.parameters[0]) or self.IsFlopRegister(self.parameters[0])) and self.parameters[0].strip() != "$zero" and not self.IsWholeNumber(self.parameters[0])):
                    raise Exception("Fatal Error -- branch not equal to zero parameter 1 should be a valid register at line:", self.globalLineNumber)
                if (self.IsRegister(self.parameters[1]) or self.parameters[1] == "$zero" or self.IsFlopRegister(self.parameters[1])):
                    raise Exception("Fatal Error -- branch not equal to zero parameter 2 should be a valid label at line:", self.globalLineNumber)

            case "mfhi": #move from hi (hi is a register that holds the remainder after division, or the upper 32 bits of mult result)
                #make sure there's 1 parameter (a register)
                if (len(self.parameters) != 1):
                    raise Exception("Fatal Error -- move from hi should have 1 parameter at line:", self.globalLineNumber)
                if (not self.IsRegister(self.parameters[0]) or self.parameters[0] == "$zero" or self.IsFlopRegister(self.parameters[0])):
                    raise Exception("Fatal Error -- move from hi parameter 1 should be a valid register at line:", self.globalLineNumber)

            case "mflo": #move from lo (lo is a register that holds the quotient after a division, or lower 32 bits of mult result)
                #make sure there's 1 parameter (a register)
                if (len(self.parameters) != 1):
                    raise Exception("Fatal Error -- move from lo should have 1 parameter at line:", self.globalLineNumber)
                if (not self.IsRegister(self.parameters[0]) or self.parameters[0] == "$zero" or self.IsFlopRegister(self.parameters[0])):
                    raise Exception("Fatal Error -- move from lo parameter 1 should be a valid register at line:", self.globalLineNumber)

            case "l.s": #load single precision
                #make sure there's 2 parameters (a flop register and an offset to an address)
                if(len(self.parameters) != 2):
                    raise Exception("Fatal Error -- load single should have 2 parameters at line:", self.globalLineNumber)
                if (not self.IsFlopRegister(self.parameters[0]) or self.parameters[0] == "$zero"):
                    raise Exception("Fatal Error -- load single parameter 1 should be a valid coproc register at line:", self.globalLineNumber)
                if (self.IsRegister(self.parameters[1]) or self.parameters[1] == "$zero" or self.IsFlopRegister(self.parameters[1])):
                    raise Exception("Fatal Error -- load single parameter 2 should be a valid data address reference offset at line:", self.globalLineNumber)

            case "lwc1": #load word coproc 1
                #make sure there's 2 parameters (a flop register and an offset to an address)
                if (len(self.parameters) != 2):
                    raise Exception("Fatal Error -- load word into coproc 1 should have 2 parameters at line:", self.globalLineNumber)
                if (not self.IsFlopRegister(self.parameters[0]) or self.parameters[0] == "$zero"):
                    raise Exception("Fatal Error -- load word into coproc 1 parameter 1 should be a valid coproc register at line:", self.globalLineNumber)
                if (self.IsRegister(self.parameters[1]) or self.parameters[1] == "$zero" or self.IsFlopRegister(self.parameters[1])):
                    raise Exception("Fatal Error -- load word into coproc 1 parameter 2 should be a valid data address reference offset at line:", self.globalLineNumber)

            case "mul.s": #multiply single precision
                #make sure there's 3 parameters (all registers)
                if (len(self.parameters) != 3):
                    raise Exception("Fatal Error -- multiply single precision should have 3 parameters at line:", self.globalLineNumber)
                if (not self.IsFlopRegister(self.parameters[0]) or self.parameters[0] == "$zero"):
                    raise Exception("Fatal Error -- multiply single precision parameter 1 should be a valid coproc register at line:", self.globalLineNumber)
                if (not self.IsFlopRegister(self.parameters[1]) or self.parameters[1] == "$zero"):
                    raise Exception("Fatal Error -- multiply single precision parameter 2 should be a valid coproc register at line:", self.globalLineNumber)
                if (not self.IsFlopRegister(self.parameters[2]) or self.parameters[2] == "$zero"):
                    raise Exception("Fatal Error -- multiply single precision parameter 3 should be a valid coproc register at line:", self.globalLineNumber)

            case "sub.s": #subtract single precision
                #make sure there's 3 parameters (all registers)
                if (len(self.parameters) != 3):
                    raise Exception("Fatal Error -- subtract single precision should have 3 parameters at line:", self.globalLineNumber)
                if (not self.IsFlopRegister(self.parameters[0]) or self.parameters[0] == "$zero"):
                    raise Exception("Fatal Error -- subtract single precision parameter 1 should be a valid coproc register at line:", self.globalLineNumber)
                if (not self.IsFlopRegister(self.parameters[1]) or self.parameters[1] == "$zero"):
                    raise Exception("Fatal Error -- subtract single precision parameter 2 should be a valid coproc register at line:", self.globalLineNumber)
                if (not self.IsFlopRegister(self.parameters[2]) or self.parameters[2] == "$zero"):
                    raise Exception("Fatal Error -- subtract single precision parameter 3 should be a valid coproc register at line:", self.globalLineNumber)

            case "abs.s": #absolute value single precision
                #make sure there's 2 parameters (all registers)
                if (len(self.parameters) != 2):
                    raise Exception("Fatal Error -- absolute value single precision should have 2 parameters at line:", self.globalLineNumber)
                if (not self.IsFlopRegister(self.parameters[0]) or self.parameters[0] == "$zero"):
                    raise Exception("Fatal Error -- absolute value single precision parameter 1 should be a valid coproc register at line:", self.globalLineNumber)
                if (not self.IsFlopRegister(self.parameters[1]) or self.parameters[1] == "$zero"):
                    raise Exception("Fatal Error -- absolute value single precision parameter 2 should be a valid coproc register at line:", self.globalLineNumber)

            case "abs": #absolute value of integer
                #make sure there's two parameters (both registers)
                if (len(self.parameters) != 2):
                    raise Exception("Fatal Error -- absolute value should have 2 parameters at line:", self.globalLineNumber)
                if (self.IsFlopRegister(self.parameters[0]) or self.parameters[0] == "$zero" or not self.IsRegister(self.parameters[0])):
                    raise Exception( "Fatal Error -- absolute value parameter 1 should be a valid register at line:", self.globalLineNumber)
                if (self.IsFlopRegister(self.parameters[1]) or (self.parameters[1] != "$zero" and not self.IsRegister(self.parameters[0]) and not self.IsWholeNumber(self.parameters[0]))):
                    raise Exception("Fatal Error -- absolute value parameter 2 should be either an integer or a valid register at line:", self.globalLineNumber)

            case "c.lt.s": #compare less than single precision
                #make sure there's 2 parameters (all registers)
                if (len(self.parameters) != 2):
                    raise Exception("Fatal Error -- compare less than single precision should have 2 parameters at line:", self.globalLineNumber)
                if (not self.IsFlopRegister(self.parameters[0]) or self.parameters[0] == "$zero"):
                    raise Exception("Fatal Error -- compare less than single precision parameter 1 should be a valid coproc register at line:", self.globalLineNumber)
                if (not self.IsFlopRegister(self.parameters[1]) or self.parameters[1] == "$zero"):
                    raise Exception("Fatal Error -- compare less than single precision parameter 2 should be a valid coproc register at line:", self.globalLineNumber)

            case "c.eq.s": #compare equal to single precision
                #make sure there's 2 parameters (all registers)
                if (len(self.parameters) != 2):
                    raise Exception("Fatal Error -- compare equal to single precision should have 2 parameters at line:", self.globalLineNumber)
                if (not self.IsFlopRegister(self.parameters[0]) or self.parameters[0] == "$zero"):
                    raise Exception("Fatal Error -- compare equal to single precision parameter 1 should be a valid coproc register at line:", self.globalLineNumber)
                if (not self.IsFlopRegister(self.parameters[1]) or self.parameters[1] == "$zero"):
                    raise Exception("Fatal Error -- compare equal to single precision parameter 2 should be a valid coproc register at line:", self.globalLineNumber)

            case "bc1t": #branch if coproc 1 is true (condition flag in the coproc, only param is segment header)
                #make sure there's 1 parameter (a label)
                if (len(self.parameters) != 1):
                    raise Exception("Fatal Error -- branch if coproc 1 flag true should have 1 parameter at line:", self.globalLineNumber)
                if (self.IsRegister(self.parameters[0]) or self.parameters[0] == "$zero" or self.IsFlopRegister(self.parameters[0])):
                    raise Exception("Fatal Error -- branch if coproc 1 flag true parameter 1 should be a valid label at line:", self.globalLineNumber)

            case "mov.s": #move into register single precision
                #make sure there's 2 parameters (all registers)
                if (len(self.parameters) != 2):
                    raise Exception("Fatal Error -- move single precision should have 2 parameters at line:", self.globalLineNumber)
                if (not self.IsFlopRegister(self.parameters[0]) or self.parameters[0] == "$zero"):
                    raise Exception("Fatal Error -- move single precision parameter 1 should be a valid coproc register at line:", self.globalLineNumber)
                if (not self.IsFlopRegister(self.parameters[1]) or self.parameters[1] == "$zero"):
                    raise Exception("Fatal Error -- move single precision parameter 2 should be a valid coproc register at line:", self.globalLineNumber)

            case "add.s": #addition single precision
                #make sure there's 3 parameters (all registers)
                if (len(self.parameters) != 3):
                    raise Exception("Fatal Error -- add single precision should have 3 parameters at line:", self.globalLineNumber)
                if (not self.IsFlopRegister(self.parameters[0]) or self.parameters[0] == "$zero"):
                    raise Exception("Fatal Error -- add single precision parameter 1 should be a valid coproc register at line:", self.globalLineNumber)
                if (not self.IsFlopRegister(self.parameters[1]) or self.parameters[1] == "$zero"):
                    raise Exception("Fatal Error -- add single precision parameter 2 should be a valid coproc register at line:", self.globalLineNumber)
                if (not self.IsFlopRegister(self.parameters[2]) or self.parameters[2] == "$zero"):
                    raise Exception("Fatal Error -- add single precision parameter 3 should be a valid coproc register at line:", self.globalLineNumber)

            case "div.s": #subtraction single precision
                #make sure there's 3 parameters (all registers)
                if (len(self.parameters) != 3):
                    raise Exception("Fatal Error -- divide single precision should have 3 parameters at line:", self.globalLineNumber)
                if (not self.IsFlopRegister(self.parameters[0]) or self.parameters[0] == "$zero"):
                    raise Exception("Fatal Error -- divide single precision parameter 1 should be a valid coproc register at line:", self.globalLineNumber)
                if (not self.IsFlopRegister(self.parameters[1]) or self.parameters[1] == "$zero"):
                    raise Exception("Fatal Error -- divide single precision parameter 2 should be a valid coproc register at line:", self.globalLineNumber)
                if (not self.IsFlopRegister(self.parameters[2]) or self.parameters[2] == "$zero"):
                    raise Exception("Fatal Error -- divide single precision parameter 3 should be a valid coproc register at line:", self.globalLineNumber)

            case "addi":  #addition of integers (immediate-specific)
                #make sure there's three parameters (two registers and one immediate)
                if (len(self.parameters) != 3):
                    raise Exception("Fatal Error -- addi should have 3 parameters at line:", self.globalLineNumber)
                if (not self.IsRegister(self.parameters[0]) or self.parameters[0] == "$zero" or self.IsFlopRegister(self.parameters[0])):
                    raise Exception("Fatal Error -- addi parameter 1 should be a valid register at line:", self.globalLineNumber)
                if ((not self.IsRegister(self.parameters[1]) and self.parameters[1].strip() != "$zero") or self.IsFlopRegister(self.parameters[1])):
                    raise Exception("Fatal Error -- addi parameter 2 should be a valid register at line:", self.globalLineNumber)
                try:
                    int(self.parameters[2])
                except ValueError:
                    raise Exception("Fatal Error -- addi parameter 3 should be either an intege at line:", self.globalLineNumber)

            case "subi":  #subtraction of integers (immediate-specific)
                #make sure there's three parameters (two registers and one immediate)
                if (len(self.parameters) != 3):
                    raise Exception("Fatal Error -- subi should have 3 parameters at line:", self.globalLineNumber)
                if (not self.IsRegister(self.parameters[0]) or self.parameters[0] == "$zero" or self.IsFlopRegister(self.parameters[0])):
                    raise Exception("Fatal Error -- subi parameter 1 should be a valid register at line:", self.globalLineNumber)
                if ((not self.IsRegister(self.parameters[1]) and self.parameters[1].strip() != "$zero") or self.IsFlopRegister(self.parameters[1])):
                    raise Exception("Fatal Error -- subi parameter 2 should be a valid register at line:", self.globalLineNumber)
                try:
                    int(self.parameters[2])
                except ValueError:
                    raise Exception("Fatal Error -- subi parameter 3 should be either an integer at line:", self.globalLineNumber)

            #custom (database-related) mnemonics are below here
            case "dbct": #database connect (needs 2 dest. registers (one for the conn and one for the cursor), and a file location register)
                #make sure there's three parameters (3 registers)
                if (len(self.parameters) != 3):
                    raise Exception("Fatal Error -- database connect should have 3 parameters at line:", self.globalLineNumber)
                if (not self.IsRegister(self.parameters[0]) and self.parameters[0] != "$zero" or self.IsFlopRegister(self.parameters[0])):
                    raise Exception("Fatal Error -- database connect parameter 1 should be a valid register at line:", self.globalLineNumber)
                if (not self.IsRegister(self.parameters[1]) and self.parameters[1] != "$zero" or self.IsFlopRegister(self.parameters[1])):
                    raise Exception("Fatal Error -- database connect parameter 2 should be a valid register at line:", self.globalLineNumber)
                if (not self.IsRegister(self.parameters[2]) and self.parameters[2] != "$zero" or self.IsFlopRegister(self.parameters[2])):
                    raise Exception("Fatal Error -- database connect parameter 3 should be a valid register at line:", self.globalLineNumber)

            case "dbcl": #database close (needs the registers with the db connect and the db cursor)
                #make sure there's two parameters (2 registers)
                if (len(self.parameters) != 2):
                    raise Exception("Fatal Error -- database close should have 2 parameters at line:", self.globalLineNumber)
                if (not self.IsRegister(self.parameters[0]) and self.parameters[0] != "$zero" or self.IsFlopRegister(self.parameters[0])):
                    raise Exception("Fatal Error -- database close parameter 1 should be a valid register at line:", self.globalLineNumber)
                if (not self.IsRegister(self.parameters[1]) and self.parameters[1] != "$zero" or self.IsFlopRegister(self.parameters[1])):
                    raise Exception("Fatal Error -- database close parameter 2 should be a valid register at line:", self.globalLineNumber)

            case "dbs": #database select (needs the rowCount dest. register with the db cursor register, sql query register, followed by all params (in registers))
                #make sure there's more than two parameters (3+ registers)
                if (len(self.parameters) < 3):
                    raise Exception("Fatal Error -- database select should have 3 or more parameters at line:", self.globalLineNumber)
                if (not self.IsRegister(self.parameters[0]) or self.parameters[0] == "$zero" or self.IsFlopRegister(self.parameters[0])):
                    raise Exception("Fatal Error -- database select parameter 1 should be a valid register at line:", self.globalLineNumber)
                if (not self.IsRegister(self.parameters[1]) or self.parameters[1] == "$zero" or self.IsFlopRegister(self.parameters[1])):
                    raise Exception("Fatal Error -- database select parameter 2 should be a valid register at line:", self.globalLineNumber)
                if (not self.IsRegister(self.parameters[2]) or self.parameters[2] == "$zero" or self.IsFlopRegister(self.parameters[2])):
                    raise Exception("Fatal Error -- database select parameter 3 should be a valid register at line:", self.globalLineNumber)
                for i in range(3, len(self.parameters)):
                    if(i >= len(self.parameters)):
                        break
                    if (not self.IsRegister(self.parameters[i]) and self.parameters[i] != "$zero" and not self.IsFlopRegister(self.parameters[i])):
                        raise Exception("Fatal Error -- database select parameter", i, "should be a valid register at line:", self.globalLineNumber)

            case "dbi": #database insert (needs the register with the db connect and the db cursor, sql query register, followed by all params)
                #make sure there's more than three parameters (4+ registers)
                if (len(self.parameters) < 4):
                    raise Exception("Fatal Error -- database insert should have 4 or more parameters at line:", self.globalLineNumber)
                if (not self.IsRegister(self.parameters[0]) and self.parameters[0] != "$zero" or self.IsFlopRegister(self.parameters[0])):
                    raise Exception("Fatal Error -- database insert parameter 1 should be a valid register at line:", self.globalLineNumber)
                if (not self.IsRegister(self.parameters[1]) and self.parameters[1] != "$zero" or self.IsFlopRegister(self.parameters[1])):
                    raise Exception("Fatal Error -- database insert parameter 2 should be a valid register at line:", self.globalLineNumber)
                if (not self.IsRegister(self.parameters[2]) and self.parameters[2] != "$zero" or self.IsFlopRegister(self.parameters[2])):
                    raise Exception("Fatal Error -- database insert parameter 3 should be a valid register at line:", self.globalLineNumber)
                for i in range(4, len(self.parameters)):
                    if(i >= len(self.parameters)):
                        break
                    if (not self.IsRegister(self.parameters[i]) and self.parameters[i] != "$zero" and not self.IsFlopRegister(self.parameters[0])):
                        raise Exception("Fatal Error -- database insert parameter", i, "should be a valid register at line:", self.globalLineNumber)

            case "dbd": #database delete (needs the register with the db conenct and the db cursor, sql query register, followed by all params)
                #make sure there's more than two parameters (3+ registers)
                if (len(self.parameters) < 3):
                    raise Exception("Fatal Error -- database delete should have 3 or more parameters at line:", self.globalLineNumber)
                if (not self.IsRegister(self.parameters[0]) and self.parameters[0] != "$zero" or self.IsFlopRegister(self.parameters[0])):
                    raise Exception("Fatal Error -- database delete parameter 1 should be a valid register at line:", self.globalLineNumber)
                if (not self.IsRegister(self.parameters[1]) and self.parameters[1] != "$zero" or self.IsFlopRegister(self.parameters[1])):
                    raise Exception("Fatal Error -- database delete parameter 2 should be a valid register at line:", self.globalLineNumber)
                if (not self.IsRegister(self.parameters[2]) and self.parameters[2] != "$zero" or self.IsFlopRegister(self.parameters[2])):
                    raise Exception("Fatal Error -- database delete parameter 3 should be a valid register at line:", self.globalLineNumber)
                for i in range(3, len(self.parameters)):
                    if(i >= len(self.parameters)):
                        break
                    if (not self.IsRegister(self.parameters[i]) and self.parameters[i] != "$zero" and not self.IsFlopRegister(self.parameters[i])):
                        raise Exception("Fatal Error -- database delete parameter", i, "should be a valid register at line:", self.globalLineNumber)

            case "dbt": #database table (needs the register with the db connect and the db cursor, sql query register)
                #make sure there's more than two parameters (3+ registers)
                if (len(self.parameters) != 3):
                    raise Exception("Fatal Error -- database table should have 3 parameters at line:", self.globalLineNumber)
                if (not self.IsRegister(self.parameters[0]) and self.parameters[0] != "$zero" or self.IsFlopRegister(self.parameters[0])):
                    raise Exception("Fatal Error -- database table parameter 1 should be a valid register at line:", self.globalLineNumber)
                if (not self.IsRegister(self.parameters[1]) and self.parameters[1] != "$zero" or self.IsFlopRegister(self.parameters[1])):
                    raise Exception("Fatal Error -- database table parameter 2 should be a valid register at line:", self.globalLineNumber)
                if (not self.IsRegister(self.parameters[2]) and self.parameters[2] != "$zero" or self.IsFlopRegister(self.parameters[2])):
                    raise Exception("Fatal Error -- database table parameter 3 should be a valid register at line:", self.globalLineNumber)

            case "dbu": #database update (needs the register with the db connect and the db cursor, sql query register, followed by all params)
                #make sure there's more than three parameters (4+ registers)
                if (len(self.parameters) < 4):
                    raise Exception("Fatal Error -- database update should have 4 or more parameters at line:", self.globalLineNumber)
                if (not self.IsRegister(self.parameters[0]) and self.parameters[0] != "$zero" or self.IsFlopRegister(self.parameters[0])):
                    raise Exception("Fatal Error -- database update parameter 1 should be a valid register at line:", self.globalLineNumber)
                if (not self.IsRegister(self.parameters[1]) and self.parameters[1] != "$zero" or self.IsFlopRegister(self.parameters[1])):
                    raise Exception("Fatal Error -- database update parameter 2 should be a valid register at line:", self.globalLineNumber)
                if (not self.IsRegister(self.parameters[2]) and self.parameters[2] != "$zero" or self.IsFlopRegister(self.parameters[2])):
                    raise Exception("Fatal Error -- database update parameter 3 should be a valid register at line:", self.globalLineNumber)
                for i in range(4, len(self.parameters)):
                    if(i >= len(self.parameters)):
                        break
                    if (not self.IsRegister(self.parameters[i]) and self.parameters[i] != "$zero"):
                        raise Exception("Fatal Error -- database update parameter", i, "should be a valid register at line:", self.globalLineNumber)

            case "dbit": #database iterate (needs the row number, register with the db cursor register, followed by all params (in registers))
                #make sure there's more than three parameters (3+ registers)
                if (len(self.parameters) < 4):
                    raise Exception("Fatal Error -- database iterate should have 4 or more parameters at line:", self.globalLineNumber)
                if (not self.IsRegister(self.parameters[0]) or self.parameters[0] == "$zero" or self.IsFlopRegister(self.parameters[0])):
                    raise Exception("Fatal Error -- database iterate parameter 1 should be a valid register at line:", self.globalLineNumber)
                if (not self.IsRegister(self.parameters[1]) or self.parameters[1] == "$zero" or self.IsFlopRegister(self.parameters[1])):
                    raise Exception("Fatal Error -- database iterate parameter 2 should be a valid register at line:", self.globalLineNumber)
                for i in range(2, len(self.parameters)):
                    if(i >= len(self.parameters)):
                        break
                    if (not self.IsRegister(self.parameters[i]) and self.parameters[i] != "$zero" and i != 1):
                        raise Exception("Fatal Error -- database iterate parameter", i, "should be a valid register at line:", self.globalLineNumber)

            case _: #default case, throw an error (not a valid pseudo instruction)
                raise Exception("Fatal Error -- unknown pseudo instruction at line:", self.globalLineNumber , self.content)

    #function to determine if a string (parameter) is any valid register (not including $zero)
    def IsRegister(self, parameter: str) -> bool:
        registers: list[str] = ["$at", "$v0", "$v1", "$a0", "$a1", "$a2", "$a3", "$t0", "$t1",
                               "$t2", "$t3", "$t4", "$t5", "$t6", "$t7", "$t8", "$t9", "$s0", "$s1",
                               "$s2", "$s3", "$s4", "$s5", "$s6", "$s7", "$s8", "$s9", "$k0", "$k1",
                               "$gp", "$sp", "$ra", "$fp", "$f0", "$f1", "$f2", "$f3", "$f4", "$f5",
                               "$f6", "$f7", "$f8", "$f9", "$f10", "$f11", "$f12", "$f13", "$f14", "$f15",
                               "$f16", "$f17", "$f18", "$f19", "$f20", "$f21", "$f22", "$f23", "$f24", "$f25",
                               "$f26", "$f27", "$f29", "$f30", "$f31"]  # reserved register names

        if(parameter.strip() in registers):
            return True
        return False

    #function to determine if a string (parameter) is a valid flop register
    def IsFlopRegister(self, parameter: str) -> bool:
        registers: list[str] = ["$f0", "$f1", "$f2", "$f3", "$f4", "$f5","$f6", "$f7", "$f8", "$f9", "$f10",
                                "$f11", "$f12", "$f13", "$f14", "$f15","$f16", "$f17", "$f18", "$f19", "$f20",
                                "$f21", "$f22", "$f23", "$f24", "$f25","$f26", "$f27", "$f29", "$f30", "$f31"]  # reserved register names

        if (parameter.strip() in registers):
            return True
        return False

    #function to determine if a string (parameter) can be turned into a number
    #cannot be a decimal (can't contain '.') and not negative
    def IsWholeNonNegNumber(self, parameter: str) -> bool:
        if('.' in parameter):
            return False
        if('-' in parameter):
            return False
        try:
            int(parameter)
            return True
        except ValueError:
            return False

    #function to determine if string (parameter) can be turned into a number
    #cannot be a decimal (can't contain '.')
    def IsWholeNumber(self, parameter: str) -> bool:
        if('.' in parameter):
            return False
        try:
            int(parameter)
            return True
        except ValueError:
            return False

#special class used during the .data segment
class DataLine:
    def __init__(self, content: str, lineNumber: int, globalLineNumber: int):
        #get the variable name and value, when the data lines are iterated through,
        #the variable name is searched for and the value is retrieved
        self.content = content
        self.lineNumber = lineNumber
        self.globalLineNumber = globalLineNumber

        if(content.strip().startswith(".data")):
            self.type: str = "Data Segment Header"
            self.contentName = None
            self.contentType = None
            self.value = None
            self.length = None
        else:
            self.type: str = "Data"
            #this is the name of the variable of the line (used so we can find this line and access the memory in value)
            self.contentName: str = self.GetDataName(self.content)

            #content is the .word, .asciiz, etc. of the line
            self.contentType: str = self.GetDataType(self.content)

            #value is just the hex of the base memory address
            self.value: hex = self.GetDataValue(self.content)

    #function to determine if a line is the .data segment
    def IsDataSegment(self, line: str) -> bool:
        line = line.strip()
        if (len(line) < 5 or len(line) > 5):
            return False
        return (line[0] == '.' and line[1] == 'd' and line[2] == 'a' and line[3] == 't' and line[4] == 'a')

    #function to get the variable name of the .data variable
    #does not check if the name has already been taken, will be checked by the Program object as overhead
    def GetDataName(self, line: str) -> str:
        name: str = line.strip().split(':')[0] #anything before the colon is technically the name

        #ensure that the name does not start with '.' or a number
        badStart: list[str] = ['.', '0', '1', '2', '3', '4', '5', '6', '7',
                               '8', '9', '-', '$', '&', '@', '!', '%', '^',
                               '*', '(', ')', '[', ']', '{', '}', ';', ':',
                               '\'', '\"', '|', '\\', '/', '?', '>', ',',
                               '<', '=', '+', '~', '`']
        if(name[0] in badStart):
            raise Exception("Fatal Error -- Data name " + name + " starts with invalid character at line:", self.globalLineNumber)

        #ensure that the name does not contain certain special characters or whitespace
        badCharacters: list[str] = [' ', '-', '!', '@', '%', '^', '&', '*',
                                    '(', ')', '{', '}', '[', ']', ':', ';',
                                    '\'', '\'', '\\', '|', ',', '.', '/',
                                    '?', '`', '~', '+', '=']
        for character in name:
            if(character in badCharacters):
                raise Exception("Fatal Error -- Data name " + name + " contains invalid character at line:", self.globalLineNumber)

        #ensure that the name is valid (not a reserved phrase) before rturning it (otherwise raise a Fatal Error)
        badNames: list[str] = ["$zero", "$at", "$v0", "$v1", "$a0", "$a1", "$a2", "$a3", "$t0", "$t1",
                               "$t2", "$t3", "$t4", "$t5", "$t6", "$t7", "$t8", "$t9", "$s0", "$s1",
                               "$s2", "$s3", "$s4", "$s5", "$s6", "$s7", "$s8", "$s9", "$k0", "$k1",
                               "$gp", "$sp", "$ra", "$fp"] #reserved register names
        if(name in badNames):
            raise Exception("Fatal Error -- Data name " + name + " is a reserved word at line:", self.globalLineNumber)

        return name

    #function to get the datatype of the .data variable
    def GetDataType(self, line: str):
        if(".asciiz" in line):
            return ".asciiz"
        elif(".word" in line):
            return ".word"
        elif(".float" in line):
            return ".float"
        elif(".space" in line):
            return ".space"
        else:
            raise Exception("Fatal Error -- .data type not valid at line:", self.globalLineNumber)

    #function to get the value of the .data variable
    def GetDataValue(self, line: str) -> hex: #return a memory address
        memManager: MemoryManager._MemoryManagerImpl = MemoryManager()

        #based on the type, different actions can occur
        if (self.contentType == ".asciiz"):
            memManager.add_address(value=line.strip().split(self.contentType)[1][2:-1])
            return memManager.mostRecentAddress

        elif(self.contentType == ".word"):
            returnAddress: hex = hex(int(str(memManager.mostRecentAddress), 16) + 4) #get the address for return (base address in case this is an array)
            for word in line.strip().split(self.contentType)[1].strip().split(','):
                memManager.add_address(value=word)
            return returnAddress

        elif((self.contentType == ".space")):
            #get the size and round up to the nearest number divisible by four
            size: int = int(line.strip().split(self.contentType)[1].strip())
            while (size % 4 != 0):
                size += 1
            #create size // 4 new memory locations
            returnAddress: hex = hex(int(str(memManager.mostRecentAddress), 16) + 4)  #get the address for return
            for i in range(size//4):
                memManager.add_address() #uninitialized, (value=NoneType by default)
            return returnAddress

        elif (self.contentType == ".float"):
            memManager.add_address(value=float(line.strip().split(self.contentType)[1].strip()))
            return memManager.mostRecentAddress

        return 0 #hopefully never happens

import typing_extensions #used to access Any as a datatype

#class to handle register file functionality
#this includes the return register, zero register etc
class RegisterFile:
    def __init__(self):
        self.ZERO: Register = Register("$zero") #zero register
        self.AT: Register = Register("$at") #at register
        self.V0: Register = Register("$v0") #v0 register
        self.V1: Register = Register("$v1") #v1 register
        self.A: list[Register] = [Register("$a0"), Register("$a1"), Register("$a2"), Register("$a3")] #a0-a3 registers
        self.T: list[Register] = [Register("$t0"), Register("$t1"), Register("$t2"), Register("$t3"), Register("$t4"),
                                  Register("$t5"), Register("$t6"), Register("$t7"), Register("$t8"), Register("$t9")] #t0-t9 registers
        self.S: list[Register] = [Register("$s0"), Register("$s1"), Register("$s2"), Register("$s3"),
                                  Register("$s4"), Register("$s5"), Register("$s6"), Register("$s7")]  #s0-s7 registers
        self.K0: Register = Register("$k0") #k0 register
        self.K1: Register = Register("$k1") #k1 register
        self.GP: Register = Register("$gp") #gp register
        self.SP: Register = Register("$sp") #sp register
        self.FP: Register = Register("$fp") #fp register
        self.RA: Register = Register("$ra") #return address register
        self.ProgramCounter: int = 0 #integer that holds the current instruction address (will be the line number here)
        self.F: list[FloatRegister] = [FloatRegister("$f0"), FloatRegister("$f1"), FloatRegister("$f2"), FloatRegister("$f3"),
                                       FloatRegister("$f4"), FloatRegister("$f5"), FloatRegister("$f6"), FloatRegister("$f7"),
                                       FloatRegister("$f8"), FloatRegister("$f9"), FloatRegister("$f10"), FloatRegister("$f11"),
                                       FloatRegister("$f12"), FloatRegister("$f13"), FloatRegister("$f14"), FloatRegister("$f15"),
                                       FloatRegister("$f16"), FloatRegister("$f17"), FloatRegister("$f18"), FloatRegister("$f19"),
                                       FloatRegister("$f20"), FloatRegister("$f21"), FloatRegister("$f22"), FloatRegister("$f23"),
                                       FloatRegister("$f24"), FloatRegister("$f25"), FloatRegister("$f26"), FloatRegister("$f27"),
                                       FloatRegister("$f28"), FloatRegister("$f29"), FloatRegister("$f30"), FloatRegister("$f31")] #f0-f31 float registers
        self.HI: FloatRegister = FloatRegister("$hi") #Hi register (set to float in the case it is used with floats) (only access from mfhi)
        self.LO: FloatRegister = FloatRegister("$lo") #Lo register (set to float in the case it is used with floats) (only access from mflo)
        self.Fcc = False #condition flag for coproc 1

    #function to use the zero register
    def GetZeroRegister(self) -> int:
        return 0

    #function to get the stored value of the Lo register
    def GetLoRgister(self):
        return self.LO.value

    #function to get the stored value of the Hi register
    def GetHiRegister(self):
        return self.HI.value

    #function to get the stored value of the v0 (syscall) register
    def GetSyscallRegister(self):
        return self.V0.value

    #function to set the stored value of the v0 (syscall) register
    def SetSyscallRegister(self, value: int):
        self.V0.value = value

    #function to get the stored value of a given saved register
    def GetSavedRegister(self, index: int):
        if (index < 0 or index > 7):
            raise Exception("Fatal Error -- S register", index, "is not valid")
        return self.S[index].value

    #function to set the stored value of a given saved register
    def SetSavedRegister(self, index: int, value):
        if (index < 0 or index > 7):
            raise Exception("Fatal Error -- S register", index, "is not valid")
        self.S[index].value = value

    #function to get the stored value of a given temporary register
    def GetTempRegister(self, index: int):
        if (index < 0 or index > 9):
            raise Exception("Fatal Error -- T register", index, "is not valid")
        return self.T[index].value

    #function to set the stored value of a given temporary register
    def SetTempRegister(self, index: int, value):
        if (index < 0 or index > 9):
            raise Exception("Fatal Error -- T register", index, "is not valid")
        self.T[index].value = value

    #function to get the stored value of a given flop register
    def GetFlopRegister(self, index: int):
        if(index < 0 or index > 31):
            raise Exception("Fatal Error -- F register", index,"is not valid")
        return self.F[index].value

    #function to set the stored value of a given flop register
    def SetFlopRegister(self,index: int, value: float):
        if (index < 0 or index > 31):
            raise Exception("Fatal Error -- F register", index, "is not valid")
        self.F[index].value = value

    #function to get the value of the program counter
    def GetProgramCounter(self) -> int:
        return self.ProgramCounter

    #function to set the value in the return address register
    def SetReturnAddressRegister(self, val: int):
        self.ProgramCounter = val

    #function to get the value of the return address register
    def GetReturnAddressRegister(self) -> int:
        return self.RA.value

#internal class used to mimic the registers
class Register:
    def __init__(self, name: str):
        self.value: typing_extensions.Any = 0
        self.name = name

#internal class used to mimic the coproc float registers
class FloatRegister:
    def __init__(self, name: str):
        self.value: float = 0.0
        self.name = name

#public singleton class used to represent all memory address-value pairs
class MemoryManager:
    _Instance = None

    #called before __init__
    def __new__(cls):
        if not cls._Instance:
            cls._Instance = cls._MemoryManagerImpl()
        return cls._Instance

    #class used as the implementation of the above singleton
    class _MemoryManagerImpl:
        def __init__(self):
            self.mostRecentAddress: hex = -4
            self.memory: dict[hex, typing_extensions.Any] = dict()
            self.memoryType: dict[hex, str] = dict()
            self.memoryAvail: dict[hex, bool] = dict()
            self.results = None #storage for results of a select query

        #function to add a new address to the dict
        def add_address(self, value: typing_extensions.Any = None, memType: str = "static"):
            if(memType != "db"):
                self.memory[hex(int(str(self.mostRecentAddress), 16) + 4)] = value
                self.memoryType[hex(int(str(self.mostRecentAddress), 16) + 4)] = memType
                self.memoryAvail[hex(int(str(self.mostRecentAddress), 16) + 4)] = False #only applies for db memory
                self.mostRecentAddress = hex(int(str(self.mostRecentAddress), 16) + 4)
            else: #database allocated memory segments
                self.memory[hex(int(str(self.mostRecentAddress), 16) + 4)] = value
                self.memoryType[hex(int(str(self.mostRecentAddress), 16) + 4)] = memType
                self.memoryAvail[hex(int(str(self.mostRecentAddress), 16) + 4)] = True #starts uninitialized
                self.mostRecentAddress = hex(int(str(self.mostRecentAddress), 16) + 4)

        #function to get the value stored at an address
        def get_address(self, address: hex):
            return self.memory[address]

        #function to get the type of memory stored at an address
        def get_type(self, address: hex) -> str:
            return str(self.memoryType[address])

        #does this class contain a given address
        def containsAddress(self, address: hex):
            return address in self.memory

        #set a given address in hex to a value
        def setAddress(self, address: hex, value: typing_extensions.Any = None):
            self.memory[address] = value
            self.memoryAvail[address] = False #no matter what when setting, it becomes unavailable

        #function to set all db memory type to available (called at the start of all dbit instructions)
        def setAllAvailable(self):
            address: hex = hex(0)
            while (self.containsAddress(address)):
                if(self.memoryType[address] == "db"):
                    self.memoryAvail[address] = True
                address = hex(int(address, 16) + 4)

        #function to get the first available db memory slot
        def getFirstAvailable(self) -> hex:
            address: hex = hex(0)
            while (self.containsAddress(address)):
                if(self.memoryType[address] == "db" and self.memoryAvail[address]):
                    return address
                address = hex(int(address, 16) + 4)

        #function to determine if there is an available db memory slot
        def hasAvailable(self) -> bool:
            address: hex = hex(0)
            while (self.containsAddress(address)):
                if (self.memoryType[address] == "db" and self.memoryAvail[address]):
                    return True
                address = hex(int(address, 16) + 4)
            return False

        #function to trigger a memory dump (debugging purposes --> print all memory-value pairs)
        def memoryDump(self):
            address: hex = hex(0)
            while(self.containsAddress(address)):
                print(address, ":" + str(self.get_address(address)), ":\n")
                address = hex(int(address, 16) + 4)

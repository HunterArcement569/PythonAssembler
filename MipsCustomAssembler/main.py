import os #needed to get all files in the 'Assembly Files' subdirectory
from Program import Program #program class used for storing the list of lines and flow of control of the program
from RegisterFile import RegisterFile #register file class used to mimic the register file in assembly
import traceback #used to see where in python and assembly programs exceptions appear

#main function of the running program
def main():
    #call the function to get the assembly file we are to run
    asmFile = SelectProgram()

    #check if the program meets syntax requirements, and create the 'runnable' program object (done at the same time)
    try:
        programObject: Program = Program(asmFile, RegisterFile())
    except Exception as e:
        tb = e.__traceback__
        tb_info = traceback.extract_tb(tb)
        last_trace = tb_info[-1]
        print(f"File: {last_trace.filename}, Line: {last_trace.lineno}, In Function: {last_trace.name}")
        print("\nAssembly Program Invalid\n", str(e), "\nExiting Program")
        return #end the program

    #run the program now that it has loaded
    try:
        print("\nAssembled Successfully!\n")
        result: bool = programObject.RunAssemblyProgram()
    except Exception as e:
        tb = e.__traceback__
        tb_info = traceback.extract_tb(tb)
        last_trace = tb_info[-1]
        print(f"File: {last_trace.filename}, Line: {last_trace.lineno}, In Function: {last_trace.name}")
        print("\nProgram Error --\n", str(e), "\nExiting Program")
        return #end the program

    if(not result):
        print("\nProgram exited, dropped off bottom")

    print("\nAssembler Program Concluded")

#function to get input from the user on which .asm file in this project directory they wish to run
def SelectProgram():
    #go through and print all the file names in the Assembly Files directory
    directory = 'Assembly Files'
    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))] #list of files in the directory
    while(True):
        counter: int = 1
        for file in files:
            print(f'{counter}. {file}')
            counter += 1
        fileNumber: str = input('Enter the number next to the file to proceed: ')
        try:
            if(int(fileNumber) in range(1, counter)):
                return open(directory + '/' + files[int(fileNumber) - 1], 'r')
            else:
                raise ValueError
        except ValueError:
            print('\nInvalid input -- must be an integer from the listing\n')

#call to the main function of the program
if __name__ == '__main__':
    main()
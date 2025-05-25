 .text                      # Where the code methods/instructions go
main:
    li $v0, 4               # Put a value 4 into the $v0 register to instruct a print statement
    la $a0, variableName    # Load the address of the variableName into the $a0 register
    syscall                 # Print greeting. The print is indicated by
                            # $v0 having a value of 4, and the string to
                            # print is stored at the address in $a0.
    li $v0, 10              # Load a 10 (halt) into $v0
    syscall                 # The program ends.
.data                       # Define the program data.
variableName: .asciiz "Hello World"    # The string to print.

#we store the message in a space in memory with a memory address
#then we instruct the v0 register to print, but it needs to know what to print
#so we tell the a0 register the address of the message memory address using the variable's name
#the value 10 placed into the v0 register is instructions to end the program 
#the syscall is a call to read the instructions as they are in each of the registers so the first one is to print and the second is to end the run cycle
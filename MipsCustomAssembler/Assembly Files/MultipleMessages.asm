#the first thing we do is declare the main section of the program
.text
main: 
	#the next thing we do it to add the value 4 (print) into the v0 register
	li $v0, 4
	#now we give the address of the first message to the a0 register
	la $a0, MessageOne
	#perform syscall to print the first message
	syscall
	
	#now we give the address of the second message to the a0 register 
	la $a0, MessageTwo
	#now syscall  to run instructions
	syscall
	
	#set the v0 register to 10 to give instructions to end the program
	li $v0, 10
	#now syscall to end the run
	syscall
	
#data area to set up the messages in memory
.data
#variables are stored as varName: value and if that value is a string use the .asciiz to translate into ascii for the assembler
MessageOne: .asciiz "My first true Assembly Program! \n"    #the first string message to be printed, has a newline character
							    #to put the next message on the second line
MessageTwo: .asciiz "All this does is print two seperate messages that are stored in memory"  #the second message

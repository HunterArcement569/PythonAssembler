.data
	#message addresses
	exitMessage: .asciiz "\nExitting the program!"
	firstPrompt: .asciiz "Enter 1 to add, 2 to subtract, 3 to multiply, or 4 to divide: "
	secondPrompt: .asciiz "\nEnter the first number: "
	thirdPrompt: .asciiz "\nEnter the second number: "
	resultMessage: .asciiz "\nThe result was: "
.text
j INPUT #start at the input section to get the user's input for an integer

INPUT: #input section for the initial section jump address decision
	#prompt the user
	li $v0, 4
	la $a0, firstPrompt
	syscall
	
	#get the actual number
	li $v0, 5
	syscall
	move $t1, $v0 #set the t1 register to the input, t0 will be used for the conditional jump
	
	j COND #jump to the condition section

COND: #condition set to determine which branch(es) to jump to
	beq $t1 , 1 , ADD # if (t1 == 1) go to ADD
	beq $t1 , 2 , SUB # if (t1 == 2) go to SUB
	beq $t1 , 3 , MUL # if (t1 == 3) go to MUL
	beq $t1 , 4 , DIV # if (t1 == 4) go to DIV

ADD: #addition section
	#Get the user's second and third inputs
	#second input
	li $v0, 4
	la $a0, secondPrompt
	syscall
	
	#get the actual number
	li $v0, 5
	syscall
	move $t1, $v0 #set the t1 register to the input, t0 will be used to print the output of the operation
	
	#third input
	li $v0, 4
	la $a0, thirdPrompt
	syscall
	
	#get the actual number
	li $v0, 5
	syscall
	move $t2, $v0 #set the t2 register to the input, t0 will be used to add the numbers in place
	
	#add the numbers
	add $t0 , $t1 , $t2
	
	#print the result message 
	li $v0, 4
	la $a0, resultMessage
	syscall
	
	#print the result from the register t0
	li $v0, 1
    move $a0, $t0
    syscall
        
    j EXIT #end the program

SUB: #subtraction section
	#Get the user's second and third inputs
	#second input
	li $v0, 4
	la $a0, secondPrompt
	syscall
	
	#get the actual number
	li $v0, 5
	syscall
	move $t1, $v0 #set the t1 register to the input, t0 will be used to print the output of the operation
	
	#third input
	li $v0, 4
	la $a0, thirdPrompt
	syscall
	
	#get the actual number
	li $v0, 5
	syscall
	move $t2, $v0 #set the t2 register to the input, t0 will be used to subtract the numbers in place
	
	#subtract the numbers
	sub  $t0 , $t1 , $t2
	
	#print the result message 
	li $v0, 4
	la $a0, resultMessage
	syscall
	
	#print the result from the register t0
	li $v0, 1
    move $a0, $t0
    syscall
        
    j EXIT #end the program

MUL: #multiplication section
	#Get the user's second and third inputs
	#second input
	li $v0, 4
	la $a0, secondPrompt
	syscall
	
	#get the actual number
	li $v0, 5
	syscall
	move $t1, $v0 #set the t1 register to the input, t0 will be used to print the output of the operation
	
	#third input
	li $v0, 4
	la $a0, thirdPrompt
	syscall
	
	#get the actual number
	li $v0, 5
	syscall
	move $t2, $v0 #set the t2 register to the input, t0 will be used to multiply the numbers in place
	
	#multiply the numbers
	mul   $t0 , $t1 , $t2
	
	#print the result message 
	li $v0, 4
	la $a0, resultMessage
	syscall
	
	#print the result from the register t0
	li $v0, 1
    move $a0, $t0
    syscall
        
    j EXIT #end the program

DIV: #division section
	#Get the user's second and third inputs
	#second input
	li $v0, 4
	la $a0, secondPrompt
	syscall
	
	#get the actual number
	li $v0, 5
	syscall
	move $t1, $v0 #set the t1 register to the input, t0 will be used to print the output of the operation
	
	#third input
	li $v0, 4
	la $a0, thirdPrompt
	syscall
	
	#get the actual number
	li $v0, 5
	syscall
	move $t2, $v0 #set the t2 register to the input, t0 will be used to divide the numbers in place
	
	#divide the numbers
	div  $t0 , $t1 , $t2
	
	#print the result message 
	li $v0, 4
	la $a0, resultMessage
	syscall
	
	#print the result from the register t0
	li $v0, 1
    move $a0, $t0
    syscall
        
    j EXIT #end the program

EXIT: #exit section
	li $v0, 4
	la $a0, exitMessage
	syscall
	li $v0, 10
	syscall
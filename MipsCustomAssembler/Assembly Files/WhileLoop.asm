.data
	#message addresses
	exitMessage: .asciiz "\nExitting the program!"
	firstPrompt: .asciiz "\nEnter 1 to add, 2 to subtract, 3 to multiply, 4 to divide, or 5 to exit: "
	secondPrompt: .asciiz "\nEnter the first number: "
	thirdPrompt: .asciiz "\nEnter the second number: "
	resultMessage: .asciiz "\nThe result was: "
.text
j LOOP #start at the loop region to get the user's input for an integer

LOOP: #looped region, the if will determine if the code jumps back to here
	j INPUT #go to the input section to determine if the loop persists or terminates
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
	beq $t1, 1, ADD # if (t1 == 1) go to ADD
	beq $t1, 2, SUB # if (t1 == 2) go to SUB
	beq $t1, 3, MUL # if (t1 == 3) go to MUL
	beq $t1, 4, DIV # if (t1 == 4) go to DIV
	beq $t1, 5, EXIT #if (t1 == 5) go to the EXIT, loop terminates

ADD: #addistion section
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
        
    j LOOP #restart the loop to test input to either persist loop or terminate

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
        
    j LOOP #restart the loop to test input to either persist loop or terminate

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
	mul $t0 , $t1 , $t2
	
	#print the result message 
	li $v0, 4
	la $a0, resultMessage
	syscall
	
	#print the result from the register t0
	li $v0, 1
    move $a0, $t0
    syscall
        
    j LOOP #restart the loop to test input to either persist loop or terminate

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
        
    j LOOP #restart the loop to test input to either persist loop or terminate

EXIT: #exit section
	li $v0, 4
	la $a0, exitMessage
	syscall
	li $v0, 10
	syscall

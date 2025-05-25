#Hunter Arcement
#C00490617
#CMPS 351
#PA4

#Notes -- 3 functions + main with one loop in every 

.data
	ExitMessage: .asciiz "\nExitting Program!"
	ErrorMessage: .asciiz "\nInvalid selection - please try again."
	SquareRootPrompt: .asciiz "\nSquare root of which number: "
	SquareRootMessage: .asciiz "\nApproximate square root of "
	PrimeNumberPrompt: .asciiz "\nWhich Prime number: "
	PrimeNumberMessage: .asciiz "\nPrime Number "
	PellNumberPrompt: .asciiz "\nWhich Pell number: "
	PellNumberMessage: .asciiz "\nPell Number "
	MainPrompt: .asciiz "\nEnter 1 for Pell sequence, 2 for Nth Prime, or 3 for approximate square root (0 quits): "
	
	ZERO: .float 0.0
	PT5: .float 0.5
	PT01: .float 0.01
	
.text
.globl main

main: #main function label and start of the program, this happens before the do-while loop
#start by setting the choice to 1 to start the do-while loop
	#using the $t0 as the user input register
	add $t0 , $zero , 1
	#using the $f0 for the square number function user input
	l.s $f0 ,ZERO
	
mainLoop: #do-while loop label for the main function
#start by checking what selection was made by the user
	#if the selection was 0, jump unconditionally to the exit label
	beqz $t0 , exit
	
	#if the selection was 1, jump and link to the pell function call segment
	beq $t0 , 1 , pellCall
	
	#if the selection was 2, jump and link to the prime number function call segment
	beq $t0 , 2 , primeCall
	
	#if the selection was 3, jump and link to the prime number function call segment
	beq $t0 , 3 , squareRootCall
	
	#otherwise the selection is invalid, jump to the error segment and then jump to the end of the do-while for user input
	bltz $t0 , Error
	bgt $t0 , 3 , Error
	
pellCall: #label responsible for calling the pell function and jumping to the user input segment
	#print the prompt and get the user input for the argyment
	#print the prompt
	li $v0, 4
	la $a0, PellNumberPrompt
	syscall

	#get the input
	li $v0, 5
	syscall
	move  $a0, $v0 #the input goes into the argument register to be sent to the function
	
	#go to the function
	jal pell
	
	#now use the result placed into the $v1 register
	#print the message 
	li $v0, 4
	la $a0, PellNumberMessage
	syscall
	#print the number return value currently in the $s1
	li $v0, 1
	move $a0 , $s1
    syscall
        
    #go to the user input which will go back to the main loop afterwards
    j userInput

primeCall: #label responsible for calling the prime number function and jumping to the user input segment
	#print the prompt and get the user input for the argyment
	#print the prompt
	li $v0, 4
	la $a0, PrimeNumberPrompt
	syscall

	#get the input
	li $v0, 5
	syscall
	move  $a0, $v0 #the input goes into the argument register to be sent to the function
	
	#go to the function
	jal prime
	
	#now use the result placed into the $s1 register
	#print the message 
	li $v0, 4
	la $a0, PrimeNumberMessage
	syscall
	#print the number return value currently in the $s1
	li $v0, 1
	move $a0 , $s1
    syscall
        
    #go to the user input which will go back to the main loop afterwards
    j userInput

squareRootCall:#label responsible for calling the square root function and jumping to the user input segment
	#print the prompt and get the user input for the argyment
	#print the prompt
	li $v0, 4
	la $a0, SquareRootPrompt
	syscall

	#get the input
	li $v0, 6
	syscall #the input goes into the first float register, used as an arg for the function --> $f0
	
	#go to the function
	jal squareRoot
	
	#now use the result placed into the $v1 register
	#print the message 
	li $v0, 4
	la $a0, SquareRootMessage
	syscall
	
	#print the number return value currently in the $f12
	li $v0, 2
    syscall
        
    #go to the user input which will go back to the main loop afterwards
    j userInput

Error:#label responsible for error display and jumping to the user input segment
	#print the error message
	li $v0, 4
	la $a0, ErrorMessage
	syscall
	
	#jump to the user input section no strings attached
	j userInput

userInput: #label responsible for printing the main prompt and getting the user's integer input and storing it in $t0
	#print the prompt
	li $v0, 4
	la $a0, MainPrompt
	syscall

	#get the input
	li $v0, 5
	syscall
	move  $t0, $v0 

	#jump to the start of the do-while loop if and only if the choice is NOT 0
	bnez $t0 , mainLoop
	#otherwise exit the program much like if the decision was 0
	beqz $t0 , exit

pell: #pell function label
	#if the argument is 0 then return 0
	#if the argument is 1 then return 1
	beqz $a0 , FirstPellIf
	beq $a0 , 1 , SecondPellIf
	
	#otherwise we set X = 1, Y = 0, Z = 0
	#Let the $t1 be x, $t2 be Y, $t3 be Z
	add $t1 , $zero , 1
	add $t2 , $zero , $zero
	add $t3 , $zero , $zero 
	#set the i = 1, let $t4 be the for increment
	add $t4 , $zero , 1
	
	#start of the while loop is here, jump to the start of the loop segment
	j pellLoop
	
FirstPellIf:
	add $s1 , $zero , $zero
	jr $ra
SecondPellIf:
	add $s1 , $zero , 1
	jr $ra
ThirdPellIf:
	#clear the registers
	add $t1 , $zero , $zero
	add $t2 , $zero , $zero
	add $t4 , $zero , $zero
	add $t5 , $zero , $zero
	add $t7 , $zero , $zero
	#set the s1 register for the print post function
	move $s1 , $t3
	#clear the Z register
	add $t3 , $zero , $zero
	#jump to the ra register
	jr $ra

pellLoop: #for loop label for the pell function
	#Z = 2*X + Y;
	mul $t5 , $t1 , 2
	add $t3 , $t5 , $t2 
	#Y = X;
	add $t2 , $zero , $t1
	#X = Z;
	add $t1 , $zero , $t3
	
	#increment the i then if the i = $a0, end the loop
	add $t4 , $t4 , 1
	beq $t4 , $a0 , ThirdPellIf
	#otherwise return to the loop 
	j pellLoop

prime: #prime number function label
	#set up the needed registers, $t1 will be P , $t2 will be C , $t3 will be Prime boolean, set either to 0 or 1
	add $t1 , $zero , 2
	add $t2 , $zero , 1
	add $t3 , $zero , $zero
	
	#start the loop, go into the segment sequentially

primeLoop: #while loop label for the prime number function

	#check if we can leave the loop
	beq $t2 , $a0 , PostWhilePrime
	#otherwise perform the loop
	#increment the P variable, set the PrimeBoolean to true (1)
	add $t1 , $t1 , 1
	add $t3 , $zero , 1
	
	#sequentially start the for loop
	#set the $t4 to testDiv increment for the for loop
	add $t4 , $zero , 2
	
primeFor: #for loop label for the prime number function
	#check for the label jump
	beq $t4 , $t1 , PostForPrime
	
	#if the $t1 % $t4 = 0 go to the primeForCheck, otherwise go back to the for loop
	div $t1 , $t4 
	mfhi $t5
	beqz $t5 , primeForCheck
	add $t4 , $t4 , 1
	j primeFor
	
primeForCheck:
	#set the prime to false (0)
	add $t3 , $zero , $zero
	#jump to the while toop
	j PostForPrime
	
PostForPrime:
	#if the $t3 boolean is 1
	beq $t3 , 1 , PostForTrue
	#otherwise return to the while loop
	j primeLoop
	
PostForTrue:
	#increment C then go to the while loop
	add $t2 , $t2 , 1
	j primeLoop
	
PostWhilePrime:
	#clear all registers after setting the $s1 then jump to the ra register
	add $s1 , $t1 , $zero
	
	add $t1 , $zero , $zero
	add $t2 , $zero , $zero
	add $t3 , $zero , $zero
	add $t4 , $zero , $zero
	add $t5 , $zero , $zero
	
	jr $ra

squareRoot: #square root number function label
	#let $f1 be X , N is currently $f0
	lwc1 $f1 , PT5
	lwc1 $f4 , PT01
	lwc1 $f5 , PT5
	
	#start the loop sequentially

squareRootLoop: #while loop label for the square root number function#check the condition first
	#square X - N
	mul.s $f6 , $f1 , $f1
	sub.s $f7 , $f6 , $f0
	#take the absolute value of the $f1 register and set it to the $f2 register for the checks
	abs.s $f2 , $f7
	c.lt.s $f4 , $f2
	bc1t squareRootWhile
	
	#otherwise return $f1 in $f12 (for printing), and clear all used registers
	mov.s $f12 , $f1
	lwc1 $f1 , ZERO
	lwc1 $f2 , ZERO
	lwc1 $f3 , ZERO
	lwc1 $f4 , ZERO
	lwc1 $f5 , ZERO
	lwc1 $f6 , ZERO
	lwc1 $f7 , ZERO
	
	jr $ra
	
squareRootWhile:
	#{ X = 0.5 * (X + (N / X));
	div.s $f3 , $f0 , $f1
	add.s $f3 , $f3 , $f1
	mul.s $f1 , $f5 , $f3
	
	j squareRootLoop

exit: #label to exit the running program
	#print the exit message
	li $v0, 4
	la $a0, ExitMessage
	syscall

	li $v0, 10
	syscall

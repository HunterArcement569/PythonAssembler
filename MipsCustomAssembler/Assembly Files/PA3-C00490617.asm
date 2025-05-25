#Hunter Arcement
#C00490617
#CMPS 351
#PA3

.data #the data section contains mostly the string messages for the two prompts, result, and error
	firstPrompt: .asciiz "Enter a positive array length: " #this is the prompt the user will see first
	secondPrompt: .asciiz "\nEnter integer " #this is the prompt in the "for" loop the user will see several times to input their array numbers
	Error: .asciiz "\nError -- Number was not positive, ending program!"
	ResultMessage: .asciiz "\nThe maximum value in the array is: "
	Array: .space 200  #store a number of bytes for the integers, this number must be a multiple of 4 since each int is 32 bites
	#the number 200 means that Array can store 50 integers, statically reserved
	
.text #the text section that contains all the program including the void-parameterized function
.globl main
main:          #main label
    #first thing is to get the user input that determines the array size or end of the running program
	#print the prompt
	li $v0, 4
	la $a0, firstPrompt
	syscall

	#get the input
	li $v0, 5
	syscall
	move  $t1, $v0 #set the t1 register to the input, *** $t1 will be the counter for the main "for" loop ***
	add $t2 , $zero , $t1 #copy the user input into another register so it can be used later as an actual parameter
	li $t3 , 1 #load 1 into the register for decrement of variables in both of the "for" loops

    #check if that number is < 0, if it is then the loop is unnecessary
	blt $t1 , $zero , finalPrint
    #check if that number is = 0, if it is then the loop is unnecessary
	beqz $t1 , finalPrint
	
     #if we didn't go into the Error and Exit, then first set up the array's length and begin getting the values that will populate it
     la $s0 , Array
	
FirstFor: #the "for" loop in main used for getting all the numbers that are being placed in the array
    #get the user input for what number comes next
	#print the prompt
	li $v0, 4
	la $a0, secondPrompt
	syscall

	#get the input
	li $v0, 5
	syscall
	
	#put it into the array
	add  $t4 , $zero , $v0 
	sw $t4 , Array($t0)
	#increment the $t0 by 4 to index all of the needed integers
	add $t0 , $t0 , 4
	
    #decrement the counter and continue the loop based on if we are still greater than zero
	sub $t2 , $t2 , $t3
	bgt $t2 , $zero , FirstFor
	
	#make the call to the function
	la $a1 , Array #this is the first parameter, the starting address of the array
	add $a2 , $t1 , $zero #this is the second parameter, the array length
	jal PrintArrayMax #link this address to the $ra so we can come back here after the function ends
	
	#when program returns jump to the exit
	j Exit

finalPrint: #finalPrint label if the user entered a number that was 0 or not positive for the first input
	#print the error message
	li $v0, 4
	la $a0, Error
	syscall
	
	#jump to the exit section
	j Exit

PrintArrayMax: #function label
	lw $t5 , ($a1) #using the $t5 register as my current max, set it to max
	add $t4 , $a1 , $zero  #set $t4 to act as my indexer
	#using $t6 to store the data of the not confirmed data
	
secondFor:  #second "for" loop label, this is in the function
	#get the information from the array address + index offset * 4, store in t6 , array start is a1 , offset in t4
	lw $t6, ($t4)
	
	#check the information and set the register at $t5 based on the results
	bgt $t6 , $t5 , changeMax #if greater than go to the swap
	ble $t6 , $t5 , afterCheck #if not then skip that and go straight to the increment/decrement
	
changeMax: #label to change the max value
	add $t5 , $t6 , $zero
	
afterCheck: #label to be used to skip the changeMax section
	#increment/decrement appropriate counters
	add $t4 , $t4 , 4 #increment offset
	sub $a2 , $a2 , $t3 #decrement loop counter
	sub $t6, $t6 , $t6 #set the $t6 to zero for the next potential iteration
	
	#check if we are still 
	bgtz $a2 , secondFor 
	
	#print the output after the loop terminates
	#print the message
	li $v0, 4
	la $a0, ResultMessage
	syscall
	#print the integer --> should be the max value in that array of integers
	li $v0, 1
    move $a0, $t5 #put t5 into the parameter of the integer print
    syscall
	
	jr $ra #return to the main function

Exit:         #exit label
li $v0, 10
syscall

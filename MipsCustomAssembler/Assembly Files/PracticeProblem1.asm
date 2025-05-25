#Hunter Arcement --> C00490617 --> 3/14/2024

.data
    exitMessage: .asciiz "\n\nExitting the program!\n"
	firstPrompt: .asciiz "How many numbers: "
	secondPrompt: .asciiz "Enter a num: "
	firstMessage: .asciiz "\nSum of nums: "

.text 
#before the program starts the loop section sequentially, get the number of numbers and save it 

#print the prompt
li $v0, 4
la $a0, firstPrompt
syscall

#get the input
li $v0, 5
syscall
move  $t1, $v0 #set the t1 register to the input 

#check if that number is < 0, if it is then the loop is unnecessary
blt $t1 , $zero , POSTLOOP
#check if that number is = 0, if it is then the loop is unnecessary
beqz $t1 , POSTLOOP

#if we did neither jump above, sequentially start the loop
li $t3 , 1
LOOP: #marker for the loop
	#first we need the user input for what number we are adding 
	
	#print the prompt
	li $v0, 4
	la $a0, secondPrompt
	syscall

	#get the input
	li $v0, 5
	syscall
	move $t2, $v0 #set the t2 register to the input, this is the temp
	
	#add the t2 to the register we are using to store the sum
	add $t0 , $t0 , $t2
	
	#decrement the counter
	sub  $t1 , $t1 , $t3
	
	#check if we are still running the loop, otherwise let the program sequentially go to the postloop instructions
	bge $t1 , $t3 , LOOP
	

POSTLOOP: #marker for the post-loop instructions
	#print the message
	li $v0, 4
	la $a0, firstMessage
	syscall
	
	#print the number
	li $v0, 1
    move $a0, $t0
    syscall
        
    #allow the program to exit sequentially

EXIT: #marker for the exit section
	li $v0, 4
	la $a0, exitMessage
	syscall
	li $v0, 10
	syscall
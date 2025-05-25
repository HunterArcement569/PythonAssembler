#declare the data section
.data
	#create the prompt message string to get an integer from the user
	messagePrompt: .asciiz "Enter an integer value: "
	#create the message strings for output relative to the input
	messageLessThan: .asciiz "\nThe number input was less than 100!"
	messageEqualTo: .asciiz "\nThe number input was equal to 100!"
	messageGreaterThan: .asciiz "\nThe number input was greater than 100!"

#declare the text section
.text
main:
    #put the number we are comparing to into the register
	li  $s0 , 100
	
    #get the user input
	#prompt the user
	li $v0, 4
	la $a0, messagePrompt
	syscall
	
	#get the actual number
	li $v0, 5
	syscall
	move $t0, $v0
	
    #run the comparison
    #if the input is greater than 100
    sgt $t1, $t0, $s0 #if t0 (input) is greater than s0 (100) set t1 to true, otherwise false and the next segment is skipped
    beqz $t1, _greaterThan
    #{
    #print the output
    li $v0, 4
    la $a0, messageGreaterThan
    syscall
    #}
_greaterThan: #mark the end of the code block
    	
    #if the input is less than 100
    sgt $t1, $s0, $t0 #if $s0 (100) is greater than $t0 (input), reverse of last condition
    beqz $t1, _lessThan
    #{
    #print the output
    li $v0, 4
    la $a0, messageLessThan
    syscall
    #}
_lessThan: #mark the end of the code block
    #if the input is 100
    seq $t1, $s0, $t0 #if $s0 (100) is equal to $t0 (input)
    beqz $t1, _equalTo
    #{
    #print the output
    li $v0, 4
    la $a0, messageEqualTo
    syscall
    #}
_equalTo: #mark the end of the code block
    	
#exit the program
li $v0, 10
syscall

.data 
	messageFirstProcedure: .asciiz "This is the first procedure"
	messageSecondProcedure: .asciiz "\nThis is the second and last procedure"
	messageMiddle: .asciiz "\nThis is between the procedure calls"
	messageEnd: .asciiz "\nThis is after both procedures"
.text 
	MAIN: #main function
		jal FIRST #call the first procedure
		
		#print a message to confirm we returned to main properly
		li $v0, 4
		la $a0, messageMiddle
		syscall
		
		jal SECOND #call the second procedure
		
		#print a message to confirm we returned to main properly
		li $v0, 4
		la $a0, messageEnd
		syscall
	
		j EXIT #go to the exit
		
	EXIT: #exit section
		li $v0, 10
		syscall
	
	FIRST: #the first procedure (function)
		li $v0, 4
		la $a0, messageFirstProcedure 
		syscall
		
		jr $ra
	
	SECOND: #the second procedure (function)
		li $v0, 4
		la $a0, messageSecondProcedure  
		syscall
		
		jr $ra

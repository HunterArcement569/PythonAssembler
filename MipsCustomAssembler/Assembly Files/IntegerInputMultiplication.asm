.text
main:
    # Prompt for the first integer to enter
    li $v0, 4
    la $a0, prompt
    syscall
    
    # Read the first integer and save it in $s0
    li $v0, 5
    syscall
    move $s0, $v0
    
    # Output the text
    li $v0, 4
    la $a0, output
    syscall

    # Output the first number
    li $v0, 1
    move $a0, $s0
    syscall
    
    # Prompt for the second integer to enter
    li $v0, 4
    la $a0, secondPrompt
    syscall
    
    # Read the second integer and save it in $s1
    li $v0, 5
    syscall
    move $s1, $v0
    
    # Output the text
    li $v0, 4
    la $a0, output
    syscall

    # Output the second number
    li $v0, 1
    move $a0, $s0
    syscall
    
    #multiply the numbers into the registers
    mul $s1, $s0, $s1
    
    #output the product of both numbers
    li $v0, 4
    la $a0, productMessage
    syscall
    li $v0, 1
    move $a0, $s1
    syscall

    # Exit the program
    li $v0, 10
    syscall
    
.data
prompt: .asciiz "Please enter an integer: " 
secondPrompt: .asciiz "\nPlease enter another integer: "
output: .asciiz "\nYou typed the number: "
productMessage: .asciiz "\nProduct of your two numbers is: "

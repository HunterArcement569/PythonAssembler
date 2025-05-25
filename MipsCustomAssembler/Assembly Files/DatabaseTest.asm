.data
	#message addresses
	exitMessage: .asciiz "\nExiting the program!"
	invalidInputMessage: .asciiz "\nInvalid Input\n"
	space: .asciiz " "
	period: .asciiz "."
	newline: .asciiz "\n"

	classIdPrompt: .asciiz "\nEnter class ID: "
	studentIdPrompt: .asciiz "\nEnter student ID: "
	scorePrompt: .asciiz "\nEnter score: "
	studentPrompt: .asciiz "\nEnter student name: "
	classPrompt: .asciiz "\nEnter class name: "

	outerPrompt: .asciiz "\nEnter the number of your choice: "

	insertOuterPrompt: .asciiz "\nEnter 0 to exit Insert\nEnter 1 to Insert Student\nEnter 2 to Insert Class\nEnter 3 to Insert Grade"
	selectOuterPrompt: .asciiz "\nEnter 0 to exit Select\nEnter 1 to Select Student by Name\nEnter 2 to Select Class by Name\nEnter 3 to Select Student by Average Grade\nEnter 4 to Select Class by Average Grade\nEnter 5 to Select Grades in a Class"
    updateOuterPrompt: .asciiz "\nEnter 0 to exit Update\nEnter 1 to Update Grade"
    deleteOuterPrompt: .asciiz "\nEnter 0 to exit Delete\nEnter 1 to Delete Student\nEnter 2 to Delete Class"\nEnter 3 to Delete Grade"

	#file location of the database
	databaseLocation: .asciiz "DatabaseTest.db"

	#table creates
	tableCreate_1: .asciiz "CREATE TABLE IF NOT EXISTS Student(ID INTEGER PRIMARY KEY AUTOINCREMENT, Name TEXT NOT NULL)"
	tableCreate_2: .asciiz "CREATE TABLE IF NOT EXISTS Class(ID INTEGER PRIMARY KEY AUTOINCREMENT, Name TEXT NOT NULL UNIQUE)"
	tableCreate_3: .asciiz "CREATE TABLE IF NOT EXISTS Grade(S_ID INTEGER NOT NULL, C_ID INTEGER NOT NULL, Value FLOAT NOT NULL, FOREIGN KEY (S_ID) REFERENCES Student(ID) ON DELETE CASCADE, FOREIGN KEY (C_ID) REFERENCES Class(ID) ON DELETE CASCADE)"

    #view creates
    viewCreate_1: .asciiz "CREATE VIEW IF NOT EXISTS SingleAverages AS SELECT Student.Name, AVG(Grade.Value) AS Average FROM Student, Grade WHERE Student.ID = Grade.S_ID GROUP BY Student.ID"
    viewCreate_2: .asciiz "CREATE VIEW IF NOT EXISTS ClassAverages AS SELECT Class.Name, AVG(Grade.VALUE) AS Average FROM Class, Grade WHERE Class.ID = Grade.C_ID GROUP BY Class.ID"

    #inserts
    insertStudent: .asciiz "INSERT INTO Student(Name) VALUES(?)"
    insertClass: .asciiz "INSERT INTO Class(Name) VALUES(?)"
    insertGrade: .asciiz "INSERT INTO Grade(S_ID, C_ID, Value) VALUES(?,?,?)"

    #update
    updateGrade: .asciiz "UPDATE Grade SET Value = ? WHERE S_ID = ? AND C_ID = ?"

    #deletes
    deleteStudent: .asciiz "DELETE FROM Student WHERE ID = ?"
    deleteClass: .asciiz "DELETE FROM Class WHERE ID = ?"
    deleteGrade: .asciiz "DELETE FROM Grade WHERE S_ID = ? AND C_ID = ?"

    #utility selects
    selectStudent: .asciiz "SELECT * FROM Student"
    selectClass: .asciiz "SELECT * FROM Class"

    #selects
    selectStudentName: .asciiz "SELECT * FROM Student ORDER BY Name"
    selectClassName: .asciiz "SELECT * FROM Class ORDER BY Name"
    selectStudentAverages: .asciiz "SELECT * FROM SingleAverages ORDER BY Average DESC"
    selectClassAverages: .asciiz "SELECT * FROM ClassAverages ORDER BY Average DESC"
    selectClassGrades: .asciiz "SELECT Student.Name, Grade.Value FROM Grade, Student, Class WHERE Grade.C_ID = ? AND Student.ID = Grade.S_ID AND Grade.C_ID = Class.ID ORDER BY Grade.Value DESC"

    #storage for the scores when they're inputted by the user
    gradeValue: .float 0.0

    #storage for id's when they're inputted by the user
    studentIdValue: .word -1
    classIdValue: .word -1

    #storage for important float value(s)
    ZERO: .float 0.0

    #array storage for the id's of classes and names used for many operations
    ids: .space 200 #stores up to 50 id's

    #storage for the name of the student(s) and class(es), to be given by the user
    input: .space 81
    inputSize: .word 80
.text
MAIN:
    jal CONNECT #Connect is a void function that just connects to the database
    jal TABLES #Tables is a void function that just create database tables and views (if they aren't there already)

    j INSERT_OUTER #Insert_Outer is a void function that acts as the first layer of user input for inserts
    #CLOSE and EXIT are called after the chain execution of insert, update, delete, select


CONNECT:
    la $t0, databaseLocation
    dbct $s0, $s1, $t0 #call database connect to store the connection in $so, cursor in $s1 with the file location of $t0
    jr $ra


TABLES:
    la $t0, tableCreate_1
    dbt $s0, $s1, $t0 #create the Student table

    la $t0, tableCreate_2
    dbt $s0, $s1, $t0 #create the Class table

    la $t0, tableCreate_3
    dbt $s0, $s1, $t0 #create the Grade table

    la $t0, viewCreate_1
    dbt $s0, $s1, $t0 #create the SingleAverages view (virtual table to contain each student's name and average of just their class grades)

    la $t0, viewCreate_2
    dbt $s0, $s1, $t0 #create the ClassAverages view (virtual table to contain the class average (for each class))
    jr $ra


INSERT_OUTER:
    #prompt the user for an integer input
    la $a0, insertOuterPrompt #print options
    li $v0, 4
    syscall
    la $a0, outerPrompt #prompt for option number
    syscall
    li $v0, 5
    syscall
    move $t1, $v0 #store the user input into $t1

    #if the input was not 0, 1, 2, or 3 then repeat the loop, otherwise go to the needed function
    beq $t1, 0, UPDATE_OUTER #branch to the next segment of the main code
    beq $t1, 1, INSERT_STUDENT
    beq $t1, 2, INSERT_CLASS
    beq $t1, 3, INSERT_GRADE

    #print an error message
    li $v0, 4
    la $a0, invalidInputMessage
    syscall

    j INSERT_OUTER

INSERT_STUDENT:
    #prompt the user for a name
    li $v0, 4
    la $a0, studentPrompt
    syscall
    li $v0, 8
    la $a0, input
    lw $a1, inputSize
    syscall
    la $t1, input #name is now in $t1

    #perform the input
    la $t0, insertStudent
    dbi $s0, $s1, $t0, $t1

    #jump back to the insert outer loop
    j INSERT_OUTER

INSERT_CLASS:
    #prompt the user for a name
    li $v0, 4
    la $a0, classPrompt
    syscall
    li $v0, 8
    la $a0, input
    lw $a1, inputSize
    syscall
    la $t1, input #name is now in $t1

    #perform the input
    la $t0, insertClass
    dbi $s0, $s1, $t0, $t1

    #jump back to the insert outer loop
    j INSERT_OUTER

INSERT_GRADE:
    #get the student id from the user
    jal STUDENT_ID
    sw $t1, studentIdValue
    la $t1, studentIdValue

    #get the class id from the user
    jal CLASS_ID
    sw $t2, classIdValue
    la $t2, classIdValue

    #get the score from the user
    jal SCORE
    s.s $f0, gradeValue
    la $t3, gradeValue

    #perform the insertion
    la $t0, insertGrade
    dbi $s0, $s1, $t0, $t1, $t2, $t3 #input returns from the two functions and the score

    j INSERT_OUTER


UPDATE_OUTER:
    #prompt the user for an integer input
    la $a0, updateOuterPrompt #print options
    li $v0, 4
    syscall
    la $a0, outerPrompt #prompt for option number
    syscall
    li $v0, 5
    syscall
    move $t1, $v0 #store the user input into $t1

    #if the input was not 0 or 1 then repeat the loop, otherwise go to the needed function
    beq $t1, 0, DELETE_OUTER #branch to the next segment of the main code
    beq $t1, 1, UPDATE_GRADE

    #print an error message
    li $v0, 4
    la $a0, invalidInputMessage
    syscall

    j DELETE_OUTER

UPDATE_GRADE:
    #get the student id from the user
    jal STUDENT_ID
    sw $t1, studentIdValue
    la $t1, studentIdValue

    #get the class id from the user
    jal CLASS_ID
    sw $t2, classIdValue
    la $t2, classIdValue

    #get the score from the user
    jal SCORE
    s.s $f0, gradeValue
    la $t3, gradeValue

    #perform the update
    la $t0, updateGrade
    dbu $s0, $s1, $t0, $t3, $t1, $t2 #input returns from the two functions and the score, order is score then name id then class id

    j UPDATE_OUTER


DELETE_OUTER:
    #prompt the user for an integer input
    la $a0, deleteOuterPrompt #print options
    li $v0, 4
    syscall
    la $a0, outerPrompt #prompt for option number
    syscall
    li $v0, 5
    syscall
    move $t1, $v0 #store the user input into $t1

    #if the input was not 0, 1, 2, or 3 then repeat the loop, otherwise go to the needed function
    beq $t1, 0, SELECT_OUTER #branch to the next segment of the main code
    beq $t1, 1, DELETE_STUDENT
    beq $t1, 2, DELETE_CLASS
    beq $t1, 3, DELETE_GRADE

    #print an error message
    li $v0, 4
    la $a0, invalidInputMessage
    syscall

    j DELETE_OUTER

DELETE_STUDENT:
    #get the student id from the user
    jal STUDENT_ID
    sw $t1, studentIdValue
    la $t1, studentIdValue

    #perform the delete
    la $t0, deleteStudent
    dbd $s0, $s1, $t0, $t1 #input returns from the one function

    j DELETE_OUTER

DELETE_CLASS:
    #get the class id from the user
    jal CLASS_ID
    sw $t2, classIdValue
    la $t2, classIdValue

    #perform the delete
    la $t0, deleteClass
    dbd $s0, $s1, $t0, $t2 #input returns from the one function

    j DELETE_OUTER

DELETE_GRADE:
    #get the student id from the user
    jal STUDENT_ID
    sw $t1, studentIdValue
    la $t1, studentIdValue

    #get the class id from the user
    jal CLASS_ID
    sw $t2, classIdValue
    la $t2, classIdValue

    #perform the delete
    la $t0, deleteGrade
    dbd $s0, $s1, $t0, $t1, $t2 #input returns from the two functions and the score

    j DELETE_OUTER


SELECT_OUTER:
    #prompt the user for an integer input
    la $a0, selectOuterPrompt #print options
    li $v0, 4
    syscall
    la $a0, outerPrompt #prompt for option number
    syscall
    li $v0, 5
    syscall
    move $t1, $v0 #store the user input into $t1

    #if the input was not 0, 1, 2, 3, 4, or 5 then repeat the loop, otherwise go to the needed function
    beq $t1, 0, CLOSE #branch to the next segment of the main code
    beq $t1, 1, SELECT_STUDENT_NAME
    beq $t1, 2, SELECT_CLASS_NAME
    beq $t1, 3, SELECT_STUDENT_AVG_GRADE
    beq $t1, 4, SELECT_CLASS_AVG_GRADE
    beq $t1, 5, SELECT_CLASS_GRADES

    #print an error message
    li $v0, 4
    la $a0, invalidInputMessage
    syscall

    j INSERT_OUTER

SELECT_STUDENT_NAME:
    #perform the select
    la $t5, selectStudentName
    dbs $t6, $s1, $t5 #row count goes into $t6
    move $t4, $zero #$t4 is the counter for the next function (ensure it is zero to start)

SELECT_STUDENT_NAME_ITER:
    #perform the iteration
    dbit $t4, $s1, $t7, $t8 #id address into #t7, name address into $t8

    #load the id into its register
    lw $t7, ($t7)

    #print the student id
    li $v0, 1
    move $a0, $t7
    syscall

    #print a period
    li $v0, 4
    la $a0, period
    syscall

    #print a space
    la $a0, space
    syscall

    #print the student name
    move $a0, $t8
    syscall

    #print a newline
    la $a0, newline
    syscall

    #increment the counter and test if the loop continues
    add $t4, $t4, 1
    blt $t4, $t6, SELECT_STUDENT_NAME_ITER

    #now that the loop has concluded, return to the header function
    j SELECT_OUTER

SELECT_CLASS_NAME:
    #perform the select
    la $t5, selectClassName
    dbs $t6, $s1, $t5 #row count goes into $t6
    move $t4, $zero #$t4 is the counter for the next function (ensure it is zero to start)

SELECT_CLASS_NAME_ITER:
    #perform the iteration
    dbit $t4, $s1, $t7, $t8 #id address into #t7, name address into $t8

    #load the id into its register
    lw $t7, ($t7)

    #print the class id
    li $v0, 1
    move $a0, $t7
    syscall

    #print a period
    li $v0, 4
    la $a0, period
    syscall

    #print a space
    la $a0, space
    syscall

    #print the class name
    move $a0, $t8
    syscall

    #print a newline
    la $a0, newline
    syscall

    #increment the counter and test if the loop continues
    add $t4, $t4, 1
    blt $t4, $t6, SELECT_CLASS_NAME_ITER

    #now that the loop has concluded, return to the header function
    j SELECT_OUTER

SELECT_STUDENT_AVG_GRADE:
    #perform the select
    la $t5, selectStudentAverages
    dbs $t6, $s1, $t5 #row count goes into $t6
    move $t4, $zero #$t4 is the counter for the next function (ensure it is zero to start)

SELECT_STUDENT_AVG_ITER:
    #perform the iteration
    dbit $t4, $s1, $t7, $f12 #name address into #t7, score value into $f12

    #print the student name
    li $v0, 4
    move $a0, $t7
    syscall

    #print a period
    la $a0, period
    syscall

    #print a space
    la $a0, space
    syscall

    #print the student avg grade
    li $v0, 2
    syscall

    #print a newline
    li $v0, 4
    la $a0, newline
    syscall

    #increment the counter and test if the loop continues
    add $t4, $t4, 1
    blt $t4, $t6, SELECT_STUDENT_AVG_ITER

    #now that the loop has concluded, return to the header function
    j SELECT_OUTER

SELECT_CLASS_AVG_GRADE:
    #perform the select
    la $t5, selectClassAverages
    dbs $t6, $s1, $t5 #row count goes into $t6
    move $t4, $zero #$t4 is the counter for the next function (ensure it is zero to start)

SELECT_CLASS_AVG_ITER:
    #perform the iteration
    dbit $t4, $s1, $t7, $f12 #name address into #t7, score value into $f12

    #print the class name
    li $v0, 4
    move $a0, $t7
    syscall

    #print a period
    la $a0, period
    syscall

    #print a space
    la $a0, space
    syscall

    #print the class avg grade
    li $v0, 2
    syscall

    #print a newline
    li $v0, 4
    la $a0, newline
    syscall

    #increment the counter and test if the loop continues
    add $t4, $t4, 1
    blt $t4, $t6, SELECT_CLASS_AVG_ITER

    #now that the loop has concluded, return to the header function
    j SELECT_OUTER

SELECT_CLASS_GRADES:
    #get the class id from the user
    jal CLASS_ID
    sw $t2, classIdValue
    la $t2, classIdValue

    #perform the select
    la $t5, selectClassGrades
    dbs $t6, $s1, $t5, $t2 #row count goes into $t6, $t2 is the parameter address (of the class id)
    move $t4, $zero #$t4 is the counter for the next function (ensure it is zero to start)

SELECT_CLASS_GRADE_ITER:
    #perform the iteration
    dbit $t4, $s1, $t7, $f12 #name address into #t7, score value into $f12

    #print the student's name
    li $v0, 4
    move $a0, $t7
    syscall

    #print a period
    la $a0, period
    syscall

    #print a space
    la $a0, space
    syscall

    #print the student's class grade
    li $v0, 2
    syscall

    #print a newline
    li $v0, 4
    la $a0, newline
    syscall

    #increment the counter and test if the loop continues
    add $t4, $t4, 1
    blt $t4, $t6, SELECT_CLASS_GRADE_ITER

    #now that the loop has concluded, return to the header function
    j SELECT_OUTER


STUDENT_ID: #function to get user input on the student id (select, output, and validate input)
    #perform the select query
    la $t5, selectStudent
    dbs $t6, $s1, $t5 #row count goes into $t6
    move $t4, $zero #$t4 is the counter for the next function (ensure it is zero to start)

    #enter the iteration sequentially

STUDENT_ID_ITERATE: #function to loop through the iterations
    #perform the iteration
    dbit $t4, $s1, $t7, $t8 #id address into #t7, name address into $t8

    #load the id into its register
    lw $t7, ($t7)

    #save the id into the index of the ids array
    mul $t3, $t4, 4
    sw $t7, ids($t3)

    #print the student id
    li $v0, 1
    move $a0, $t7
    syscall

    #print a period
    li $v0, 4
    la $a0, period
    syscall

    #print a space
    la $a0, space
    syscall

    #print the student name
    move $a0, $t8
    syscall

    #print a newline
    la $a0, newline
    syscall

    #increment the counter and test if the loop continues
    add $t4, $t4, 1
    blt $t4, $t6, STUDENT_ID_ITERATE

    #if loop doesn't continue, prompt the user and get the integer input
    li $v0, 4
    la $a0, studentIdPrompt
    syscall
    li $v0, 5
    syscall
    move $t1, $v0

    #determine if that integer was in the ids array (enter the function sequentially)
    move $t4 , $zero #$t4 is the counter

IN_IDS:
    #load the word from the ids at the offset
    mul $t0, $t4, 4
    lw $t5, ids($t0)

    #if the loaded number is the same as the input, return, otherwise reset the loop if possible)
    beq $t5, $t1, RETURN_SC_ID
    add $t4, $t4, 1 #increment
    blt $t4, $t6, IN_IDS

    #print an error and branch back to the start of the function
    li $v0, 4
    la $a0, invalidInputMessage
    syscall
    j STUDENT_ID


CLASS_ID: #function to get user input on the class id (select, output, and validate input)
    #perform the select query
    la $t5, selectClass
    dbs $t6, $s1, $t5 #row count goes into $t6
    move $t4, $zero #$t4 is the counter for the next function (ensure it is zero to start)

    #enter the iteration sequentially

CLASS_ID_ITERATE: #function to loop through the iterations
    #perform the iteration
    dbit $t4, $s1, $t7, $t8 #id address into #t7, name address into $t8

    #print the id number
    lw $t9, ($t7)
    move $a0, $t9
    li $v0, 1
    syscall

    #save the id into the index of the ids array
    mul $t3, $t4, 4
    sw  $t9, ids($t3)

    #print a period
    li $v0, 4
    la $a0, period
    syscall

    #print a space
    la $a0, space
    syscall

    #print the class name
    move $a0, $t8
    syscall

    #print a newline
    la $a0, newline
    syscall

    #increment the counter and test if the loop continues
    add $t4, $t4, 1
    blt $t4, $t6, CLASS_ID_ITERATE

    #if loop doesn't continue, prompt the user and get the integer input
    li $v0, 4
    la $a0, classIdPrompt
    syscall
    li $v0, 5
    syscall
    move $t2, $v0

    #determine if that integer was in the ids array (enter the function sequentially)
    move $t4 , $zero #$t4 is the counter

IN_IDS_CLASS:
    #load the word from the ids at the offset
    mul $t0, $t4, 4
    lw $t5, ids($t0)

    #if the loaded number is the same as the input, return, otherwise reset the loop if possible)
    beq $t5, $t2, RETURN_SC_ID
    add $t4, $t4, 1 #increment
    blt $t4, $t6, IN_IDS_CLASS

    #print an error and branch back to the start of the function
    li $v0, 4
    la $a0, invalidInputMessage
    syscall
    j CLASS_ID


RETURN_SC_ID: #used to return for the Student and Class ID functions
    jr $ra


SCORE: #function to get user input on the score (used for update and insert)
    #print the prompt
    li $v0, 4
    la $a0, scorePrompt
    syscall

    #get the input (float)
    li $v0, 6
	syscall

    #validate the input
    lwc1 $f1, ZERO #ensure it is not negative (< 0.0)
    c.lt.s $f0, $f1
    bc1t SCORE_INVALID_INPUT
    jr $ra #return value (the score) is in $f1

SCORE_INVALID_INPUT: #function to print the invalid input and jump back to the score function
    li $v0, 4
    la $a0, invalidInputMessage
    syscall
    j SCORE


CLOSE:
    dbcl $s0, $s1 #call database close end the connection and cursor to the database

    #exit the program sequentially after closing the database connection

EXIT: #exit section
	li $v0, 4
	la $a0, exitMessage
	syscall
	li $v0, 10
	syscall

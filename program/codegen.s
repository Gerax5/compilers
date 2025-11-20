.data
var_L9_else: .word 0
var_L9_end: .word 0
var_Lwhile_body_2: .word 0
var_Lwhile_end_3: .word 0
var_Lwhile_test_1: .word 0
var_addFive: .word 0
var_func_makeAdder_t1: .word 0
var_func_makeAdder_x: .word 0
tmp_t1: .word 0
tmp_t2: .word 0
str0: .asciiz "Greater than 5"
str1: .asciiz "5 or less"
str2: .asciiz "\n"

.text
main:
	li $a0, 1
	jal func_makeAdder
	sw $v0, tmp_t1
	lw $t0, tmp_t1
	sw $t0, var_addFive
	lw $t0, var_addFive
	li $t1, 5
	slt $t2, $t1, $t0
	sw $t2, tmp_t1
	lw $t0, tmp_t1
	beq $t0, $zero, L9_else
	la $a0, str0
	li $v0, 4
	syscall
	j L9_end
L9_else:
	la $a0, str1
	li $v0, 4
	syscall
L9_end:
Lwhile_test_1:
	lw $t0, var_addFive
	li $t1, 10
	slt $t2, $t0, $t1
	sw $t2, tmp_t2
	lw $t0, tmp_t2
	beq $t0, $zero, Lwhile_end_3
Lwhile_body_2:
	lw $t0, var_addFive
	li $t1, 1
	add $t2, $t0, $t1
	sw $t2, tmp_t2
	lw $t0, tmp_t2
	sw $t0, var_addFive
	j Lwhile_test_1
Lwhile_end_3:
	la $a0, str2
	li $v0, 4
	syscall
	lw $a0, var_addFive
	li $v0, 1
	syscall

	li $v0, 10
	syscall
func_makeAdder:
	addiu $sp, $sp, -8
	sw $ra, 4($sp)
	sw $fp, 0($sp)
	move $fp, $sp
	sw $a0, var_func_makeAdder_x
	lw $t0, var_func_makeAdder_x
	li $t1, 1
	add $t2, $t0, $t1
	sw $t2, tmp_t1
	lw $v0, tmp_t1
	lw $ra, 4($sp)
	lw $fp, 0($sp)
	addiu $sp, $sp, 8
	jr $ra
.data
var_addFive: .word 0
var_func_makeAdder_t1: .word 0
var_func_makeAdder_x: .word 0
tmp_t1: .word 0
tmp_t2: .word 0
str0: .asciiz "\n"

.text
main:
	li $a0, 1
	jal func_makeAdder
	sw $v0, tmp_t1
	lw $t0, tmp_t1
	sw $t0, var_addFive
	lw $t0, var_addFive
	li $t1, 1
	sub $t2, $t0, $t1
	sw $t2, tmp_t1
	lw $t0, tmp_t1
	sw $t0, var_addFive
	lw $t0, var_addFive
	li $t1, 7
	slt $t2, $t1, $t0
	sw $t2, tmp_t1
	la $a0, str0
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
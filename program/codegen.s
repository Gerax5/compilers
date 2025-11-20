.data
var_L0for_body_2: .word 0
var_L0for_end_4: .word 0
var_L0for_incr_3: .word 0
var_L0for_test_1: .word 0
var_i: .word 0
tmp_t1: .word 0
str0: .asciiz "Loop index: "

.text
main:
	li $t0, 0
	sw $t0, var_i
L0for_test_1:
	lw $t0, var_i
	li $t1, 3
	slt $t2, $t0, $t1
	sw $t2, tmp_t1
	lw $t0, tmp_t1
	beq $t0, $zero, L0for_end_4
L0for_body_2:
	la $a0, str0
	li $v0, 4
	syscall
	lw $a0, var_i
	li $v0, 1
	syscall
L0for_incr_3:
	lw $t0, var_i
	li $t1, 1
	add $t2, $t0, $t1
	sw $t2, tmp_t1
	lw $t0, tmp_t1
	sw $t0, var_i
	j L0for_test_1
L0for_end_4:

	li $v0, 10
	syscall
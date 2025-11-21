.data
var_L1while_body_2: .word 0
var_L1while_end_3: .word 0
var_L1while_test_1: .word 0
var_i: .word 0
tmp_t1: .word 0

.text
main:
	li $t0, 0
	sw $t0, var_i
L1while_test_1:
	lw $t0, var_i
	li $t1, 3
	slt $t2, $t0, $t1
	sw $t2, tmp_t1
	lw $t0, tmp_t1
	beq $t0, $zero, L1while_end_3
L1while_body_2:
	lw $a0, var_i
	li $v0, 1
	syscall
	lw $t0, var_i
	li $t1, 1
	add $t2, $t0, $t1
	sw $t2, tmp_t1
	lw $t0, tmp_t1
	sw $t0, var_i
	j L1while_test_1
L1while_end_3:

	li $v0, 10
	syscall
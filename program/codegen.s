.data
var_L17_else: .word 0
var_L8foreach_body_2: .word 0
var_L8foreach_end_4: .word 0
var_L8foreach_incr_3: .word 0
var_L8foreach_test_1: .word 0
var_arr_0: .word 0
var_n: .word 0
var_numbers: .word 0
tmp_t1: .word 0
tmp_t2: .word 0
tmp_t3: .word 0
tmp_t4: .word 0
tmp_t5: .word 0
arr_arr_0: .space 20
arr_arr_0_len: .word 5
str0: .asciiz "HOLA"

.text
main:
	la $t0, arr_arr_0
	sw $t0, var_arr_0
	la $t0, arr_arr_0
	li $t1, 0
	li $t2, 1
	sll $t1, $t1, 2
	add $t0, $t0, $t1
	sw $t2, 0($t0)
	la $t0, arr_arr_0
	li $t1, 1
	li $t2, 2
	sll $t1, $t1, 2
	add $t0, $t0, $t1
	sw $t2, 0($t0)
	la $t0, arr_arr_0
	li $t1, 2
	li $t2, 3
	sll $t1, $t1, 2
	add $t0, $t0, $t1
	sw $t2, 0($t0)
	la $t0, arr_arr_0
	li $t1, 3
	li $t2, 4
	sll $t1, $t1, 2
	add $t0, $t0, $t1
	sw $t2, 0($t0)
	la $t0, arr_arr_0
	li $t1, 4
	li $t2, 5
	sll $t1, $t1, 2
	add $t0, $t0, $t1
	sw $t2, 0($t0)
	lw $t0, var_arr_0
	sw $t0, var_numbers
	la $a0, str0
	li $v0, 4
	syscall
	li $t0, 0
	sw $t0, tmp_t1
L8foreach_test_1:
	lw $t0, arr_arr_0_len
	sw $t0, tmp_t2
	lw $t0, tmp_t1
	lw $t1, tmp_t2
	slt $t2, $t0, $t1
	sw $t2, tmp_t3
	lw $t0, tmp_t3
	beq $t0, $zero, L8foreach_end_4
L8foreach_body_2:
	lw $t3, var_numbers
	lw $t1, tmp_t1
	sll $t1, $t1, 2
	add $t3, $t3, $t1
	lw $t4, 0($t3)
	sw $t4, tmp_t4
	lw $t0, tmp_t4
	sw $t0, var_n
	lw $t0, var_n
	li $t1, 3
	sub $t3, $t0, $t1
	sltiu $t2, $t3, 1
	sw $t2, tmp_t4
	lw $t0, tmp_t4
	beq $t0, $zero, L17_else
	j L8foreach_incr_3
L17_else:
	lw $a0, var_n
	li $v0, 1
	syscall
L8foreach_incr_3:
	lw $t0, tmp_t1
	li $t1, 1
	add $t2, $t0, $t1
	sw $t2, tmp_t5
	lw $t0, tmp_t5
	sw $t0, tmp_t1
	j L8foreach_test_1
L8foreach_end_4:

	li $v0, 10
	syscall
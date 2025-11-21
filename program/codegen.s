.data
var_L19_else: .word 0
var_L19_end: .word 0
var_L25while_body_2: .word 0
var_L25while_end_3: .word 0
var_L25while_test_1: .word 0
var_L33dowhile_body_4: .word 0
var_L33dowhile_cond_5: .word 0
var_L33dowhile_end_6: .word 0
var_L42for_body_8: .word 0
var_L42for_end_10: .word 0
var_L42for_incr_9: .word 0
var_L42for_test_7: .word 0
var_L54foreach_body_12: .word 0
var_L54foreach_end_14: .word 0
var_L54foreach_incr_13: .word 0
var_L54foreach_test_11: .word 0
var_L63_else: .word 0
var_L69_else: .word 0
var_L77case_15: .word 0
var_L77case_16: .word 0
var_L77default_17: .word 0
var_L77switch_end_18: .word 0
var_L89catch_19: .word 0
var_L89try_end_20: .word 0
var_addFive: .word 0
var_arr_0: .word 0
var_err: .word 0
var_exception: .word 0
var_func_makeAdder_t1: .word 0
var_func_makeAdder_x: .word 0
var_i: .word 0
var_n: .word 0
var_numbers: .word 0
var_risky: .word 0
tmp_t1: .word 0
tmp_t2: .word 0
tmp_t3: .word 0
tmp_t4: .word 0
tmp_t5: .word 0
tmp_t6: .word 0
tmp_t7: .word 0
tmp_t8: .word 0
arr_arr_0: .space 24
arr_arr_0_len: .word 6
str0: .asciiz "\n5 + 1 = "
str1: .asciiz "\nGreater than 5"
str2: .asciiz "\n5 or less"
str3: .asciiz "\nResult is now "
str4: .asciiz "\nLoop index: "
str5: .asciiz "\nNumber: "
str6: .asciiz "\nIt's seven"
str7: .asciiz "\nIt's six"
str8: .asciiz "\nSomething else"
str9: .asciiz "\nRisky access: "
str10: .asciiz "\nCaught an error: "

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
	la $t0, arr_arr_0
	li $t1, 5
	li $t2, 6
	sll $t1, $t1, 2
	add $t0, $t0, $t1
	sw $t2, 0($t0)
	lw $t0, var_arr_0
	sw $t0, var_numbers
	li $a0, 5
	jal func_makeAdder
	sw $v0, tmp_t1
	lw $t0, tmp_t1
	sw $t0, var_addFive
	la $a0, str0
	li $v0, 4
	syscall
	lw $a0, var_addFive
	li $v0, 1
	syscall
	lw $t0, var_addFive
	li $t1, 5
	slt $t2, $t1, $t0
	sw $t2, tmp_t1
	lw $t0, tmp_t1
	beq $t0, $zero, L19_else
	la $a0, str1
	li $v0, 4
	syscall
	j L19_end
L19_else:
	la $a0, str2
	li $v0, 4
	syscall
L19_end:
L25while_test_1:
	lw $t0, var_addFive
	li $t1, 10
	slt $t2, $t0, $t1
	sw $t2, tmp_t2
	lw $t0, tmp_t2
	beq $t0, $zero, L25while_end_3
L25while_body_2:
	lw $t0, var_addFive
	li $t1, 1
	add $t2, $t0, $t1
	sw $t2, tmp_t2
	lw $t0, tmp_t2
	sw $t0, var_addFive
	j L25while_test_1
L25while_end_3:
L33dowhile_body_4:
	la $a0, str3
	li $v0, 4
	syscall
	lw $a0, var_addFive
	li $v0, 1
	syscall
	lw $t0, var_addFive
	li $t1, 1
	sub $t2, $t0, $t1
	sw $t2, tmp_t2
	lw $t0, tmp_t2
	sw $t0, var_addFive
L33dowhile_cond_5:
	lw $t0, var_addFive
	li $t1, 7
	slt $t2, $t1, $t0
	sw $t2, tmp_t2
	lw $t0, tmp_t2
	bne $t0, $zero, L33dowhile_body_4
L33dowhile_end_6:
	li $t0, 0
	sw $t0, var_i
L42for_test_7:
	lw $t0, var_i
	li $t1, 3
	slt $t2, $t0, $t1
	sw $t2, tmp_t2
	lw $t0, tmp_t2
	beq $t0, $zero, L42for_end_10
L42for_body_8:
	la $a0, str4
	li $v0, 4
	syscall
	lw $a0, var_i
	li $v0, 1
	syscall
L42for_incr_9:
	lw $t0, var_i
	li $t1, 1
	add $t2, $t0, $t1
	sw $t2, tmp_t2
	lw $t0, tmp_t2
	sw $t0, var_i
	j L42for_test_7
L42for_end_10:
	li $t0, 0
	sw $t0, tmp_t2
L54foreach_test_11:
	lw $t0, arr_arr_0_len
	sw $t0, tmp_t3
	lw $t0, tmp_t2
	lw $t1, tmp_t3
	slt $t2, $t0, $t1
	sw $t2, tmp_t4
	lw $t0, tmp_t4
	beq $t0, $zero, L54foreach_end_14
L54foreach_body_12:
	lw $t3, var_numbers
	lw $t1, tmp_t2
	sll $t1, $t1, 2
	add $t3, $t3, $t1
	lw $t4, 0($t3)
	sw $t4, tmp_t5
	lw $t0, tmp_t5
	sw $t0, var_n
	lw $t0, var_n
	li $t1, 3
	sub $t3, $t0, $t1
	sltiu $t2, $t3, 1
	sw $t2, tmp_t5
	lw $t0, tmp_t5
	beq $t0, $zero, L63_else
	j L54foreach_incr_13
L63_else:
	la $a0, str5
	li $v0, 4
	syscall
	lw $a0, var_n
	li $v0, 1
	syscall
	lw $t0, var_n
	li $t1, 4
	slt $t2, $t1, $t0
	sw $t2, tmp_t6
	lw $t0, tmp_t6
	beq $t0, $zero, L69_else
	j L54foreach_end_14
L69_else:
L54foreach_incr_13:
	lw $t0, tmp_t2
	li $t1, 1
	add $t2, $t0, $t1
	sw $t2, tmp_t7
	lw $t0, tmp_t7
	sw $t0, tmp_t2
	j L54foreach_test_11
L54foreach_end_14:
	lw $t0, var_addFive
	li $t1, 7
	sub $t3, $t0, $t1
	sltiu $t2, $t3, 1
	sw $t2, tmp_t8
	lw $t0, tmp_t8
	bne $t0, $zero, L77case_15
	lw $t0, var_addFive
	li $t1, 6
	sub $t3, $t0, $t1
	sltiu $t2, $t3, 1
	sw $t2, tmp_t8
	lw $t0, tmp_t8
	bne $t0, $zero, L77case_16
	j L77default_17
L77case_15:
	la $a0, str6
	li $v0, 4
	syscall
L77case_16:
	la $a0, str7
	li $v0, 4
	syscall
L77default_17:
	la $a0, str8
	li $v0, 4
	syscall
L77switch_end_18:
	lw $t3, var_numbers
	li $t1, 10
	lw $t0, arr_arr_0_len
	bltz $t1, L89catch_19
	bge $t1, $t0, L89catch_19
	sll $t1, $t1, 2
	add $t3, $t3, $t1
	lw $t4, 0($t3)
	sw $t4, tmp_t8
	lw $t0, tmp_t8
	sw $t0, var_risky
	la $a0, str9
	li $v0, 4
	syscall
	lw $a0, var_risky
	li $v0, 1
	syscall
	j L89try_end_20
L89catch_19:
	lw $t0, var_exception
	sw $t0, var_err
	la $a0, str10
	li $v0, 4
	syscall
	lw $a0, var_err
	li $v0, 1
	syscall
L89try_end_20:

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
	lw $ra, 4($sp)
	lw $fp, 0($sp)
	addiu $sp, $sp, 8
	jr $ra
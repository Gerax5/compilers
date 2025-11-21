.data
var_Animal: .word 0
var_dog: .word 0
var_func_Animal_constructor_name: .word 0
var_func_Animal_speak_name: .word 0
var_func_Animal_speak_t1: .word 0
var_func_Animal_speak_t2: .word 0
var_func_Animal_speak_this: .word 0
var_speak: .word 0
tmp_t1: .word 0
tmp_t2: .word 0
var_Animal_name: .word 0
var_Animal_this: .word 0
str0: .asciiz " makes a sound."
str1: .asciiz "Rex"

.text
main:
	li $v0, 9
	li $a0, 4
	syscall
	sw $v0, tmp_t1
	lw $a0, tmp_t1
	la $a1, str1
	jal func_Animal_constructor
	lw $t0, tmp_t1
	sw $t0, var_dog
	la $t0, func_Animal_speak
	sw $t0, tmp_t1
	lw $t0, tmp_t1
	jal $t0
	sw $v0, tmp_t2
	lw $a0, tmp_t2
	li $v0, 4
	syscall

	li $v0, 10
	syscall
func_Animal_constructor:
	addiu $sp, $sp, -8
	sw $ra, 4($sp)
	sw $fp, 0($sp)
	move $fp, $sp
	sw $a1, var_func_Animal_constructor_name
	lw $t0, var_func_Animal_constructor_name
	sw $t0, var_Animal_name
	lw $ra, 4($sp)
	lw $fp, 0($sp)
	addiu $sp, $sp, 8
	jr $ra
func_Animal_speak:
	addiu $sp, $sp, -8
	sw $ra, 4($sp)
	sw $fp, 0($sp)
	move $fp, $sp
	lw $t0, var_Animal_name
	sw $t0, tmp_t1
	lw $a0, tmp_t1
	li $v0, 4
	syscall
	la $a0, str0
	li $v0, 4
	syscall
	lw $t0, var_Animal_name
	sw $t0, tmp_t2
	lw $v0, tmp_t1
	lw $ra, 4($sp)
	lw $fp, 0($sp)
	addiu $sp, $sp, 8
	jr $ra
	lw $ra, 4($sp)
	lw $fp, 0($sp)
	addiu $sp, $sp, 8
	jr $ra
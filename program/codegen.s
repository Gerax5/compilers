.data
var_Animal: .word 0
var_func_Animal_constructor_name: .word 0
var_func_Animal_constructor_this: .word 0
var_func_Animal_speak_name: .word 0
var_func_Animal_speak_t1: .word 0
var_func_Animal_speak_t2: .word 0
var_func_Animal_speak_this: .word 0
str0: .asciiz " makes a sound."

.text
main:

	li $v0, 10
	syscall
func_Animal_constructor:
	addiu $sp, $sp, -8
	sw $ra, 4($sp)
	sw $fp, 0($sp)
	move $fp, $sp
	sw $a0, var_func_Animal_constructor_name
func_Animal_speak:
	addiu $sp, $sp, -8
	sw $ra, 4($sp)
	sw $fp, 0($sp)
	move $fp, $sp
	lw $v0, tmp_t2
	lw $ra, 4($sp)
	lw $fp, 0($sp)
	addiu $sp, $sp, 8
	jr $ra
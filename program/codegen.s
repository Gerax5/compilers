.data
tmp_t1: .word 0
str0: .asciiz "HOLA"

.text
main:
	jal func_makeAdder
	sw $v0, tmp_t1
	lw $a0, tmp_t1
	li $v0, 4
	syscall

	li $v0, 10
	syscall
func_makeAdder:
	addiu $sp, $sp, -8
	sw $ra, 4($sp)
	sw $fp, 0($sp)
	move $fp, $sp
	la $v0, str0
	lw $ra, 4($sp)
	lw $fp, 0($sp)
	addiu $sp, $sp, 8
	jr $ra
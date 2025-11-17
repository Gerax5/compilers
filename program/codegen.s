.data
var_func_makeAdder: .word 0
var_makeAdder: .word 0
tmp_t1: .word 0
var_x: .word 0

.text
main:
	lw $t0, var_x
	li $t1, 1
	add $t2, $t0, $t1
	sw $t2, tmp_t1

	li $v0, 10
	syscall
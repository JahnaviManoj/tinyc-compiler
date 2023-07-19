#import statements
import sys
from enum import Enum

filename = sys.argv[1]

f = open(filename, "r")
input = f.read()


global_var = [0] * 26


#      --------------------LEXER--------------------
symbols = Enum('symbols', ['DO_SYM', 'ELSE_SYM', 'IF_SYM', 'WHILE_SYM', 'LBRA', 'RBRA', 'LPAR', 'RPAR',
       'PLUS', 'MINUS', 'LESS', 'SEMI', 'EQUAL', 'INT', 'ID', 'EOI'])

words = ["do", "else", "if", "while", 'NULL']

input_next = 0

ch = ' '
sym = None
int_val = None
id_name = ''

def next_char():
    global input_next, ch
    if input_next == len(input):
        ch = '\0'   #EOF
    else:
        ch = input[input_next]
        input_next += 1

def next_symbol():
    global ch, sym, id_name, int_val
    match ch:
        case ' ':
            next_char()
            next_symbol()
        case '\n':
            next_char()
            next_symbol()
        case '\0':
            sym = symbols.EOI
        case '{':
            next_char()
            sym = symbols.LBRA
        case '}':
            next_char()
            sym = symbols.RBRA
        case '(':
            next_char()
            sym = symbols.LPAR
        case ')':
            next_char()
            sym = symbols.RPAR
        case '+':
            next_char()
            sym = symbols.PLUS
        case '-':
            next_char()
            sym = symbols.MINUS
        case '<':
            next_char()
            sym = symbols.LESS
        case ';':
            next_char()
            sym = symbols.SEMI
        case '=':
            next_char()
            sym = symbols.EQUAL
        case _:
            if ch.isnumeric():
                int_val = 0
                while ch.isnumeric():
                    int_val = int_val*10 + (ord(ch) - ord('0'))
                    next_char()
                sym = symbols.INT
            elif ch.isalpha():
                id_name = ''
                while ch.isalpha() or ch == '_':
                    id_name += ch
                    next_char()
                i = 1
                for word in words: # if id_name is a keyword
                    if id_name != word:
                        i += 1
                    else:
                        sym = symbols(i)
                        break
                if id_name not in words:   # if id_name is not a keyword
                    if len(id_name) == 1:
                        sym = symbols.ID
                    else:
                        raise SyntaxError
            else:
                raise SyntaxError



#      --------------------PARSER--------------------
parse = Enum('parse', ['VAR', 'CST', 'ADD', 'SUB', 'LT', 'SET', 'IF1', 'IF2', 'WHILE', 'DO', 'EMPTY', 'SEQ', 'EXPR', 'PROG'])

class node:
    def __init__(self, k = None):
        self.kind = k
        self.o1 = self.o2 = self.o3 = None
        self.val = None

def new_node(k):
    x = node(k)
    return x

def parent_exp():    # parent_exp  -->   "(" expr ")"
    global sym
    if sym == symbols.LPAR:
        next_symbol()
    else:
        raise SyntaxError
    x = expr()
    if sym == symbols.RPAR:
        next_symbol()
    else:
        raise SyntaxError
    return x

def expr():    # expr  -->   test | id "=" expr
    global sym
    if sym != symbols.ID:
        return test()
    x = test()
    if x.kind == parse.VAR and sym == symbols.EQUAL:
        t = x
        x = new_node(parse.SET)
        next_symbol()
        x.o1 = t
        x.o2 = expr()
    return x

def test():    # test  -->   sum_exp | sum_exp "<" sum_exp
    global sym
    x = sum_exp()
    if sym == symbols.LESS:
        t = x
        x = new_node(parse.LT)
        next_symbol()
        x.o1 = t
        x.o2 = sum_exp()
    return x

def sum_exp():    # sum_exp  -->   term | sum "+" term | sum "-" term
    global sym
    x = term()
    while sym == symbols.PLUS or sym == symbols.MINUS:
        t = x
        if sym == symbols.PLUS:
            x = new_node(parse.ADD)
        elif sym == symbols.MINUS:
            x = new_node(parse.SUB)
        next_symbol()
        x.o1 = t
        x.o2 = term()
    return x

def term():    # term  -->   id | int | paren_exp
    global sym, id_name, int_val
    if sym == symbols.ID:
        x = new_node(parse.VAR)
        x.val = ord(id_name[0]) - ord('a')
        next_symbol()
    elif sym == symbols.INT:
        x = new_node(parse.CST)
        x.val = int_val
        next_symbol()
    else:
        x = parent_exp()
    return x

def statement():
    global sym
    if sym == symbols.IF_SYM: #  "if" paren_expr statement
        x = new_node(parse.IF1)
        next_symbol()
        x.o1 = parent_exp()
        x.o2 = statement()
        if sym == symbols.ELSE_SYM: #  ... "else" statement
            x.kind = parse.IF2
            next_symbol()
            x.o3 = statement()
    elif sym == symbols.WHILE_SYM: #  "while" paren_expr statement
        x = new_node(parse.WHILE)
        next_symbol()
        x.o1 = parent_exp()
        x.o2 = statement()
    elif sym == symbols.DO_SYM: #  "do" statement "while" paren_expr
        x = new_node(parse.DO)
        next_symbol()
        x.o1 = statement()
        if sym == symbols.WHILE_SYM:
            next_symbol()
        else:
            raise SyntaxError
        x.o2 = parent_exp()
        if sym == symbols.SEMI:
            next_symbol()
        else:
            raise SyntaxError
    elif sym == symbols.SEMI: #  ";"
        x = new_node(parse.EMPTY)
        next_symbol()
    elif sym == symbols.LBRA: #  "{" { statement } "}"
        x = new_node(parse.EMPTY)
        next_symbol()
        while sym != symbols.RBRA:
            t = x
            x = new_node(parse.SEQ)
            x.o1 = t
            x.o2 = statement()
        next_symbol()
    else: #  expr ";"
        x = new_node(parse.EXPR)
        x.o1 = expr()
        if sym == symbols.SEMI:
            next_symbol()
        else:
            raise SyntaxError
    return x

def program(): #   program ::= statement
    x = new_node(parse.PROG)
    next_symbol()
    x.o1 = statement()
    if sym != symbols.EOI:
        raise SyntaxError
    return x
    




#      --------------------CODE GENERATOR--------------------
code_gen = Enum('code_gen', ['IFETCH', 'ISTORE', 'IPUSH', 'IPOP', 'IADD', 'ISUB', 'ILT', 'JZ', 'JNZ', 'JMP', 'HALT'])

object = []

def g(c):
    global object
    object.append(c)

def hole():
    global object
    object.append(None)
    return len(object) - 1

def fix(src, dst):
    global object
    object[src] = dst

def c(x):
    match x.kind:
        case parse.VAR:
            g(code_gen.IFETCH)
            g(x.val)
        case parse.CST:
            g(code_gen.IPUSH)
            g(x.val)
        case parse.ADD:
            c(x.o1)
            c(x.o2)
            g(code_gen.IADD)
        case parse.SUB:
            c(x.o1)
            c(x.o2)
            g(code_gen.ISUB)
        case parse.LT:
            c(x.o1)
            c(x.o2)
            g(code_gen.ILT)
        case parse.SET:
            c(x.o2)
            g(code_gen.ISTORE)
            g(x.o1.val)
        case parse.IF1:
            c(x.o1)
            g(code_gen.JZ)
            p1 = hole()
            c(x.o2)
            fix(p1, len(object))
        case parse.IF2:
            c(x.o1)
            g(code_gen.JZ)
            p1 = hole()
            c(x.o2)
            g(code_gen.JMP)
            p2 = hole()
            fix(p1, len(object))
            c(x.o3)
            fix(p2, len(object))
        case parse.WHILE:
            p1 = len(object)
            c(x.o1)
            g(code_gen.JZ)
            p2 = hole()
            c(x.o2)
            g(code_gen.JMP)
            fix(hole(), p1)
            fix(p2, len(object))
        case parse.DO:
            p1 = len(object)
            c(x.o1)
            c(x.o2)
            g(code_gen.JNZ)
            fix(hole(), p1)
        case parse.EMPTY:
            pass
        case parse.SEQ:
            c(x.o1)
            c(x.o2)
        case parse.EXPR:
            c(x.o1)
            g(code_gen.IPOP)
        case parse.PROG:
            c(x.o1)
            g(code_gen.HALT)



#      --------------------VIRTUAL MACHINE--------------------

stack = [None] * 500
sp = 0
pc = 0

def run():
    global stack, pc, sp
    match object[pc]:
        case code_gen.IFETCH:
            pc += 1
            stack[sp] = global_var[object[pc]]
            sp += 1
            pc += 1
            run()
        case code_gen.ISTORE:
            pc += 1
            global_var[object[pc]] = stack[sp - 1]
            pc += 1
            run()
        case code_gen.IPUSH:
            pc += 1
            stack[sp] = object[pc]
            pc += 1
            sp += 1
            run()
        case code_gen.IPOP:
            pc += 1
            sp -= 1
            run()
        case code_gen.IADD:
            pc += 1
            stack[sp - 2] = stack[sp - 2] + stack[sp - 1]
            sp -= 1
            run()
        case code_gen.ISUB:
            pc += 1
            stack[sp - 2] = stack[sp - 2] - stack[sp - 1]
            sp -= 1
            run()
        case code_gen.ILT:
            pc += 1
            stack[sp - 2] = stack[sp - 2] < stack[sp - 1]
            sp -= 1
            run()
        case code_gen.JMP:
            pc += 1
            pc = object[pc]
            run()
        case code_gen.JZ:
            pc += 1
            sp -= 1
            if stack[sp] == 0:
                pc = object[pc]
            else:
                pc += 1
            run()
        case code_gen.JNZ:
            pc += 1
            sp -= 1
            if stack[sp] != 0:
                pc = object[pc]
            else:
                pc += 1
            run()


#      --------------------MAIN--------------------

c(program())
run()
for i in range(26):
    if global_var[i] != 0:
        print(chr(ord('a') + i), " = ", global_var[i])
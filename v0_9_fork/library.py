'''LIBRARY FILE'''

# COMPILER CODE

import re

'''Converting expressions into RPN'''

OPERATIONS = "+-*/%^\\~"

def is_number(s):
    if s.isdigit(): # Integer
        return True
    elif re.match(r"\d+\.\d+", s): # Float
        return True
    return False

class Number:
    def __init__(self, value):
        self.value = value
    
    def to_str(self):
        return f"{self.value}"
    
    def __repr__(self):
        return f"Number({self.value})"

class String:
    def __init__(self, string):
        self.string = string[1:-1]
    
    def to_str(self):
        return f'"{self.string}"'
    
    def __repr__(self):
        return f"String({self.string})"

class Variable:
    def __init__(self, name):
        self.name = name
    
    def to_str(self):
        return f"{self.name}"
    
    def __repr__(self):
        return f"Variable({self.name})"

def precedence(operator):
    if operator == "~":
        return 4
    if operator == "^":
        return 3
    elif operator in "*/\\":
        return 2
    elif operator in "+-":
        return 1
    else:
        return -1

def associativity(operator):
    return "R" if operator == "^" else "L"

def extract_components_from_infix(s):
    tokens = []
    i = 0
    while i < len(s):
        char = s[i]
        if char == "'" or char == '"': # string quotes
            tokens.append(String(part := s[i:s[i+1:].find(char)+i+2]))
        elif char in OPERATIONS+"()": # operation or bracket
            tokens.append(part := char)
        elif char == "[": # open square backet denotes accessing item in array
            tokens.append(part := "~")
            tokens.append("(")
        elif char == "]": # close square bracket
            tokens.append(")")
        elif char.isdigit() or char == ".": # start of a number
            if i == len(s) - 1:
                tokens.append(Number(part := char))
            else:
                for j, c in enumerate(s[i+1:]):
                    if not c.isdigit() and c != ".":
                        tokens.append(Number(part := s[i:j+i+1]))
                        break
                else:
                    tokens.append(Number(part := s[i:]))
        elif char.isalpha(): # start of a variable
            if i == len(s) - 1:
                tokens.append(Variable(part := char))
            else:
                for j, c in enumerate(s[i+1:]):
                    if not c.isalpha() and not c.isdigit():
                        tokens.append(Variable(part := s[i:j+i+1]))
                        break
                else:
                    tokens.append(Variable(part := s[i:]))
        i += len(part)
    return tokens

def convert_to_rpn(s):
    tokens = extract_components_from_infix(s)
    operator_stack = []
    result = []
    for token in tokens:
        if type(token) in (Number, String, Variable): # Operand
            result.append(token)
        elif token == "(": # Open bracket
            operator_stack.append(token)
        elif token == ")": # Close bracket
            while operator_stack and operator_stack[-1] != "(": # While stack is not empty and item at top of stack is not open bracket
                result.append(operator_stack.pop()) # Pop from stack and add to result
            operator_stack.pop() # Pop the open bracket
        else: # Operator
            while operator_stack and (precedence(token) < precedence(operator_stack[-1]) or \
                             precedence(token) == precedence(operator_stack[-1]) and associativity(token) == "L"): 
                # Precedence of token <= precedence of operator on stack, accounting for associativity of repeated exponentiation (aka. tetration)
                result.append(operator_stack.pop()) # Pop from stack and add to reuslt
            operator_stack.append(token)
    
    while operator_stack:
        result.append(operator_stack.pop())
    
    return result

def convert_expression(s):
    return ','.join([token.to_str() if type(token) != str else token for token in convert_to_rpn(s)])

def is_value(s):
    return len(convert_expression(s)) == 1

'''Actual compiling process'''

class Compiler:

    REGISTERS = ["__r0__", "__r1__", "__r2__", "__r3__"]
    INDENT_SIZE = 4

    @staticmethod
    def __num_indents(code, ln):
        for idx, char in enumerate(code[ln]):
            if char != " ":
                if idx % Compiler.INDENT_SIZE != 0:
                    raise SyntaxError(f"INDENT ERROR occurred on line {ln}")
                return idx // Compiler.INDENT_SIZE

    @staticmethod
    def __find_end_of_if_statement(code, start_line, indents):
        for ln in range(start_line, len(code)):
            if Compiler.__num_indents(code, ln) <= indents and not re.match(r" *else:", code[ln]) and not re.match(r" *elif.*:", code[ln]):
                return ln

    @staticmethod
    def __find_end_of_curr_if_block(code, start_line, indents):
        for ln in range(start_line, len(code)):
            if Compiler.__num_indents(code, ln) == indents:
                return ln

    @staticmethod
    def find_else_block(code, start_line, indents):
        for ln in range(start_line, len(code)):
            if Compiler.__num_indents(code, ln) == indents and re.match(r" *else:", code[ln]):
                return ln

    @staticmethod
    def __shift_pointers(assembly_code, start_line, split_point=None, only_pointers=False):
        output = {}
        for ln, line in assembly_code.items():
            if line[0] == "B" and "break" not in line:
                ptr = int(line.split(' ')[1])
                if split_point is None or (split_point is not None and ptr > split_point):
                    line = f"{line.split(' ')[0]} {ptr + start_line}"
            output[ln if only_pointers else ln+start_line] = line
        return output

    @staticmethod
    def __extend_code(assembly_code, new_code, start_line):
        for k, v in Compiler.__shift_pointers(new_code, start_line).items():
            assembly_code[k] = v
        return assembly_code

    @staticmethod
    def __find_pointers_to(assembly_code, ptr): # Function to find pointers to a given line
        for ln, line in assembly_code.items():
            if line[0] == "B" and int(line.split(" ")[1]) == ptr:
                yield ln

    @staticmethod
    def __next_non_pass_line(assembly_code, linenum): # Function to find next non-pass line after given line number
        for ln in range(linenum, len(assembly_code)):
            if assembly_code[ln] != "PASS":
                return ln

    @staticmethod
    def __extract_section(assembly_code, start, end): # Function to extract code between inclusive start and end bounds
        new_code = {}
        for ln, line in assembly_code.items():
            if start <= ln <= end:
                new_code[ln] = line
        return new_code

    @staticmethod
    def __compile_rpn(rpn, store=None, used_reg=None):

        registers = [False for _ in range(len(Compiler.REGISTERS))] # Initialise list of registers that have something stored
        if used_reg is not None: # If a register has been used by another part of the comparison operation
            registers[Compiler.REGISTERS.index(used_reg)] = True # Block out this register
        assembly_code = {}
        linenum = 0
        stack = []

        for idx, token in enumerate(rpn): # Loop through all tokens in RPN list
            if token in OPERATIONS: # Operator found
                reg = min([i for i, v in enumerate(registers) if not v]) # Get next free register index
                register = Compiler.REGISTERS[reg] # Get name of register
                if idx == len(rpn) - 1 and store is not None: # If a store is required and this is the last operation
                    register = store
                operand2 = stack.pop()
                operand1 = stack.pop()
                match token:
                    case "+": assembly_code[linenum] = f"ADD {register} {operand1} {operand2}"
                    case "-": assembly_code[linenum] = f"SUB {register} {operand1} {operand2}"
                    case "*": assembly_code[linenum] = f"MTP {register} {operand1} {operand2}" 
                    case "/": assembly_code[linenum] = f"DIV {register} {operand1} {operand2}"
                    case "^": assembly_code[linenum] = f"EXP {register} {operand1} {operand2}"
                    case "%": assembly_code[linenum] = f"MOD {register} {operand1} {operand2}"
                    case "\\": assembly_code[linenum] = f"FDV {register} {operand1} {operand2}"
                    case "~": assembly_code[linenum] = f"AGT {register} {operand1} {operand2}"
                stack.append(register)
                if store is None or idx < len(rpn) - 1: # If store operation is not required
                    registers[reg] = True # Set current register to be used
                    if operand1 in Compiler.REGISTERS:
                        registers[Compiler.REGISTERS.index(operand1)] = False # Free up register if used as operand
                    if operand2 in Compiler.REGISTERS:
                        registers[Compiler.REGISTERS.index(operand2)] = False # Free up register if used as operand
                linenum += 1
            else: # Operand found
                if token.isdigit(): # number
                    stack.append(token)
                else: # string or variable
                    stack.append(token)
        
        return assembly_code, stack[-1] # Return assembly code and the register where output is stored at

    @staticmethod
    def __compile_argument(expression, used_reg=None): # Compile argument
        return Compiler.__compile_rpn(convert_expression(expression).split(","), used_reg=used_reg)

    @staticmethod
    def __compile_assignment(line): # Compile Assignment operations

        lefthalf, righthalf = line.split("=") # Split assignment into two halves
        rpn = convert_expression(righthalf).split(",") # Convert the right hand side into RPN
        assembly_code = {}

        if len(rpn) == 1: # If only one operand
            assembly_code[0] = f"STR {lefthalf} {rpn[0]}" # Store directly
        else: # Otherwise
            assembly_code, _ = Compiler.__compile_rpn(rpn, store=lefthalf) # Compile RPN with store operation included
        return assembly_code

    @staticmethod
    def __compile_comparison(line): # Compile comparison operation

        assembly_code = {}

        condition = line.split("if")[1][:-1] # Get the if statement
        for cond, keyword in {"==": "BEQ", "!=": "BNE", ">": "BGT", "<": "BLT"}.items(): # Loop through all compare possibilities
            if re.match(r".*"+cond+r".*", condition): # Check if line matches

                lefthalf, righthalf = condition.split(cond) # Split condition into lefthalf and righthalf
                lrpn, rrpn = convert_expression(lefthalf).split(","), convert_expression(righthalf).split(",")

                '''Compile rpn for LHS and RHS and add compare instruction'''
                if len(lrpn) == 1 and len(rrpn) == 1: # both do not require compiling
                    assembly_code[0] = f"CMP {lrpn[0]} {rrpn[0]}"

                elif len(lrpn) == 1 and len(rrpn) > 1: # right half requires compiling
                    assembly_code, lastreg = Compiler.__compile_rpn(rrpn)
                    linenum = len(assembly_code)
                    assembly_code[linenum] = f"CMP {lrpn[0]} {lastreg}"

                elif len(lrpn) > 1 and len(rrpn) == 1: # left half requires compiling
                    assembly_code, lastreg = Compiler.__compile_rpn(lrpn)
                    linenum = len(assembly_code)
                    assembly_code[linenum] = f"CMP {rrpn[0]} {lastreg}"
                
                else: # both sides need compiling
                    assembly_code, lastreg = Compiler.__compile_rpn(lrpn) # Compile LHS and store register with stored value
                    linenum = len(assembly_code)
                    new_code, lastreg2 = Compiler.__compile_rpn(rrpn, used_reg=lastreg) # Compile RHS whilst blocking out register that is being used
                    assembly_code = Compiler.__extend_code(assembly_code, new_code, linenum) # Extend the assembly code
                    assembly_code[len(assembly_code)] = f"CMP {lastreg} {lastreg2}" # Add the compare operation

                linenum = len(assembly_code)
                assembly_code[linenum] = f"{keyword} {linenum+2}" # Add branch instruction
                return assembly_code

    @staticmethod
    def __remove_pass_statements(assembly_code): # Remove pass statements from compiled code
        ln = 0
        while ln < len(assembly_code) - 1:
            line = assembly_code[ln]
            if line == "PASS":
                next_line = Compiler.__next_non_pass_line(assembly_code, ln)
                for loc in Compiler.__find_pointers_to(assembly_code, ln):
                    assembly_code[loc].replace(str(ln), str(next_line))
                assembly_code = Compiler.__extend_code(Compiler.__shift_pointers(Compiler.__extract_section(assembly_code, 0, ln), -1, split_point=ln, only_pointers=True), 
                                            Compiler.__shift_pointers(Compiler.__extract_section(assembly_code, ln+1, len(assembly_code)), -1, split_point=ln), 0)
                ln = 0
            ln += 1
        assembly_code[len(assembly_code)-1] = "HALT"
        return assembly_code

    @staticmethod
    def __compile_code(code): # Compile code function with pass statements

        '''Handle cases where there is no line after if statement or no else statement'''
        if "END" not in code and code: # If there is no ending statement in the current code
            code += [f"{Compiler.__num_indents(code, 0)*' '*Compiler.INDENT_SIZE}END"] # Add the ending statement

        assembly_code = {} # Initialise assembly code dictionary
        ptrs = {} # Initialise dictionary for if statement pointers
        break_ptrs = {} # Initialise dictionary for break statement pointers
        ln = 0 # Set current line number to be 0

        try:
            while ln < len(code):

                line = code[ln]
                line = line.replace(" ", "")
                linenum = len(assembly_code)

                '''Fill in pointers if line found for if statements'''
                if ln in ptrs: # If the pointer line matches
                    for actual_line in ptrs[ln]: # Loop through pointer lines
                        assembly_code[actual_line] = assembly_code[actual_line].replace("ptr", str(linenum)) # Replace the temporary pointer with the actual line
                
                '''Fill in pointers if line found for break statements'''
                if ln in break_ptrs:
                    for k, v in assembly_code.items():
                        if "break" in v:
                            assembly_code[k] = v.replace("break", str(break_ptrs[ln]))
                
                if re.match(r"if.*:", line) or re.match(r"elif.*:", line) or re.match(r"while.*:", line): # If statement, elif statement or while loop
                    
                    while_loop = False
                    if re.match(r"elif.*:", line): # Elif statement
                        line = line.replace("elif", "if")
                    elif re.match(r"while.*:", line): # While loop
                        line = line.replace("while", "if")
                        while_loop = True
                    
                    '''Add the compare and initial branch instruction'''
                    linenum = len(assembly_code)
                    if while_loop:
                        while_instruction_linenum = linenum
                    assembly_code = Compiler.__extend_code(assembly_code, Compiler.__compile_comparison(line), linenum)
                    
                    '''Add else branch instruction pointer'''
                    linenum = len(assembly_code)
                    end_of_curr_if_block = Compiler.__find_end_of_curr_if_block(code, ln+1, Compiler.__num_indents(code, ln)) # Find when the current if block ends
                    assembly_code[linenum] = f"BAL ptr" # Add else instruction
                    else_instruction = linenum
                    
                    '''Compile code inside the if statement'''
                    linenum = len(assembly_code)
                    end_of_if_statement = Compiler.__find_end_of_if_statement(code, ln+1, Compiler.__num_indents(code, ln)) # Find when the if statement ends
                    assembly_code = Compiler.__extend_code(assembly_code, Compiler.__compile_code(code[ln+1:end_of_curr_if_block]), linenum) # Compile whatever code there is inside the if block
                    if while_loop: # While loop
                        assembly_code[linenum := len(assembly_code)] = f"BAL {while_instruction_linenum}"
                    else:
                        assembly_code[linenum := len(assembly_code)] = "BAL ptr"
                        if end_of_if_statement not in ptrs:
                            ptrs[end_of_if_statement] = set()
                        ptrs[end_of_if_statement].add(linenum)

                    '''Fill in address for else branch instruction'''
                    assembly_code[else_instruction] = assembly_code[else_instruction].replace("ptr", str(len(assembly_code)))
                    ln = end_of_curr_if_block # Set line in original code to jump to next
                
                elif re.match(r"for(.*,.*,.*):", line): # For loop
                    linenum = len(assembly_code)
                    initialisation, condition, increment = line.replace("):", "").replace("for(", "").split(",") # split for loop code into three sections
                    end_of_for_loop = Compiler.__find_end_of_if_statement(code,ln+1, indents := Compiler.__num_indents(code, ln)) # Find when the for loop ends
                    loop_code = [" "*Compiler.INDENT_SIZE*indents + initialisation, f"{' '*Compiler.INDENT_SIZE*indents}while {condition}:"] + code[ln+1:end_of_for_loop] + [f"{' '*Compiler.INDENT_SIZE*(indents+1)}{increment}"] # convert for loop into a while loop
                    assembly_code = Compiler.__extend_code(assembly_code, Compiler.__compile_code(loop_code), linenum)
                    ln = end_of_for_loop
                    break_ptrs[ln] = len(assembly_code)
                
                elif re.match(r"else:", line): # Else statement
                    linenum = len(assembly_code)
                    end_of_if_statement = Compiler.__find_end_of_if_statement(code, ln+1, Compiler.__num_indents(code, ln)) # Find when the if statement ends
                    assembly_code = Compiler.__extend_code(assembly_code, Compiler.__compile_code(code[ln+1:end_of_if_statement]), linenum) # Compile whatever code there is inside the if block
                    ln = end_of_if_statement
                
                elif re.match(r"break", line): # Break statement
                    assembly_code[linenum] = "BAL break"
                    ln += 1
                
                elif re.match(r".*=array(.*)", line): # Array declaration
                    name, size = line[:-1].split("=array(")
                    if not is_number(size):
                        new_code, size = Compiler.__compile_argument(size)
                        assembly_code = Compiler.__extend_code(assembly_code, new_code, linenum)
                    assembly_code[linenum := len(assembly_code)] = f"ARR {name} {size}"
                    ln += 1
                
                elif re.match(r".*\[.*\]=.*", line): # Assignment to an array
                    __front, expression = line.split("]=")
                    array_name, index = __front.split("[")
                    if not is_value(index):
                        new_code1, index = Compiler.__compile_argument(index)
                        assembly_code = Compiler.__extend_code(assembly_code, new_code1, linenum)
                    if not is_value(expression):
                        new_code2, expression = Compiler.__compile_argument(expression, used_reg=index if not is_value(index) else None)
                        assembly_code = Compiler.__extend_code(assembly_code, new_code2, len(assembly_code))
                    assembly_code[linenum := len(assembly_code)] = f"AMV {array_name} {index} {expression}"
                    ln += 1
                
                elif re.match(r".*\+=.*", line): # Fast Addition operator
                    variable, operand = line.split("+=")
                    assembly_code = Compiler.__extend_code(assembly_code, Compiler.__compile_code([f"{variable} = {variable} + ({operand})"]), linenum) # Convert fast addition operator into compilable syntax
                    ln += 1
                
                elif re.match(r".*-=.*", line): # Fast Subtraction operator
                    variable, operand = line.split("-=")
                    assembly_code = Compiler.__extend_code(assembly_code, Compiler.__compile_code([f"{variable} = {variable} - ({operand})"]), linenum) # Convert fast subtraction operator into compilable syntax
                    ln += 1
                
                elif re.match(r".*\*=.*", line): # Fast Multiplication operator
                    variable, operand = line.split("*=")
                    assembly_code = Compiler.__extend_code(assembly_code, Compiler.__compile_code([f"{variable} = {variable} * ({operand})"]), linenum) # Convert fast multiplication operator into compilable syntax
                    ln += 1
                
                elif re.match(r".*/=.*", line): # Fast Division operator
                    variable, operand = line.split("/=")
                    assembly_code = Compiler.__extend_code(assembly_code, Compiler.__compile_code([f"{variable} = {variable} / ({operand})"]), linenum) # Convert fast division operator into compilable syntax
                    ln += 1
                
                elif re.match(r".*^=.*", line): # Fast Exponentiation operator
                    variable, operand = line.split("^=")
                    assembly_code = Compiler.__extend_code(assembly_code, Compiler.__compile_code([f"{variable} = {variable} ^ ({operand})"]), linenum) # Convert fast exponentiation operator into compilable syntax
                    ln += 1
                
                elif re.match(r".*%=.*", line): # Fast Modulo operator
                    variable, operand = line.split("%=")
                    assembly_code = Compiler.__extend_code(assembly_code, Compiler.__compile_code([f"{variable} = {variable} % ({operand})"]), linenum) # Convert fast modulo operator into compilable syntax
                    ln += 1
                
                elif re.match(r".*\\=.*", line): # Fast Floor Division operator
                    variable, operand = line.split("\\=")
                    assembly_code = Compiler.__extend_code(assembly_code, Compiler.__compile_code([f"{variable} = {variable} \\ ({operand})"]), linenum) # Convert fast floor division operator into compilable syntax
                    ln += 1

                elif re.match(r".*=.*", line): # Assignment
                    assembly_code = Compiler.__extend_code(assembly_code, Compiler.__compile_assignment(line), linenum) # Compile assignment RPN into multiple statements
                    ln += 1
                
                elif re.match(r".*\+\+", line): # Increment operator
                    variable = line.replace("++", "")
                    assembly_code = Compiler.__extend_code(assembly_code, Compiler.__compile_code([f"{variable} = {variable} + 1"]), linenum) # Convert increment operator into compilable syntax
                    ln += 1
                
                elif re.match(r".*--", line): # Decrement operator
                    variable = line.replace("--", "")
                    assembly_code = Compiler.__extend_code(assembly_code, Compiler.__compile_code([f"{variable} = {variable} - 1"]), linenum) # Convert decrement operator into compilable syntax
                    ln += 1

                elif re.match(r"print(.*)", line): # Print Statement
                    argument = line.split("print(")[1][:-1]
                    if not is_number(argument):
                        new_code, argument = Compiler.__compile_argument(argument)
                        assembly_code = Compiler.__extend_code(assembly_code, new_code, linenum)
                    assembly_code[linenum] = f"PRT {argument}"
                    ln += 1

                elif line == "END": # Pass statement used to make compiling process easier
                    assembly_code[linenum] = "PASS"
                    ln += 1

                else:
                    raise SyntaxError(f"Syntax Error occurred on line {linenum+1}") # Syntax Error
                
        except SyntaxError as err:
            print(err)
            
        return assembly_code

    @staticmethod
    def compile_code(code): # Compile code function without pass statements
        return Compiler.__remove_pass_statements(Compiler.__compile_code(code))

# SIMULATOR CODE

class PythonSimulation:

    NUMERICAL_INSTRUCTIONS = ("ADD", "SUB", "MTP", "DIV", "EXP", "MOD", "FDV")

    def __init__(self): # Constructor
        self.__variables = {}
        self.__status_register = (None, None, None, None) # Equal, Not Equal, Greater Than, Less Than

    def __fetch_variable(self, var):
        if var.isdigit():
            return int(var)
        elif is_number(var):
            return float(var)
        else:
            return self.__variables[var]

    def execute_assembly_code(self, assembly_code, debug=False): # Method to execute assembly code
        output = []
        ln = 0
        try:
            while True:
                ln = int(ln)
                line = assembly_code[ln]
                if debug:
                    yield ln, self.__variables, self.__status_register, output   
                if line == "HALT":
                    break
                opcode, operand = line.split(" ")[0], line.split(" ")[1:]
                if opcode in self.NUMERICAL_INSTRUCTIONS: # Numerical instruction
                    var, op1, op2 = operand
                    num1, num2 = self.__fetch_variable(op1), self.__fetch_variable(op2)
                    match opcode:
                        case "ADD": self.__variables[var] = num1 + num2
                        case "SUB": self.__variables[var] = num1 - num2
                        case "MTP": self.__variables[var] = num1 * num2
                        case "DIV": self.__variables[var] = num1 / num2
                        case "EXP": self.__variables[var] = num1 ** num2
                        case "MOD": self.__variables[var] = num1 % num2
                        case "FDV": self.__variables[var] = num1 // num2
                    ln += 1
                    if var == "__temp__": 
                        pass
                elif opcode == "STR": # Store instruction
                    var, op = operand
                    number = self.__fetch_variable(op)
                    self.__variables[var] = number
                    ln += 1
                elif opcode == "ARR": # Declare Array instruction
                    name, length = operand
                    length = int(length) if is_number(length) else self.__variables[length]
                    self.__variables[name] = [None for _ in range(int(length))]
                    ln += 1
                elif opcode == "AMV": # Set Item in Array instruction
                    name, index, value = operand
                    index = int(index) if is_number(index) else self.__variables[index]
                    value = self.__fetch_variable(value)
                    self.__variables[name][int(index)] = value
                    ln += 1
                elif opcode == "AGT": # Read Item in Array instruction
                    register, name, index = operand
                    index = int(index) if is_number(index) else self.__variables[index]
                    self.__variables[register] = self.__variables[name][int(index)]
                    ln += 1
                elif opcode == "CMP": # Compare instruction
                    lhs, rhs = operand
                    num1, num2 = self.__fetch_variable(lhs), self.__fetch_variable(rhs)
                    self.__status_register = (num1 == num2, num1 != num2, num1 > num2, num1 < num2)
                    ln += 1
                elif opcode[0] == "B": # Branch instruction
                    address = float(operand[0])
                    if opcode == "BAL":
                        ln = address
                    elif opcode == "BEQ" and self.__status_register[0] or opcode == "BNE" and self.__status_register[1] or \
                        opcode == "BGT" and self.__status_register[2] or opcode == "BLT" and self.__status_register[3]:
                        ln = address
                    else:
                        ln += 1
                elif opcode == "PRT": # Print instruction
                    val = float(operand[0]) if is_number(operand[0]) else self.__variables[operand[0]]
                    print(val)  
                    output.append(val)
                    ln += 1   
        except Exception as err:
            print(f"Error occurred on line {ln}: {err}")

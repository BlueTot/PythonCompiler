import re

OPERATIONS = "+-*/%^"
INDENT_SIZE = 4
VARIABLES = {}

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
    if operator == "^":
        return 3
    elif operator in "*/":
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
        elif char.isdigit(): # start of a number
            if i == len(s) - 1:
                tokens.append(Number(part := char))
            else:
                for j, c in enumerate(s[i+1:]):
                    if not c.isdigit():
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

def num_indents(code, ln):
    for idx, char in enumerate(code[ln]):
        if char != " ":
            if idx % INDENT_SIZE != 0:
                raise SyntaxError(f"INDENT ERROR occurred on line {ln}")
            return idx // INDENT_SIZE

def find_end_of_if_statement(code, start_line, indents):
    for ln in range(start_line, len(code)):
        if num_indents(code, ln) <= indents and not re.match(r" *else:", code[ln]):
            return ln

def add_else_statements(code):
    if_statement_stack = []
    output = []
    for ln, line in enumerate(code):
        if if_statement_stack and not re.match(r" *elif.*:", line) and not re.match(r" *else:", line) and num_indents(code, if_statement_stack[-1]) >= num_indents(code, ln):
            output.append(f"{num_indents(code, if_statement_stack[-1])*' '*INDENT_SIZE}else:")
            if_statement_stack.pop()
        if re.match(r" *if.*:", line):
            if_statement_stack.append(ln)
        if re.match(r" *else:", line):                                                          
            if_statement_stack.pop()
        output.append(line)
    if if_statement_stack:
        output.append(f"{num_indents(code, if_statement_stack[-1])*' '*INDENT_SIZE}else:")
        if_statement_stack.pop()
    output.append("END")
    return output

def compile_intermediate(code):
    code = add_else_statements(code)
    output = []
    curr_extra_indent = 0
    for ln, line in enumerate(code):
        indents = num_indents(code, ln)
        if re.match(r" *elif.*:", line): # elif statement
            output.append(f"{(indents+curr_extra_indent)*' '*INDENT_SIZE}else:")
            curr_extra_indent += 1
            output.append(f"{(indents+curr_extra_indent)*' '*INDENT_SIZE}if{line.split('elif')[1]}")
        elif line == "END": 
            output.append("END")
        else: # Otherwise
            output.append(f"{(curr_extra_indent)*' '*INDENT_SIZE}{line}")
    return output

def compile_code(code):
    code = compile_intermediate(code)
    assembly_code = {}
    if_statement_stack = []
    ptrs = {}
    last_if_statement_line = None
    last_if_statement_ln = None
    try:
        for ln, line in enumerate(code):
            #print(if_statement_stack, ptrs)
            linenum = len(assembly_code) # Get assembly code line number
            line = line.replace(" ", "") # Remove spaces
            if if_statement_stack: # If an if statement has been recorded
                if num_indents(code, if_statement_stack[-1]) >= num_indents(code, ln): # If number of indents match
                    dest_line = find_end_of_if_statement(code, if_statement_stack[-1]+1, num_indents(code, if_statement_stack[-1])) # Get destination line
                    if dest_line is not None: # If destination line is not None to handle cases where an if statement is the last line in the code
                        if dest_line not in ptrs:
                            ptrs[dest_line] = set() # Create new set of pointers
                        ptrs[dest_line].add(linenum)
                        assembly_code[linenum] = f"BAL ptr" # Add temporary branch to pointer instruction
                        linenum += 1
                    if_statement_stack.pop()
            if ln in ptrs: # If the pointer line matches
                for actual_line in ptrs[ln]: # Loop through pointer lines
                    assembly_code[actual_line] = assembly_code[actual_line].replace("ptr", str(linenum)) # Replace the temporary pointer with the actual line
            if re.match(r"if.*:", line) or re.match(r"elif.*:", line): # If and elif statement
                condition = line.split("if")[1][:-1] # Get the if statement
                for cond, keyword in {"==": "BEQ", "!=": "BNE", ">": "BGT", "<": "BLT"}.items(): # Loop through all compare possibilities
                    if re.match(r".*"+cond+r".*", condition): # Check if line matches
                        lefthalf, righthalf = condition.split(cond) # Split condition into lefthalf and righthalf
                        assembly_code[linenum] = f"CMP {convert_expression(lefthalf)} {convert_expression(righthalf)}" # Add compare instruction
                        assembly_code[linenum+1] = f"{keyword} {linenum+2}" # Add branch instruction
                if_statement_stack.append(ln)
                last_if_statement_line = linenum + 1
                last_if_statement_ln = ln + 1
            elif re.match(r"else:", line): # Else statement
                # Slide all statements down one line
                for l in range(max(assembly_code.keys()), last_if_statement_line, -1):
                    assembly_code[l+1] = assembly_code[l]
                # Slide all pointer references down one line
                for k, v in assembly_code.items():
                    if v[0] == "B":
                        instruction = v.split(" ")
                        if instruction[1] != "ptr" and int(instruction[1]) > last_if_statement_line:
                            assembly_code[k] = " ".join([instruction[0], str(int(instruction[1]) + 1)])
                # Slide all pointers down one line
                for k, v in ptrs.items():
                    if k > last_if_statement_ln:
                        ptrs[k] = set([i+1 if i > last_if_statement_line else i for i in v])
                assembly_code[last_if_statement_line+1] = f"BAL {linenum+1}" # Add branch instruction
            elif re.match(r".*=.*", line): # Assignment
                lefthalf, righthalf = line.split("=")
                assembly_code[linenum] = f"ASSIGN {lefthalf} {convert_expression(righthalf)}"
            elif re.match(r"print(.*)", line): # Print Statement
                arguments = line.split("print(")[1][:-1]
                assembly_code[linenum] = f"PRT {arguments}"
            elif line == "END":
                assembly_code[linenum] = "HALT"
            else:
                raise SyntaxError(f"Syntax Error occurred on line {linenum+1}") # Syntax Error
        return assembly_code
    except SyntaxError as err:
        print(err)

if __name__ in "__main__":
    with open("code.txt") as f:
        code = f.read().splitlines()
    print("\nINTERMEDIATE\n")
    for ln, line in enumerate(compile_intermediate(code)):
        print(ln, line)
    print("\nCOMPILED\n")
    for ln, line in compile_code(code).items():
        print(ln, line)
    # print("\nCONVERT ELIFS\n")
    # for ln, line in enumerate(convert_if_statements(code)):
    #     print(ln, line)
    # print("\nELSE STATEMENTS\n")
    # for ln, line in enumerate(add_else_statements(code)):
    #     print(ln, line)

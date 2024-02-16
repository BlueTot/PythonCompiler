import re

OPERATIONS = "+-*/%^"
INDENT_SIZE = 4

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
        if num_indents(code, ln) <= indents and not re.match(r" *else:", code[ln]) and not re.match(r" *elif.*:", code[ln]):
            return ln

def find_end_of_curr_if_block(code, start_line, indents):
    for ln in range(start_line, len(code)):
        if num_indents(code, ln) == indents:
            return ln

def find_else_block(code, start_line, indents):
    for ln in range(start_line, len(code)):
        if num_indents(code, ln) == indents and re.match(r" *else:", code[ln]):
            return ln

def shift_pointers(assembly_code, start_line):
    output = {}
    for ln, line in assembly_code.items():
        if line[0] == "B":
            line = f"{line.split(' ')[0]} {int(line.split(' ')[1]) + start_line}"
        output[ln+start_line] = line
    return output

def compile_code(code):

    '''Handle cases where there is no line after if statement or no else statement'''
    if "END" not in code and code: # If there is no ending statement in the current code
        code += [f"{num_indents(code, 0)*' '*INDENT_SIZE}END"] # Add the ending statement

    assembly_code = {}
    ptrs = {}
    ln = 0

    try:
        while ln < len(code):

            line = code[ln]
            line = line.replace(" ", "")
            linenum = len(assembly_code)

            '''Fill in pointers if line found'''
            if ln in ptrs: # If the pointer line matches
                for actual_line in ptrs[ln]: # Loop through pointer lines
                    assembly_code[actual_line] = assembly_code[actual_line].replace("ptr", str(linenum)) # Replace the temporary pointer with the actual line
            
            if re.match(r"if.*:", line) or re.match(r"elif.*:", line): # If statement or elif statement

                if re.match(r"elif.*:", line): # Elif statement
                    line = line.replace("elif", "if")
                
                '''Add the compare and initial branch instruction'''
                condition = line.split("if")[1][:-1] # Get the if statement
                for cond, keyword in {"==": "BEQ", "!=": "BNE", ">": "BGT", "<": "BLT"}.items(): # Loop through all compare possibilities
                    if re.match(r".*"+cond+r".*", condition): # Check if line matches
                        lefthalf, righthalf = condition.split(cond) # Split condition into lefthalf and righthalf
                        assembly_code[linenum] = f"CMP {convert_expression(lefthalf)} {convert_expression(righthalf)}" # Add compare instruction
                        assembly_code[linenum+1] = f"{keyword} {linenum+3}" # Add branch instruction
                        break
                
                '''Add else branch instruction pointer'''
                end_of_curr_if_block = find_end_of_curr_if_block(code, ln+1, num_indents(code, ln)) # Find when the current if block ends
                assembly_code[linenum+2] = f"BAL ptr" # Add else instruction
                else_instruction = linenum+2
                
                '''Compile code inside the if statement'''
                linenum = len(assembly_code)
                end_of_if_statement = find_end_of_if_statement(code, ln+1, num_indents(code, ln)) # Find when the if statement ends
                for k, v in shift_pointers(compile_code(code[ln+1:end_of_curr_if_block]), linenum).items(): # Compile whatever code there is inside the if block
                    assembly_code[k] = v
                assembly_code[linenum := len(assembly_code)] = "BAL ptr"
                if end_of_if_statement not in ptrs:
                    ptrs[end_of_if_statement] = set()
                ptrs[end_of_if_statement].add(linenum)

                '''Fill in address for else branch instruction'''
                assembly_code[else_instruction] = assembly_code[else_instruction].replace("ptr", str(len(assembly_code)))
                ln = end_of_curr_if_block # Set line in original code to jump to next
            
            elif re.match(r"else:", line): # Else statement
                linenum = len(assembly_code)
                end_of_if_statement = find_end_of_if_statement(code, ln+1, num_indents(code, ln)) # Find when the if statement ends
                for k, v in shift_pointers(compile_code(code[ln+1:end_of_if_statement]), linenum).items(): # Compile whatever code there is inside the if block
                    assembly_code[k] = v
                ln = end_of_if_statement

            elif re.match(r".*=.*", line): # Assignment
                lefthalf, righthalf = line.split("=")
                assembly_code[linenum] = f"ASSIGN {lefthalf} {convert_expression(righthalf)}"
                ln += 1
            elif re.match(r"print(.*)", line): # Print Statement
                arguments = line.split("print(")[1][:-1]
                assembly_code[linenum] = f"PRT {arguments}"
                ln += 1
            elif line == "END":
                assembly_code[linenum] = "PASS"
                ln += 1
            else:
                raise SyntaxError(f"Syntax Error occurred on line {linenum+1}") # Syntax Error
    except SyntaxError as err:
        print(err)
    return assembly_code

if __name__ in "__main__":
    with open("code.txt") as f:
        code = f.read().splitlines()
    print("\nPYTHON CODE\n")
    for ln, line in enumerate(code):
        print(ln, line)
    print("\nCOMPILED\n")
    for ln, line in compile_code(code).items():
        print(ln, line)

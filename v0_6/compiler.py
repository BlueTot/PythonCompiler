import re
from convert_expressions import OPERATIONS, convert_expression

DTV1 = "__temp__"
DTV2 = "__temp2__"

INDENT_SIZE = 4

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
        if line[0] == "B" and "break" not in line:
            line = f"{line.split(' ')[0]} {int(line.split(' ')[1]) + start_line}"
        output[ln+start_line] = line
    return output

def extend_code(assembly_code, new_code, start_line):
    for k, v in shift_pointers(new_code, start_line).items():
        assembly_code[k] = v
    return assembly_code

def compile_rpn(rpn, temp):
    assembly_code = {}
    linenum = 0
    stack = []

    for token in rpn:
        if token in OPERATIONS: # operator
            operand2 = stack.pop()
            operand1 = stack.pop()
            match token:
                case "+": assembly_code[linenum] = f"ADD {temp} {operand1} {operand2}"
                case "-": assembly_code[linenum] = f"SUB {temp} {operand1} {operand2}"
                case "*": assembly_code[linenum] = f"MTP {temp} {operand1} {operand2}" 
                case "/": assembly_code[linenum] = f"DIV {temp} {operand1} {operand2}"
                case "^": assembly_code[linenum] = f"EXP {temp} {operand1} {operand2}"
                case "%": assembly_code[linenum] = f"MOD {temp} {operand1} {operand2}"
            stack.append(temp)
            linenum += 1
        else:
            if token.isdigit(): # number
                stack.append(token)
            else: # string or variable
                stack.append(token)
    
    return assembly_code

def compile_assignment(line):

    lefthalf, righthalf = line.split("=")
    rpn = convert_expression(righthalf).split(",")
    assembly_code = {}

    if len(rpn) == 1:
        assembly_code[0] = f"STR {lefthalf} {rpn[0]}"
        return assembly_code
    
    assembly_code = compile_rpn(rpn, DTV1)
    linenum = len(assembly_code)
    assembly_code[linenum] = f"STR {lefthalf} {DTV1}"

    return assembly_code

def compile_comparison(line):

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
                assembly_code = compile_rpn(rrpn, DTV1)
                linenum = len(assembly_code)
                assembly_code[linenum] = f"CMP {lrpn[0]} {DTV1}"

            elif len(lrpn) > 1 and len(rrpn) == 1: # left half requires compiling
               assembly_code = compile_rpn(lrpn, DTV1)
               linenum = len(assembly_code)
               assembly_code[linenum] = f"CMP {DTV1} {rrpn[0]}"
               
            else: # both sides need compiling
                assembly_code = compile_rpn(lrpn, DTV1)
                linenum = len(assembly_code)
                for k, v in shift_pointers(compile_rpn(rrpn, DTV2), linenum).items():
                    assembly_code[k] = v
                assembly_code[len(assembly_code)] = f"CMP {DTV1} {DTV2}"

            linenum = len(assembly_code)
            assembly_code[linenum] = f"{keyword} {linenum+2}" # Add branch instruction
            return assembly_code

def compile_code(code):

    '''Handle cases where there is no line after if statement or no else statement'''
    if "END" not in code and code: # If there is no ending statement in the current code
        code += [f"{num_indents(code, 0)*' '*INDENT_SIZE}END"] # Add the ending statement

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
                assembly_code = extend_code(assembly_code, compile_comparison(line), linenum)
                
                '''Add else branch instruction pointer'''
                linenum = len(assembly_code)
                end_of_curr_if_block = find_end_of_curr_if_block(code, ln+1, num_indents(code, ln)) # Find when the current if block ends
                assembly_code[linenum] = f"BAL ptr" # Add else instruction
                else_instruction = linenum
                
                '''Compile code inside the if statement'''
                linenum = len(assembly_code)
                end_of_if_statement = find_end_of_if_statement(code, ln+1, num_indents(code, ln)) # Find when the if statement ends
                assembly_code = extend_code(assembly_code, compile_code(code[ln+1:end_of_curr_if_block]), linenum) # Compile whatever code there is inside the if block
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
                end_of_for_loop = find_end_of_if_statement(code,ln+1, indents := num_indents(code, ln)) # Find when the for loop ends
                loop_code = [" "*INDENT_SIZE*indents + initialisation, f"{' '*INDENT_SIZE*indents}while {condition}:"] + code[ln+1:end_of_for_loop] + [f"{' '*INDENT_SIZE*(indents+1)}{increment}"] # convert for loop into a while loop
                assembly_code = extend_code(assembly_code, compile_code(loop_code), linenum)
                ln = end_of_for_loop
                break_ptrs[ln] = len(assembly_code)
            
            elif re.match(r"else:", line): # Else statement
                linenum = len(assembly_code)
                end_of_if_statement = find_end_of_if_statement(code, ln+1, num_indents(code, ln)) # Find when the if statement ends
                assembly_code = extend_code(assembly_code, compile_code(code[ln+1:end_of_if_statement]), linenum) # Compile whatever code there is inside the if block
                ln = end_of_if_statement
            
            elif re.match(r"break", line): # Break statement
                assembly_code[linenum] = "BAL break"
                ln += 1

            elif re.match(r".*=.*", line): # Assignment
                assembly_code = extend_code(assembly_code, compile_assignment(line), linenum) # Compile assignment RPN into multiple statements
                ln += 1
            
            elif re.match(r".*\+\+", line): # Increment operator
                variable = line.replace("++", "")
                assembly_code = extend_code(assembly_code, compile_code([f"{variable} = {variable} + 1"]), linenum) # Convert increment operator into compilable syntax
                ln += 1

            elif re.match(r"print(.*)", line): # Print Statement
                arguments = line.split("print(")[1][:-1]
                assembly_code[linenum] = f"PRT {arguments}"
                ln += 1

            elif line == "END": # Pass statement used to make compiling process easier
                assembly_code[linenum] = "PASS"
                ln += 1

            else:
                raise SyntaxError(f"Syntax Error occurred on line {linenum+1}") # Syntax Error
            
    except SyntaxError as err:
        print(err)
    return assembly_code
import re
from sys import argv
from convert_expressions import OPERATIONS, convert_expression, is_number, is_value

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
        assembly_code.pop(len(assembly_code)-1)
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
                        new_code2, expression = Compiler.__compile_argument(expression, used_reg=index if not index.isdigit() else None)
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

if __name__ in "__main__":
    if len(argv) != 3:
        print("How to compile code: python compiler.py code.txt assembly.txt")
    else:
        source, dest = argv[1], argv[2]
        with open(source, "r") as f:
            code = f.read().splitlines()
        assembly = Compiler.compile_code(code)
        with open(dest, "w") as f:
            for line in assembly.values():
                f.write(line+"\n")
        print(f"Code compiled successfully into {dest}")

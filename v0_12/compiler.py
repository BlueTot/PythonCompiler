import re
from sys import argv
from convert_expressions import OPERATIONS, convert_expression, is_number, is_value, is_variable

VERSION = "v0.12"

class CompliationError(Exception):
    pass

class Compiler:

    INDENT_SIZE = 4
    VARIABLE_RANGE = (32, 191)
    ARRAY_RANGE = (192, 255)

    def __init__(self):
        self.__variables = {} # key: variable name, value: address
        self.__arrays = {} # key: array name, value: (address, size of array)
        self.__registers = {"r0": False, "r1": False, "r2": False, "r3": False, "r4": False, "r5": False, "r6": False, "r7": False}
  
    def __next_variable_address(self):
        return max(list(self.__variables.values())) + 1 if self.__variables else self.VARIABLE_RANGE[0]

    def __next_array_address(self):
        if not self.__arrays:
            return self.ARRAY_RANGE[0]
        name, max_address = max(list(self.__arrays.values()), key= lambda x: x[0])
        return self.__arrays[name][1] + max_address + 1
    
    def __next_available_register(self):
        for k, v in self.__registers.items():
            if not v:
                return k
            
    def __block_register(self, reg):
        self.__registers[reg] = True
    
    def __free_register(self, reg):
        self.__registers[reg] = False

    def __num_indents(self, code, ln):
        for idx, char in enumerate(code[ln]):
            if char != " ":
                if idx % self.INDENT_SIZE != 0:
                    raise SyntaxError(f"INDENT ERROR occurred on line {ln}")
                return idx // self.INDENT_SIZE

    def __find_end_of_if_statement(self, code, start_line, indents):
        for ln in range(start_line, len(code)):
            if self.__num_indents(code, ln) <= indents and not re.match(r" *else:", code[ln]) and not re.match(r" *elif.*:", code[ln]):
                return ln

    def __find_end_of_curr_if_block(self, code, start_line, indents):
        for ln in range(start_line, len(code)):
            if self.__num_indents(code, ln) == indents:
                return ln

    def find_else_block(self, code, start_line, indents):
        for ln in range(start_line, len(code)):
            if self.__num_indents(code, ln) == indents and re.match(r" *else:", code[ln]):
                return ln

    def __shift_pointers(self, assembly_code, start_line, split_point=None, only_pointers=False):
        output = {}
        for ln, line in assembly_code.items():
            if line[0] == "B" and "break" not in line:
                ptr = int(line.split(' ')[1])
                if split_point is None or (split_point is not None and ptr > split_point):
                    line = f"{line.split(' ')[0]} {ptr + start_line}"
            output[ln if only_pointers else ln+start_line] = line
        return output

    def __extend_code(self, assembly_code, new_code, start_line):
        for k, v in self.__shift_pointers(new_code, start_line).items():
            assembly_code[k] = v
        return assembly_code

    def __find_pointers_to(self, assembly_code, ptr): # Function to find pointers to a given line
        for ln, line in assembly_code.items():
            if line[0] == "B" and int(line.split(" ")[1]) == ptr:
                yield ln

    def __next_non_pass_line(self, assembly_code, linenum): # Function to find next non-pass line after given line number
        for ln in range(linenum, len(assembly_code)):
            if assembly_code[ln] != "PASS":
                return ln

    def __extract_section(self, assembly_code, start, end): # Function to extract code between inclusive start and end bounds
        new_code = {}
        for ln, line in assembly_code.items():
            if start <= ln <= end:
                new_code[ln] = line
        return new_code

    def __compile_rpn(self, rpn):

        assembly_code = {}
        stack = []

        for token in rpn: # Loop through all tokens in RPN list
            if token in OPERATIONS: # Operator found
                register = self.__next_available_register()
                self.__block_register(register)
                operand2 = stack.pop()
                operand1 = stack.pop()
                if token == "~": # array index operation:
                    if is_number(operand2): # Index is an immediate value
                        assembly_code[len(assembly_code)] = f"MOV {register} #{self.__arrays[operand1][0] + int(operand2)}"
                    else:
                        code, index_reg = self.__compile_variable_load(operand2)
                        assembly_code = self.__extend_code(assembly_code, code, len(assembly_code))
                        addrregname = self.__next_available_register()
                        assembly_code[len(assembly_code)] = f"ADD {addrregname} #{self.__arrays[operand1][0]} {index_reg}"
                        assembly_code[len(assembly_code)] = f"LDR {register} {addrregname}"
                    operand1 = register
                else:
                    if is_variable(operand1): # operand 1 is a variable
                        extcode, operand1 = self.__compile_variable_load(operand1)
                        assembly_code = self.__extend_code(assembly_code, extcode, len(assembly_code))
                    if is_variable(operand2): # operand 2 is a variable  
                        extcode, operand2 = self.__compile_variable_load(operand2)
                        assembly_code = self.__extend_code(assembly_code, extcode, len(assembly_code))
                    match token:
                        case "+": assembly_code[len(assembly_code)] = f"ADD {register} {operand1} {operand2}"
                        case "-": assembly_code[len(assembly_code)] = f"SUB {register} {operand1} {operand2}"
                        case "*": assembly_code[len(assembly_code)] = f"MTP {register} {operand1} {operand2}" 
                        case "/": assembly_code[len(assembly_code)] = f"DIV {register} {operand1} {operand2}"
                        case "^": assembly_code[len(assembly_code)] = f"EXP {register} {operand1} {operand2}"
                        case "%": assembly_code[len(assembly_code)] = f"MOD {register} {operand1} {operand2}"
                        case "\\": assembly_code[len(assembly_code)] = f"FDV {register} {operand1} {operand2}"
                        case "~": assembly_code[len(assembly_code)] = f"AGT {register} {operand1} {operand2}"
                stack.append(register)
                if operand1 in self.__registers:
                    self.__free_register(operand1) # Free up register if used as operand
                if operand2 in self.__registers:
                    self.__free_register(operand2) # Free up register if used as operand
            else: # Operand found
                if token.isdigit(): # number
                    stack.append(f"#{token}")
                else: # string or variable
                    stack.append(token)
        
        return assembly_code, stack[-1] # Return assembly code and the register where output is stored at

    def __compile_argument(self, expression): # Compile argument
        rpn = convert_expression(expression).split(",")
        if len(rpn) == 1:
            return self.__compile_variable_load(rpn[0])
        return self.__compile_rpn(rpn)
    
    def __compile_variable_load(self, value):
        assembly_code = {}
        if value not in self.__variables: # Operand not found in existing variables
            raise CompliationError("Variable does not exist")
        nextreg = self.__next_available_register()
        assembly_code[0] = f"LDR {nextreg} {self.__variables[value]}"
        self.__block_register(nextreg)
        return assembly_code, nextreg
    
    def __compile_variable_store(self, var, value):

        assembly_code = {}
            
        if is_number(value): # Operand is an immediate value

            nextreg = self.__next_available_register()
            assembly_code[0] = f"MOV {nextreg} {'#' if is_number(value) else ''}{value}" # move immediate value into register
            self.__block_register(nextreg)
        
        elif re.match(r"r\d+", value): # Operand is a register
            
            nextreg = value

        else: # Operand is a variable name
            
            code, nextreg = self.__compile_variable_load(value)
            assembly_code = self.__extend_code(assembly_code, code, len(assembly_code))

        if var in self.__variables: # Variable that is being saved to already exists
            assembly_code[len(assembly_code)] = f"STR {nextreg} {self.__variables[var]}"
        else:       
            nextaddr = self.__next_variable_address()
            assembly_code[len(assembly_code)] = f"STR {nextreg} {nextaddr}" # store value in register into next available address
            self.__variables[var] = nextaddr
        self.__free_register(nextreg)

        return assembly_code

    def __compile_assignment(self, line): # Compile Assignment operations

        lefthalf, righthalf = line.split("=") # Split assignment into two halves
        rpn = convert_expression(righthalf).split(",") # Convert the right hand side into RPN
        assembly_code = {}

        if len(rpn) == 1: # If only one operand
            assembly_code = self.__extend_code(assembly_code, self.__compile_variable_store(lefthalf, rpn[0]), len(assembly_code))
        else: # Multiple operands
            assembly_code, lastreg = self.__compile_rpn(rpn) # Compile RPN
            assembly_code = self.__extend_code(assembly_code, self.__compile_variable_store(lefthalf, lastreg), len(assembly_code))
            self.__free_register(lastreg)

        return assembly_code

    def __compile_comparison(self, line): # Compile comparison operation

        assembly_code = {}

        condition = line.split("if")[1][:-1] # Get the if statement
        for cond, keyword in {"==": "BEQ", "!=": "BNE", ">": "BGT", "<": "BLT"}.items(): # Loop through all compare possibilities
            if re.match(r".*"+cond+r".*", condition): # Check if line matches

                lefthalf, righthalf = condition.split(cond) # Split condition into lefthalf and righthalf
                lrpn, rrpn = convert_expression(lefthalf).split(","), convert_expression(righthalf).split(",")

                '''Compile rpn for LHS and RHS and add compare instruction'''
                if len(lrpn) == 1 and len(rrpn) == 1: # both do not require compiling
                    if is_number(lrpn[0]): # Immediate value
                        lhs = lrpn[0]
                    else: # Variable
                        extcode, lhs = self.__compile_variable_load(lrpn[0])
                        assembly_code = self.__extend_code(assembly_code, extcode, len(assembly_code))
                    if is_number(rrpn[0]): # Immediate value
                        rhs = rrpn[0]
                    else: # Variable
                        extcode, rhs = self.__compile_variable_load(rrpn[0])
                        assembly_code = self.__extend_code(assembly_code, extcode, len(assembly_code))
                    assembly_code[len(assembly_code)] = f"CMP {'#' if is_number(lrpn[0]) else ''}{lhs} {'#' if is_number(rrpn[0]) else ''}{rhs}"
                    if not is_number(lrpn[0]):
                        self.__free_register(lhs)
                    if not is_number(rrpn[0]):
                        self.__free_register(rhs)

                elif len(lrpn) == 1 and len(rrpn) > 1: # right half requires compiling
                    if is_number(lrpn[0]): # Immediate value
                        lhs = lrpn[0]
                    else: # Variable
                        extcode, lhs = self.__compile_variable_load(lrpn[0])
                        assembly_code = self.__extend_code(assembly_code, extcode, len(assembly_code))
                    extcode, lastreg = self.__compile_rpn(rrpn)
                    assembly_code = self.__extend_code(assembly_code, extcode, len(assembly_code))
                    assembly_code[len(assembly_code)] = f"CMP {'#' if is_number(lrpn[0]) else ''}{lhs} {lastreg}"
                    self.__free_register(lastreg)
                    if not is_number(lrpn[0]):
                        self.__free_register(lhs)

                elif len(lrpn) > 1 and len(rrpn) == 1: # left half requires compiling
                    if is_number(rrpn[0]): # Immediate value
                        rhs = rrpn[0]
                    else: # Variable
                        extcode, rhs = self.__compile_variable_load(rrpn[0])
                        assembly_code = self.__extend_code(assembly_code, extcode, len(assembly_code))
                    extcode, lastreg = self.__compile_rpn(lrpn)
                    assembly_code = self.__extend_code(assembly_code, extcode, len(assembly_code))
                    assembly_code[len(assembly_code)] = f"CMP {'#' if is_number(rrpn[0]) else ''}{rhs} {lastreg}"
                    self.__free_register(lastreg)
                    if not is_number(rrpn[0]):
                        self.__free_register(rhs)
                
                else: # both sides need compiling
                    assembly_code, lastreg = self.__compile_rpn(lrpn) # Compile LHS and store register with stored value
                    new_code, lastreg2 = self.__compile_rpn(rrpn) # Compile RHS whilst blocking out register that is being used
                    assembly_code = self.__extend_code(assembly_code, new_code, len(assembly_code)) # Extend the assembly code
                    assembly_code[len(assembly_code)] = f"CMP {lastreg} {lastreg2}" # Add the compare operation
                    self.__free_register(lastreg)
                    self.__free_register(lastreg2)

                linenum = len(assembly_code)
                assembly_code[linenum] = f"{keyword} {linenum+2}" # Add branch instruction
                return assembly_code

    def __remove_pass_statements(self, assembly_code): # Remove pass statements from compiled code
        ln = 0
        while ln < len(assembly_code) - 1:
            line = assembly_code[ln]
            if line == "PASS":
                next_line = self.__next_non_pass_line(assembly_code, ln)
                for loc in self.__find_pointers_to(assembly_code, ln):
                    assembly_code[loc].replace(str(ln), str(next_line))
                assembly_code = self.__extend_code(self.__shift_pointers(self.__extract_section(assembly_code, 0, ln), -1, split_point=ln, only_pointers=True), 
                                            self.__shift_pointers(self.__extract_section(assembly_code, ln+1, len(assembly_code)), -1, split_point=ln), 0)
                ln = 0
            ln += 1
        assembly_code[len(assembly_code)-1] = "HALT"
        return assembly_code

    def __compile_code(self, code): # Compile code function with pass statements

        '''Handle cases where there is no line after if statement or no else statement'''
        if "END" not in code and code: # If there is no ending statement in the current code
            code += [f"{self.__num_indents(code, 0)*' '*self.INDENT_SIZE}END"] # Add the ending statement

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
                    assembly_code = self.__extend_code(assembly_code, self.__compile_comparison(line), linenum)
                    
                    '''Add else branch instruction pointer'''
                    linenum = len(assembly_code)
                    end_of_curr_if_block = self.__find_end_of_curr_if_block(code, ln+1, self.__num_indents(code, ln)) # Find when the current if block ends
                    assembly_code[linenum] = f"BAL ptr" # Add else instruction
                    else_instruction = linenum
                    
                    '''Compile code inside the if statement'''
                    linenum = len(assembly_code)
                    end_of_if_statement = self.__find_end_of_if_statement(code, ln+1, self.__num_indents(code, ln)) # Find when the if statement ends
                    assembly_code = self.__extend_code(assembly_code, self.__compile_code(code[ln+1:end_of_curr_if_block]), linenum) # Compile whatever code there is inside the if block
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
                    end_of_for_loop = self.__find_end_of_if_statement(code,ln+1, indents := self.__num_indents(code, ln)) # Find when the for loop ends
                    loop_code = [" "*self.INDENT_SIZE*indents + initialisation, f"{' '*self.INDENT_SIZE*indents}while {condition}:"] + code[ln+1:end_of_for_loop] + [f"{' '*self.INDENT_SIZE*(indents+1)}{increment}"] # convert for loop into a while loop
                    assembly_code = self.__extend_code(assembly_code, self.__compile_code(loop_code), linenum)
                    ln = end_of_for_loop
                    break_ptrs[ln] = len(assembly_code)
                
                elif re.match(r"else:", line): # Else statement
                    linenum = len(assembly_code)
                    end_of_if_statement = self.__find_end_of_if_statement(code, ln+1, self.__num_indents(code, ln)) # Find when the if statement ends
                    assembly_code = self.__extend_code(assembly_code, self.__compile_code(code[ln+1:end_of_if_statement]), linenum) # Compile whatever code there is inside the if block
                    ln = end_of_if_statement
                
                elif re.match(r"break", line): # Break statement
                    assembly_code[linenum] = "BAL break"
                    ln += 1
                
                elif re.match(r".*=array(.*)", line): # Array declaration
                    name, size = line[:-1].split("=array(")
                    if not is_number(size):
                        raise CompliationError("Variable length arrays are not supported")
                    nextaddr = self.__next_array_address()
                    self.__arrays[name] = (nextaddr, size)
                    assembly_code = self.__extend_code(assembly_code, self.__compile_variable_store(f"__{name}__size__", size), len(assembly_code))
                    ln += 1
                
                elif re.match(r".*\[.*\]=.*", line): # Assignment to an array
                    __front, expression = line.split("]=")
                    array_name, index = __front.split("[")
                    if not is_value(index): # index is an expression
                        new_code1, index = self.__compile_argument(index)
                        assembly_code = self.__extend_code(assembly_code, new_code1, linenum)
                    elif not is_number(index): # index is a variable
                        extcode, index = self.__compile_variable_load(index)
                        assembly_code = self.__extend_code(assembly_code, extcode, len(assembly_code))
                    if not is_value(expression): # value is an expression
                        new_code2, expreg = self.__compile_argument(expression, used_reg=index if not index.isdigit() else None)
                        assembly_code = self.__extend_code(assembly_code, new_code2, len(assembly_code))
                    elif not is_number(expression): # value is a variable
                        extcode, expreg = self.__compile_variable_load(expression)
                        assembly_code = self.__extend_code(assembly_code, extcode, len(assembly_code))
                    else: # value is an immediate value
                        expreg = self.__next_available_register()
                        assembly_code[len(assembly_code)] = f"MOV {expreg} #{expression}"
                        self.__block_register(expreg)
                    addrreg = self.__next_available_register()
                    assembly_code[len(assembly_code)] = f"ADD {addrreg} #{self.__arrays[array_name][0]} {'#' if is_number(index) else ''}{index}"
                    assembly_code[len(assembly_code)] = f"STR {expreg} {addrreg}"
                    self.__free_register(expreg)
                    self.__free_register(addrreg)
                    ln += 1
                
                elif re.match(r".*\+=.*", line): # Fast Addition operator
                    variable, operand = line.split("+=")
                    assembly_code = self.__extend_code(assembly_code, self.__compile_code([f"{variable} = {variable} + ({operand})"]), linenum) # Convert fast addition operator into compilable syntax
                    ln += 1
                
                elif re.match(r".*-=.*", line): # Fast Subtraction operator
                    variable, operand = line.split("-=")
                    assembly_code = self.__extend_code(assembly_code, self.__compile_code([f"{variable} = {variable} - ({operand})"]), linenum) # Convert fast subtraction operator into compilable syntax
                    ln += 1
                
                elif re.match(r".*\*=.*", line): # Fast Multiplication operator
                    variable, operand = line.split("*=")
                    assembly_code = self.__extend_code(assembly_code, self.__compile_code([f"{variable} = {variable} * ({operand})"]), linenum) # Convert fast multiplication operator into compilable syntax
                    ln += 1
                
                elif re.match(r".*/=.*", line): # Fast Division operator
                    variable, operand = line.split("/=")
                    assembly_code = self.__extend_code(assembly_code, self.__compile_code([f"{variable} = {variable} / ({operand})"]), linenum) # Convert fast division operator into compilable syntax
                    ln += 1
                
                elif re.match(r".*^=.*", line): # Fast Exponentiation operator
                    variable, operand = line.split("^=")
                    assembly_code = self.__extend_code(assembly_code, self.__compile_code([f"{variable} = {variable} ^ ({operand})"]), linenum) # Convert fast exponentiation operator into compilable syntax
                    ln += 1
                
                elif re.match(r".*%=.*", line): # Fast Modulo operator
                    variable, operand = line.split("%=")
                    assembly_code = self.__extend_code(assembly_code, self.__compile_code([f"{variable} = {variable} % ({operand})"]), linenum) # Convert fast modulo operator into compilable syntax
                    ln += 1
                
                elif re.match(r".*\\=.*", line): # Fast Floor Division operator
                    variable, operand = line.split("\\=")
                    assembly_code = self.__extend_code(assembly_code, self.__compile_code([f"{variable} = {variable} \\ ({operand})"]), linenum) # Convert fast floor division operator into compilable syntax
                    ln += 1

                elif re.match(r".*=.*", line): # Assignment
                    assembly_code = self.__extend_code(assembly_code, self.__compile_assignment(line), linenum) # Compile assignment RPN into multiple statements
                    ln += 1
                
                elif re.match(r".*\+\+", line): # Increment operator
                    variable = line.replace("++", "")
                    assembly_code = self.__extend_code(assembly_code, self.__compile_code([f"{variable} = {variable} + 1"]), linenum) # Convert increment operator into compilable syntax
                    ln += 1
                
                elif re.match(r".*--", line): # Decrement operator
                    variable = line.replace("--", "")
                    assembly_code = self.__extend_code(assembly_code, self.__compile_code([f"{variable} = {variable} - 1"]), linenum) # Convert decrement operator into compilable syntax
                    ln += 1

                elif re.match(r"print(.*)", line): # Print Statement
                    argument = line.split("print(")[1][:-1]
                    if not is_number(argument):
                        new_code, argument = self.__compile_argument(argument)
                        assembly_code = self.__extend_code(assembly_code, new_code, len(assembly_code))
                    assembly_code[len(assembly_code)] = f"PRT {argument}"
                    ln += 1

                elif line == "END": # Pass statement used to make compiling process easier
                    assembly_code[linenum] = "PASS"
                    ln += 1

                else:
                    raise SyntaxError(f"Syntax Error occurred on line {linenum+1}") # Syntax Error
                
        except SyntaxError as err:
            print(err)
            
        return assembly_code

    def compile_code(self, code): # Compile code function without pass statements
        return self.__remove_pass_statements(self.__compile_code(code))

def main(source, dest): # Main function
    try:
        with open(source, "r") as f: # Read code file
            code = f.read().splitlines()
        compiler = Compiler()
        assembly = compiler.compile_code(code) # Compile the code
        with open(dest, "w") as f: # Write the assembly to output file
            for line in assembly.values():
                f.write(line+"\n")
            for _ in range(len(assembly), Compiler.ARRAY_RANGE[1]+1):
                f.write("\n")
        print(f"\033[92;1mCode compiled successfully into {dest}\033[0m")
    except FileNotFoundError as err: # Code file not found
        print(f"\033[91;1m{err}\033[0m")

if __name__ in "__main__":
    if argv[1] == "--version":
        print(f"\033[36;1mpcompile {VERSION}\033[0m")
    elif not argv[1] and not argv[2]: # No arguments passed:
        print("\033[91;1musage: pcompile <code file> [-o <output file>] \033[0m")
    elif not argv[2]: # Second argument not passed:
        main(argv[1], "assembly.txt")
    else: # Both arguments passed
        main(argv[1], argv[2])
        

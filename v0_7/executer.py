import re

NUMERICAL_INSTRUCTIONS = ("ADD", "SUB", "MTP", "DIV", "EXP", "MOD", "FDV")

def is_number(s):
    if s.isdigit(): # Integer
        return True
    elif re.match(r"\d+.\d+", s): # Float
        return True
    return False

def execute_assembly_code(assembly_code):
    VARIABLES = {}
    STATUS_REGISTER = (None, None, None, None) # Equal, Not Equal, Greater Than, Less Than
    ln = 0
    try:
        while ln < len(assembly_code):
            line = assembly_code[ln]
            if line == "PASS":
                ln += 1
                continue
            opcode, operand = line.split(" ")[0], line.split(" ")[1:]
            if opcode in NUMERICAL_INSTRUCTIONS: # Numerical instruction
                var, op1, op2 = operand
                num1, num2 = (float(op1) if is_number(op1) else VARIABLES[op1]), (float(op2) if is_number(op2) else VARIABLES[op2])
                match opcode:
                    case "ADD": VARIABLES[var] = num1 + num2
                    case "SUB": VARIABLES[var] = num1 - num2
                    case "MTP": VARIABLES[var] = num1 * num2
                    case "DIV": VARIABLES[var] = num1 / num2
                    case "EXP": VARIABLES[var] = num1 ** num2
                    case "MOD": VARIABLES[var] = num1 % num2
                    case "FDV": VARIABLES[var] = num1 // num2
                ln += 1
                if var == "__temp__": 
                    pass
            elif opcode == "STR": # Store instruction
                var, op = operand
                number = float(op) if is_number(op) else VARIABLES[op]
                VARIABLES[var] = number
                ln += 1
            elif opcode == "CMP": # Compare instruction
                lhs, rhs = operand
                num1, num2 = (float(lhs) if is_number(lhs) else VARIABLES[lhs]), (float(rhs) if is_number(rhs) else VARIABLES[rhs])
                STATUS_REGISTER = (num1 == num2, num1 != num2, num1 > num2, num1 < num2)
                ln += 1
            elif opcode[0] == "B": # Branch instruction
                address = float(operand[0])
                if opcode == "BAL":
                    ln = address
                elif opcode == "BEQ" and STATUS_REGISTER[0] or opcode == "BNE" and STATUS_REGISTER[1] or \
                    opcode == "BGT" and STATUS_REGISTER[2] or opcode == "BLT" and STATUS_REGISTER[3]:
                    ln = address
                else:
                    ln += 1
            elif opcode == "PRT": # Print instruction
                val = float(operand[0]) if is_number(operand[0]) else VARIABLES[operand[0]]
                print(val)
                ln += 1               
    except Exception as err:
        print(f"Error occurred on line {ln}: {err}")        
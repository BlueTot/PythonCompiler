from sys import argv
import re
from time import perf_counter

def is_number(s):
    if s[1:].isdigit() and s[0] == "#": # Integer
        return True
    elif re.match(r"\d+\.\d+", s[1:]) and s[0] == "#": # Float
        return True
    return False

NUMERICAL_INSTRUCTIONS = ("ADD", "SUB", "MTP", "DIV", "EXP", "MOD", "FDV")

def execute_assembly_code(assembly_code):
    VARIABLES = {}
    STATUS_REGISTER = (None, None, None, None) # Equal, Not Equal, Greater Than, Less Than
    ln = 0
    try:
        while True:
            line = assembly_code[ln]
            if line == "HALT":
                break
            opcode, operand = line.split(" ")[0], line.split(" ")[1:]
            if opcode in NUMERICAL_INSTRUCTIONS: # Numerical instruction
                var, op1, op2 = operand
                num1, num2 = (float(op1[1:]) if is_number(op1) else VARIABLES[op1]), (float(op2[1:]) if is_number(op2) else VARIABLES[op2])
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
                number = float(op[1:]) if is_number(op) else VARIABLES[op]
                VARIABLES[var] = number
                ln += 1
            elif opcode == "ARR": # Declare Array instruction
                name, length = operand
                length = int(length[1:]) if is_number(length) else VARIABLES[length]
                VARIABLES[name] = [None for _ in range(int(length))]
                ln += 1
            elif opcode == "AMV": # Set Item in Array instruction
                name, index, value = operand
                index = int(index[1:]) if is_number(index) else VARIABLES[index]
                value = float(value[1:]) if is_number(value) else VARIABLES[value]
                VARIABLES[name][int(index)] = value
                ln += 1
            elif opcode == "AGT": # Read Item in Array instruction
                register, name, index = operand
                index = int(index[1:]) if is_number(index) else VARIABLES[index]
                VARIABLES[register] = VARIABLES[name][int(index)]
                ln += 1
            elif opcode == "CMP": # Compare instruction
                lhs, rhs = operand
                num1, num2 = (float(lhs[1:]) if is_number(lhs) else VARIABLES[lhs]), (float(rhs[1:]) if is_number(rhs) else VARIABLES[rhs])
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

if __name__ in "__main__":
    if "--help" in argv: # Help argument
        print("\033[91;1mpexec syntax: pcompile <code file> <output>\033[0m")
    elif len(argv) != 2: # Not enough arguments
        print("\033[91;1mpexec: Incorrect number of arguments\033[0m")
    elif not argv[1]: # Blank arguments
        print("\033[91;1mpexec: Some arguments are blank\033[0m")
    else:
        try:
            with open(argv[1], "r") as f:
                data = f.read().splitlines()
            assembly = {}
            for i, line in enumerate(data):
                assembly[i] = line
            stime = perf_counter()
            execute_assembly_code(assembly)
            print(f"\033[92;1mExecution successful, took {perf_counter() - stime} seconds\033[0m")
        except FileNotFoundError as err: # Code file not found
            print(f"\033[91;1m{err}\033[0m")
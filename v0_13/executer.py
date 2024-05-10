from sys import argv
from time import perf_counter

def is_number(s):
    s = s.replace("#", "")
    if s.isdigit(): # Integer
        return True
    return False

NUMERICAL_INSTRUCTIONS = ("ADD", "SUB", "MTP", "DIV", "EXP", "MOD", "FDV")

def execute_assembly_code(memory):
    REGISTERS = {"r0": None, "r1": None, "r2": None, "r3": None, "r4": None, "r5": None, "r6": None, "r7": None}
    STATUS_REGISTER = (None, None, None, None) # Equal, Not Equal, Greater Than, Less Than
    ln = 0
    try:
        while True:
            line = memory[ln]
            # if ln == 15:
            #     print(memory)
            #     input()
            if line == "HALT":
                break
            opcode, operand = line.split(" ")[0], line.split(" ")[1:]
            if opcode in NUMERICAL_INSTRUCTIONS: # Numerical instruction
                var, op1, op2 = operand
                num1, num2 = (int(op1[1:]) if is_number(op1) else REGISTERS[op1]), (int(op2[1:]) if is_number(op2) else REGISTERS[op2])
                match opcode:
                    case "ADD": REGISTERS[var] = num1 + num2
                    case "SUB": REGISTERS[var] = num1 - num2
                    case "MTP": REGISTERS[var] = num1 * num2
                    case "DIV": REGISTERS[var] = num1 / num2
                    case "EXP": REGISTERS[var] = num1 ** num2
                    case "MOD": REGISTERS[var] = num1 % num2
                    case "FDV": REGISTERS[var] = num1 // num2
                ln += 1
            elif opcode == "LDR": # Load instruction
                reg, ref = operand
                ref = int(ref.replace("#", "")) if is_number(ref) else REGISTERS[ref]
                REGISTERS[reg] = memory[ref]
                ln += 1
            elif opcode == "STR": # Store instruction
                reg, ref = operand
                ref = int(ref.replace("#", "")) if is_number(ref) else REGISTERS[ref]
                memory[ref] = REGISTERS[reg]
                ln += 1
            elif opcode == "MOV": # Move instruction
                reg, op = operand
                op = int(op.replace("#", "")) if is_number(op) else REGISTERS[op]
                REGISTERS[reg] = op
                ln += 1
            elif opcode == "CMP": # Compare instruction
                lhs, rhs = operand
                num1, num2 = (int(lhs[1:]) if is_number(lhs) else REGISTERS[lhs]), (int(rhs[1:]) if is_number(rhs) else REGISTERS[rhs])
                STATUS_REGISTER = (num1 == num2, num1 != num2, num1 > num2, num1 < num2)
                ln += 1
            elif opcode[0] == "B": # Branch instruction
                address = int(operand[0])
                if opcode == "BAL":
                    ln = address
                elif opcode == "BEQ" and STATUS_REGISTER[0] or opcode == "BNE" and STATUS_REGISTER[1] or \
                    opcode == "BGT" and STATUS_REGISTER[2] or opcode == "BLT" and STATUS_REGISTER[3]:
                    ln = address
                else:
                    ln += 1
            elif opcode == "PRT": # Print instruction
                val = float(operand[0]) if is_number(operand[0]) else REGISTERS[operand[0]]
                print(val)
                ln += 1               
    except Exception as err:
        print(memory)
        print(f"Error occurred on line {ln}: {err}") 

if __name__ in "__main__":
    if "--version" in argv: # Version argument
        print(f"\033[36;1mpexec v0.13\033[0m")
    elif "--help" in argv: # Help argument
        print("\033[91;1mpexec syntax: pcompile <code file> <output>\033[0m")
    elif len(argv) != 2: # Not enough arguments
        print("\033[91;1mpexec: Incorrect number of arguments\033[0m")
    elif not argv[1]: # Blank arguments
        print("\033[91;1mpexec: Some arguments are blank\033[0m")
    else:
        try:
            with open(argv[1], "r") as f:
                memory = f.read().splitlines()
            stime = perf_counter()
            execute_assembly_code(memory)
            print(f"\033[92;1mExecution successful, took {perf_counter() - stime} seconds\033[0m")
        except FileNotFoundError as err: # Code file not found
            print(f"\033[91;1m{err}\033[0m")
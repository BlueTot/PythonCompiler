NUMERICAL_INSTRUCTIONS = ("ADD", "SUB", "MTP", "DIV", "EXP", "MOD")

def execute_assembly_code(assembly_code):
    VARIABLES = {}
    STATUS_REGISTER = (None, None, None, None) # Equal, Not Equal, Greater Than, Less Than
    ln = 0
    while ln < len(assembly_code):
        line = assembly_code[ln]
        if line == "PASS":
            ln += 1
            continue
        opcode, operand = line.split(" ")[0], line.split(" ")[1:]
        if opcode in NUMERICAL_INSTRUCTIONS: # Numerical instruction
            var, op1, op2 = operand
            num1, num2 = (int(op1) if op1.isdigit() else VARIABLES[op1]), (int(op2) if op2.isdigit() else VARIABLES[op2])
            match opcode:
                case "ADD": VARIABLES[var] = num1 + num2
                case "SUB": VARIABLES[var] = num1 - num2
                case "MTP": VARIABLES[var] = num1 * num2
                case "DIV": VARIABLES[var] = num1 / num2
                case "EXP": VARIABLES[var] = num1 ** num2
                case "MOD": VARIABLES[var] = num1 % num2
            ln += 1
            if var == "__temp__": 
                pass
        elif opcode == "STR": # Store instruction
            var, op = operand
            number = int(op) if op.isdigit() else VARIABLES[op]
            VARIABLES[var] = number
            ln += 1
        elif opcode == "CMP": # Compare instruction
            lhs, rhs = operand
            num1, num2 = (int(lhs) if lhs.isdigit() else VARIABLES[lhs]), (int(rhs) if rhs.isdigit() else VARIABLES[rhs])
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
            val = int(operand[0]) if operand[0].isdigit() else VARIABLES[operand[0]]
            print(val)
            ln += 1                       
                
from compiler import is_number

class PythonSimulation:

    NUMERICAL_INSTRUCTIONS = ("ADD", "SUB", "MTP", "DIV", "EXP", "MOD", "FDV")

    def __init__(self):
        self.__variables = {}
        self.__status_register = (None, None, None, None) # Equal, Not Equal, Greater Than, Less Than

    def __fetch_variable(self, var):
        if var.isdigit():
            return int(var)
        elif is_number(var):
            return float(var)
        else:
            return self.__variables[var]

    def execute_assembly_code(self, assembly_code):
        ln = 0
        try:
            while True:
                line = assembly_code[ln]
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
                    ln += 1               
        except Exception as err:
            print(f"Error occurred on line {ln}: {err}") 

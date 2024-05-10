import re

OPERATIONS = "+-*/%^\\~"

def is_variable(s):
    return not (is_number(s[1:]) and s[0] == "#") and not re.match(r"r\d", s)

def is_number(s):
    s = s.replace("#", "")
    if s.isdigit(): # Integer
        return True
    elif re.match(r"\d+\.\d+", s): # Float
        return True
    return False

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
    if operator == "~":
        return 4
    if operator == "^":
        return 3
    elif operator in "*/\\":
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
        elif char == "[": # open square backet denotes accessing item in array
            tokens.append(part := "~")
            tokens.append("(")
        elif char == "]": # close square bracket
            tokens.append(")")
        elif char.isdigit() or char == ".": # start of a number
            if i == len(s) - 1:
                tokens.append(Number(part := char))
            else:
                for j, c in enumerate(s[i+1:]):
                    if not c.isdigit() and c != ".":
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

def is_value(s):
    return len(convert_expression(s)) == 1
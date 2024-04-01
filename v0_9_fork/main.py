'''MAIN FILE'''

'''
========================================================================================================================================================================================================================================
Welcome to an unusual programming challenge, Python in Python. 

The goal of this program is to simulate running python code in python without using any existing functions to execute the code such as exec or eval.
Since computers cannot directly understand python code, it must be translated (also known as compiling) into a simpler language called Assembly that only executes one instruction at a time.
Your goal is to fix the program so python code (.py files) stored in the files dictionary can be first translated into Assembly (.exe files) and then simulated.
Some of the programs may also contain bugs and may not work properly, so it is your job to fix them!
Instructions on how to translate the code and simulalate the code are printed in the terminal when you run the program.

Challenges:

1. Currently there isn't an option to run the compiled code file. Can you add another if statement to run the code file when the user enters the keyword "run"?
    Hint: The command variable stores the command the user typed split by spaces, so the first keyword typed is stored at the first index. 
    Call the run_code() function to run the code inside the if statement.

2. In the render_debug_environment() function, print a blue arrow to the left of the line number to show which line is currently selected by the debugger.
    The blue arrow emoji can be found in the BLUE_ARROW_EMOJI constant at the top.

Before doing the next three challenges, take a look at forloops.py and arrays.py to familarise yourselves with the different syntax used in these code files:
    - For loop is written as:
        for (variable initialisation, condition to keep loop running, increment of variable):
    ... for example for (i = 0, i < 10, i++): loops through 0-9 via the variable i. i++ just means i = i + 1
    - Arrays are declared as:
         <arrayname> = array(size of array)
    ... e.g. numbers = array(10) creates an empty array of size 10. No items exist in the array when initialised.

3.
4.
5. 

Extension Challenges:




========================================================================================================================================================================================================================================
'''

from library import Compiler, PythonSimulation
import os

files = {

    # Demo code file to demonstrate for loops
    "forloops.py": """
for (i = 0, i < 10, i++):
    print(i)
""",

    # Demo code file to demonstrate arrays
    "arrays.py": """
N = 20
fib = array(N)
fib[0] = 0
fib[1] = 1
for (i = 2, i < N, i++):
    fib[i] = fib[i-1] + fib[i-2]
print(fib)
""",

    # Task 3 code file
    "task3.py": """""",
    
    # Task 4 code file
    "task4.py": """""",

    # Task 5 code file
    "task5.py": """""",

    "primes.py": """
N = 1000
prime = array(N + 1)
for (i = 0, i < N + 1, i++):
    prime[i] = 1
for (p = 2, p < N + 1, p++):
    if prime[p] == 1:
        for (j = p^2, j < N + 1, j += p):
            prime[j] = 0
for (p = 2, p < N + 1, p++):
    if prime[p] == 1:
        print(p)
"""

}

DEFAULT_COLOUR = "white"
BLUE_ARROW_EMOJI = "▶️"

class Colours: # Colour Rendering Class

    # Colours dictionary
    COLOURS = {'black': 30, 'red': 31, 'green': 32, 'yellow': 33,
            'blue': 34, 'magenta': 35, 'cyan': 36, 'white': 37}

    @staticmethod
    def colour_text(text, colour):
        # Function to print coloured text using ANSI terminal codes
        return f'\033[{Colours.COLOURS[colour]};1;1m{text}\033[0m'

def remove_blank_lines(code): # Function to remove blank lines from the code
    new_code = []
    for line in code:
        if line.replace(" ", ""):
            new_code.append(line)
    return new_code

def print_assembly(assembly):
    for ln, line in assembly.items():
        print(Colours.colour_text(f"{ln:^3}", "cyan") + f"{line}")

def print_header(): # Function to print the instructions on how to use the program
    print("\nCOMMANDS:")
    print("\t Viewing code: view <filename>")
    print("\t Compiling code: compile <filename>.py")
    print("\t Running code: run <filename>.exe")
    print("\t Debug code: debug <filename>.exe")
    print("\t Quit the program: exit\n")
    print(f"YOUR CURRENT FILES: {' '.join([k for k in files.keys()])}\n")

def view_code(filename):
    if filename not in files: # If file doesn't exist
        raise FileNotFoundError(f"File '{filename}' not found")
    elif ".py" in filename: # Python file
        print(files[filename])
    elif ".exe" in filename: # Executable file
        print_assembly(files[filename])

def compile_code(filename): # Function to compile code
    if filename not in files: # If file doesn't exist
        raise FileNotFoundError(f"File '{filename}' not found")
    elif ".py" not in filename: # If file is of the wrong type
        raise FileNotFoundError(f"Only .py files can be compiled")
    assembly = Compiler.compile_code(remove_blank_lines(files[filename].splitlines()))
    files[f"{filename.replace('.py', '')}.exe"] = assembly
    print(Colours.colour_text(f"{filename} compiled sucessfully into {filename.replace('.py', '')}.exe, here is the compiled code: \n", "green"))
    print_assembly(assembly)

def run_code(filename): # Function to run code
    if filename not in files: # If file doesn't exist
        raise FileNotFoundError(f"File '{filename}' not found")
    elif ".exe" not in filename: # If file is of the wrong type
        raise FileNotFoundError(f"Only .exe files can be simulated")
    simulation = PythonSimulation()
    for _ in simulation.execute_assembly_code(files[filename]):
        pass

def render_debug_environment(assembly, ln, variables, status_register, output): # Function to render debug environment after each pass of the debugger
    os.system("cls")
    print(Colours.colour_text(f"{'='*20}\nPYTHON DEBUGGER\n{'='*20}\n", "cyan"))
    print(Colours.colour_text("ASSEMBLY: \n", DEFAULT_COLOUR))
    for k, v in assembly.items():
        # ==> TASK 2: Print a blue arrow to the left of the line number to show which line is currently selected by the debugger.
        if ln == k:
            print(BLUE_ARROW_EMOJI, end='')
        else:
            print(f" ", end='')
        print('   ' + Colours.colour_text(f"{k:^3}", "cyan") + f"{v}")
    print(Colours.colour_text("\nVARIABLES: \n", DEFAULT_COLOUR))
    for var, contents in variables.items():
        print(f"{var}: {contents}")
    print(Colours.colour_text("\nSTATUS REGISTER: \n", DEFAULT_COLOUR))
    for tag, val in zip(("Equal", "Not Equal", "Greater Than", "Less Than"), status_register):
        print(f"{tag}: {val}")
    print(Colours.colour_text("\nOUTPUT: \n", DEFAULT_COLOUR))
    for line in output:
        print(line)
    print()

def debug_code(filename): # Function to debug code
    if filename not in files: # If file doesn't exist
        raise FileNotFoundError(f"File '{filename}' not found")
    elif ".exe" not in filename: # If file is of the wrong type
        raise FileNotFoundError(f"Only .exe files can be simulated")
    simulation = PythonSimulation()
    for ln, variables, status_register, output in simulation.execute_assembly_code(assembly := files[filename], debug=True):
        render_debug_environment(assembly, ln, variables, status_register, output)
        input(Colours.colour_text("Press enter to continue", "green"))

# Main part of code
while True:

    print_header() # Print the header

    try:

        command = input(Colours.colour_text(">>> ", "cyan")).lower().split(" ")

        # ==> TASK 1: Add another if statement to run the code file when the user enters the keyword "run"
        if command[0] == "exit": # Exit command
            break
        elif command[0] == "view": # View command
            view_code(command[1])
        elif command[0] == "compile": # Compile command
            compile_code(command[1])
        elif command[0] == "run": # Run command
            run_code(command[1])
        elif command[0] == "debug": # Debug command
            debug_code(command[1])
        else:
            print(Colours.colour_text("Command not found", "red"))

    except FileNotFoundError as err:
        print(Colours.colour_text(str(err), "red")) # Print any errors that occur
    
    print("\n"+"="*100)

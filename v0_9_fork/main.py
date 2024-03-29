from compiler import Compiler
from simulator import PythonSimulation

files = {

    "demo.py": """
for (i = 0, i < 10, i++):
    print(i)
""",

    "primes.py": """
N = 100
prime = array(101)
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

def remove_blank_lines(code):
    new_code = []
    for line in code:
        if line.replace(" ", ""):
            new_code.append(line)
    return new_code

def print_header():
    print("\nCOMMANDS:")
    print("\t Compiling code: compile <filename>.py")
    print("\t Running code: run <filename>.exe")
    print("\t Debugging code: debug <filename>.exe\n")
    print(f"YOUR CURRENT FILES: {' '.join([k for k in files.keys()])}\n")

def main():

    while True:

        print_header()

        try:

            command = input(">>> ").split(" ")

            if command[0] == "compile": # Compile command

                filename = command[1]
                if filename not in files:
                    raise FileNotFoundError(f"File '{filename}' not found")
                assembly = Compiler.compile_code(remove_blank_lines(files[filename].splitlines()))
                files[f"{filename.replace(".py", "")}.exe"] = assembly
                print(f"{filename} compiled sucessfully into {filename.replace(".py", "")}.exe, here is the compiled code: \n")
                for ln, line in assembly.items():
                    print(ln, line)

            elif command[0] == "run": # Run command

                filename = command[1]
                if filename not in files:
                    raise FileNotFoundError(f"File '{filename}' not found")
                simulation = PythonSimulation()
                simulation.execute_assembly_code(files[filename])

            elif command[0] == "debug": # Debug command
                pass
            
        except FileNotFoundError as err:
            print(err)

if __name__ in "__main__":
    main()
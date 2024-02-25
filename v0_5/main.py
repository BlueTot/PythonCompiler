from compiler import compile_code
from executer import execute_assembly_code

if __name__ in "__main__":
    with open("code.txt") as f:
        code = f.read().splitlines()
    print("\nPYTHON CODE\n")
    for ln, line in enumerate(code):
        print(ln, line)
    print("\nCOMPILED\n")
    for ln, line in (assembly_code := compile_code(code)).items():
        print(ln, line)
    print("\nOUTPUT\n")
    execute_assembly_code(assembly_code)

from compiler import compile_code
from executer import execute_assembly_code
from time import perf_counter
from convert_expressions import extract_components_from_infix

if __name__ in "__main__":
    with open("code.txt") as f:
        code = f.read().splitlines()
    print(extract_components_from_infix("list[0]"))
    print("\nPYTHON CODE\n")
    for ln, line in enumerate(code):
        print(ln, line)
    print("\nCOMPILED\n")
    stime = perf_counter()
    for ln, line in (assembly_code := compile_code(code)).items():
        print(ln, line)
    print(f"COMPILING TOOK {perf_counter() - stime} seconds")
    print("\nOUTPUT\n")
    stime = perf_counter()
    execute_assembly_code(assembly_code)
    print(f"CODE RAN FOR {perf_counter() - stime} seconds")

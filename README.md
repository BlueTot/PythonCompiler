# PythonCompiler

An experimental project that simulates a programming language similar to python by:
- Compiling python-like code syntax into a simplified assembly language code
- Then using an assembler to translate the assembly code into machine code
- Then executing the machine code on a verilog processor

*Verilog processor original code by Mr Gwilt (then modified)

## How To Use

Code for the compiler and verilog RTL microprocessor can be found in the `simulator` directory. </br>
To run the code, first manually change necessary paths (e.g. path of python) in the macros (`.bat`) </br>
Then, open the directory `main` and run the command `fakepython code.txt` in the terminal, which should open a `.vcd` file that shows the output of running the code on the microprocessor

## Features of the Programming Language

- Creation and usage of variables (only integers are supported)
- Arithmetic Operations (logical operations are NOT supported)
- Conditional Operations (if ... else)
- For loops and While loops
  - For loops follow a non-pythonic syntax: `for (starting statement, running condition, increment):`
- Arrays, defined via the syntax `<var> = array(<size>)`, creating an empty array which has to be populated manually
- All other features should follow a pythonic syntax, keep in mind that other python features such as list comprehension are not allowed.
- Functions do not exist, hence recursion also isn't possible

# PythonCompiler

An experimental project that simulates a programming language similar to python by:
- Compiling python-like code syntax into a simplified assembly language code
- Then using an assembler to translate the assembly code into machine code
- Then executing the machine code on a verilog processor

*Verilog processor original code by Mr Gwilt (then modified)

## Installation

- Type this into your terminal:
  ```
  git clone https://github.com/BlueTot/PythonCompiler
  ```
- Assuming that you are in the `main` directory of the cloned repo, run these commands to activate the simulator:
  ```
  python ../simulator/compiler.py code.txt assembly.txt
  python ../simulator/assembler.py assembly.txt memory.txt
  iverilog ../simulator/tb
- This should open a `.vcd` file that shows the output of running the code on the microprocessor
    - To check which register contains the output value, make sure to do `print(<var>)` at the end of your code and go to the bottom of `assembly.txt` and find which register contains the value.
- Or alternatively you can modify the `.bat` files given or make new commands on linux by editing `.bashrc`, so you can use the given command `fakepython`

## Dependencies

- This program requires both `python` and `iverilog` to be installed on your system.
- If you've installed the packages but the path cannot be found, try putting the paths for `python` and `iverilog` at the top of the PATH environment variable

## Features of the Programming Language

- Creation and usage of variables (only integers are supported)
- Arithmetic Operations (logical operations are NOT supported)
- Conditional Operations (if ... else)
- For loops and While loops
  - For loops follow a non-pythonic syntax: `for (starting statement, running condition, increment):`
- Arrays, defined via the syntax `<var> = array(<size>)`, creating an empty array which has to be populated manually
- All other features should follow a pythonic syntax, keep in mind that other python features such as list comprehension are not allowed.
- Functions do not exist, hence recursion also isn't possible
  - But while loops and recursion are equivalent (if you use a stack) so the language IS turing complete!

#CREDIT OF MR GWILT

from sys import argv
from os import path
from re import sub, search

def decode(asm_line):
    if asm_line:
        opcode,*operands = [x.strip() for x in asm_line.split()]
        return opcode, operands
    else:
        return "NOP",[]


def preprocessor(asmfile):
    with open(asmfile,'r') as fp:
        asm = sub(r';.*?\n',r'\n',fp.read()) # Strip comments
        asm = sub(r'(\w+)\s*:\s*\n',r'\1:',asm) # Move bare labels onto line below
        asm = sub(r'\n\s*\n',r'\n',asm) # Strip bare lines
        memory = [data.rstrip() for data in asm.splitlines()]

    labels = {}

    for address,data in enumerate(memory):
        labelpat = r'\A\s*(\w+)\s*:'
        if m := search(labelpat,data):
            labels[m.group(1)] = address
        memory[address] = sub(labelpat,'',memory[address])

    memory = [data.replace(","," ") for data in memory]
    memory = [data.strip() for data in memory]
    memory = [sub(r'\b0x([\dA-Fa-f]+)\b',lambda x: str(int(x.group(1),16)),data) for data in memory]

    for label,address in labels.items():
        pat = f'\\b{label}\\b'
        memory = [sub(pat,str(address),data) for data in memory]

    return memory,labels

def assembler(asmfile):

    memory, labels = preprocessor(asmfile)
    machine_code = []
    opcodes = {
        'LDR' : 0,
        'STR' : 1,
        'ADD' : 2,
        'SUB' : 3,
        'ORR' : 9,
        'AND' : 8,
        'EOR' : 10,
        'MOV' : 4,
        'MVN' : 11,
        'LSL' : 12,
        'LSR' : 13,
        'ASR' : 14,
        'CMP' : 5,
        'BAL' : 6,
        'BEQ' : 7,
        'BNE' : 7,
        'BGT' : 7,
        'BLT' : 7,
        'HALT': 15
        }

    for asm_line in memory:
        if "PRT" in asm_line:
            continue
        try:
            opcode, operands = decode(asm_line)
            inst = opcodes[opcode] << 12
            imm = 1 if operands and operands[-1].lower().startswith("r") else 0
            match opcode:
                case "CMP" :
                    inst |= (imm << 11)
                    inst |= (int(operands[0].lower().replace("r","").replace("#","")) << 3)
                    inst |= (int(operands[1].lower().replace("r","").replace("#","")) << 6)
                case "MOV" | "MVN" :
                    inst |= (imm << 11)
                    inst |= (int(operands[0].lower().replace("r","").replace("#","")))
                    inst |= (int(operands[1].lower().replace("r","").replace("#","")) << 6)
                case "BAL" | "BEQ" :
                    inst |= int(operands[0])
                case "BNE" :
                    inst |= (3 << 10)
                    inst |= int(operands[0])
                case "BGT" :
                    inst |= (1 << 10)
                    inst |= int(operands[0])
                case "BLT" :
                    inst |= (2 << 10)
                    inst |= int(operands[0])
                case "LDR" | "STR" :
                    inst |= (int(operands[0].lower().replace("r","").replace("#","")))
                    inst |= int(operands[1]) << 3
                case "ADD" | "SUB" | "AND" | "ORR" | "LSL" | "LSR" | "EOR" | "ASR" :
                    inst |= (imm << 11)
                    inst |= (int(operands[0].lower().replace("r","").replace("#","")))
                    inst |= (int(operands[1].lower().replace("r","").replace("#","")) << 3)
                    inst |= (int(operands[2].lower().replace("r","").replace("#","")) << 6)
                case "HALT" :
                    pass
            
            machine_code.append(inst)
        except SyntaxError as e:
            print(f"Syntax Error: {asm_line}",e)
            break

    return machine_code

def run():

    if "--version" in argv:
        print(f"\033[36;1mpasm v0.11\033[0m")
        quit()

    usage = f'\033[91;1mUsage: {argv[0]} <asm>\033[0m'

    if len(argv) != 2:
        print(usage)
        quit()

    asmfile = argv[1]

    if not(path.exists(asmfile) and path.isfile(asmfile)):
        print(usage)
        quit()

    machine_code = assembler(asmfile)

    with open("memory.txt","w") as f:
        count = 0
        for instruction in machine_code:
            f.write(f"{instruction:04X} ")
            count += 1
        while count < 256:
            f.write("0 ")
            count += 1
        f.write("\n")
    
    print(f"\033[92;1mAssembly code assembled successfully into memory.txt\033[0m")

run()

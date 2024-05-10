module alu (reg_a_data, reg_b_data, immediate, opcode, addressing_mode, result, cmp_result);

/////////////////////////////////////////
// Inputs and Outputs
/////////////////////////////////////////
input [31:0] reg_a_data, reg_b_data;
input [3:0] opcode;
input addressing_mode;
input [20:0] immediate;

output [31:0] result;
output [3:0] cmp_result;

/////////////////////////////////////////
// Wires
/////////////////////////////////////////
wire [31:0] op1, op2;
wire [31:0] result_add, result_sub, result_and, result_eor, result_orr, result_lsl, result_lsr;
reg [31:0] result;
wire result_gt, result_lt, result_eq, result_ne;

/////////////////////////////////////////
// Registers
/////////////////////////////////////////
// None

/////////////////////////////////////////
// Local Parameters
/////////////////////////////////////////
localparam
    MOV = 4'b0100,
    MVN = 4'b1011, 
    AND = 4'b1000,
    ORR = 4'b1001,
    EOR = 4'b1010,
    LSL = 4'b1100,
    LSR = 4'b1101,
    ADD = 4'b0010,
    SUB = 4'b0011,
    LDR = 4'b0000,
    STR = 4'b0001;

/////////////////////////////////////////
// Logic for Module
/////////////////////////////////////////

assign op1 = reg_a_data;
assign op2 = addressing_mode ? reg_b_data : {20'b0, immediate};

always @(*)
    case (opcode)
        ADD: result = result_add;
        SUB: result = result_sub;
        AND: result = result_and;
        ORR: result = result_orr;
        EOR: result = result_eor;
        LSL: result = result_lsl;
        LSR: result = result_lsr;
        MOV: result = op2;
        MVN: result = ~op2;
        LDR: result = op2;
        STR: result = op2;
        default: result = 32'bx;
    endcase

assign result_add = op1 + op2;
assign result_sub = op1 - op2;
assign result_and = op1 & op2;
assign result_orr = op1 | op2;
assign result_eor = op1 ^ op2;
assign result_lsl = op1 << op2;
assign result_lsr = op1 >> op2;

// Compare results
assign result_gt = op1 > op2;
assign result_lt = op1 < op2;
assign result_ne = result_gt || result_lt;
assign result_eq = !result_ne;
assign cmp_result = {result_gt, result_lt, result_ne, result_eq};

endmodule

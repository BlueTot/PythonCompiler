module alu (reg_a_data, reg_b_data, immediate, opcode, addressing_mode, result, cmp_result);

/////////////////////////////////////////
// Inputs and Outputs
/////////////////////////////////////////
input [31:0] reg_a_data, reg_b_data;
input [4:0] opcode;
input addressing_mode;
input [19:0] immediate;

output [31:0] result;
output [3:0] cmp_result;

/////////////////////////////////////////
// Wires
/////////////////////////////////////////
wire [31:0] op1, op2;
wire [31:0] result_add, result_sub, result_and, result_eor, result_orr, result_lsl, result_lsr, result_mul;
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
    MOV = 5'b00100,
    MVN = 5'b1011, 
    AND = 5'b01000,
    ORR = 5'b01001,
    EOR = 5'b01010,
    LSL = 5'b01100,
    LSR = 5'b01101,
    ADD = 5'b00010,
    SUB = 5'b00011,
    LDR = 5'b00000,
    STR = 5'b00001,
    MUL = 5'b10000;

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
        MUL: result = result_mul;
        default: result = 32'bx;
    endcase

assign result_add = op1 + op2;
assign result_sub = op1 - op2;
assign result_and = op1 & op2;
assign result_orr = op1 | op2;
assign result_eor = op1 ^ op2;
assign result_lsl = op1 << op2;
assign result_lsr = op1 >> op2;
assign result_mul = op1 * op2;

// Compare results
assign result_gt = op1 > op2;
assign result_lt = op1 < op2;
assign result_ne = result_gt || result_lt;
assign result_eq = !result_ne;
assign cmp_result = {result_gt, result_lt, result_ne, result_eq};

endmodule

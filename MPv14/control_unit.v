module control_unit (nreset, clk, ram_read, ram_write, ram_address, instruction_data, ra, rb, rc, reg_write, load_e, immediate_e, opcode_e, addressing_mode_e, cmp_result, result_d);

/////////////////////////////////////////
// Inputs and Outputs
/////////////////////////////////////////
input nreset, clk;

output load_e, addressing_mode_e;
output [19:0] immediate_e;
output [4:0] opcode_e;
input [31:0] result_d;
input [3:0] cmp_result;
output ram_read, ram_write, reg_write;
output [22:0] ram_address;
output [2:0] ra, rb, rc;
input [31:0] instruction_data;

/////////////////////////////////////////
// Local Parameters
/////////////////////////////////////////
localparam 
    FETCH  = 2'b00,
    BUBBLE = 2'b01,
    HALTED = 2'b10;

localparam 
    MOV = 5'b00100,
    MVN = 5'b01011, 
    BAL = 5'b00110,
    BCOND = 5'b00111,
    CMP = 5'b00101,
    AND = 5'b01000,
    ORR = 5'b01001,
    EOR = 5'b01010,
    LSL = 5'b01100,
    LSR = 5'b01101,
    ADD = 5'b00010,
    SUB = 5'b00011,
    STR  = 5'b00001,
    LDR  = 5'b00000,
    HALT = 5'b01111,
    MUL = 5'b10000;

/////////////////////////////////////////
// Wires
/////////////////////////////////////////
wire alu_op_d;
wire fetch;
wire execute_cmp;
wire [4:0] opcode_d;
reg flush;

// Program Counter Logic
reg [22:0] next_pc_f;
wire [22:0] inc_pc_f;

// State logic
reg [1:0] next_state;

/////////////////////////////////////////
// Registers
/////////////////////////////////////////
reg [3:0] status; // Status Register
reg [31:0] cir_d; // Current Instruction Register in decode
reg [31:0] cir_e; // Current Instruction Register in execute
reg [31:0] result_e;
reg [22:0] pc_f; // Program Counter
reg [1:0] state; // Halted. Fetch, Bubble
reg alu_op_e;
reg execute_store_e, execute_load_e, do_halt_e, decode, execute;

/////////////////////////////////////////
// Logic for Module
/////////////////////////////////////////

// Control for the ALU
assign opcode_d = cir_d[31:27];
assign opcode_e = cir_e[31:27];
assign addressing_mode_e = cir_e[26];
assign immediate_e = cir_e[25:6];
assign load_e = execute_load_e;
assign alu_op_d = (
        (opcode_d == MOV) || 
        (opcode_d == MVN) || 
        (opcode_d == AND) || 
        (opcode_d == ORR) || 
        (opcode_d == EOR) || 
        (opcode_d == LSL) || 
        (opcode_d == LSR) || 
        (opcode_d == ADD) || 
        (opcode_d == SUB) ||
        (opcode_d == MUL));

// Control for the RAM
assign ram_read = fetch || (execute && execute_load_e);
assign ram_write = execute && execute_store_e;
assign reg_write = execute && (execute_load_e || alu_op_e);


// Control for the Register File
assign ra = execute_store_e ? cir_e[2:0] : cir_e[5:3]; // Store instruction or ALU op
assign rb = cir_e[8:6];
assign rc = cir_e[2:0]; // Write port

// Address Mux
// assign ram_address = fetch ? pc_f : cir_e[26:3];
assign ram_address = fetch ? pc_f : (addressing_mode_e ? result_e[22:0] : cir_e[25:3]);

// Decoder logic
always @(posedge clk or negedge nreset)
    if (!nreset) begin
        execute_store_e <= 1'b0;
        execute_load_e <= 1'b0;
        do_halt_e <= 1'b0;
        alu_op_e <= 1'b0;
    end
    else if (decode) begin
        execute_store_e <= (opcode_d == STR);
        execute_load_e <= (opcode_d == LDR);
        do_halt_e <= (opcode_d == HALT);
        alu_op_e <= alu_op_d;
    end

// Program Counter Logic
assign inc_pc_f = pc_f + 23'd1;

always @(*)
    if (execute && (opcode_e == BAL)) begin // Branch Always
        next_pc_f = cir_e[22:0];
        flush = 1'b1;
    end else if (execute && (opcode_e == BCOND))
        // More to do here
        if ((cir_e[26:25] == 2'b00) && status[0]) begin
            next_pc_f = cir_e[22:0];
            flush = 1'b1;
        end else if ((cir_e[26:25] == 2'b11) && status[1]) begin
            next_pc_f = cir_e[22:0];
            flush = 1'b1;
        end else if ((cir_e[26:25] == 2'b01) && status[3]) begin
            next_pc_f = cir_e[22:0];
            flush = 1'b1;
        end else if ((cir_e[26:25] == 2'b10) && status[2]) begin
            next_pc_f = cir_e[22:0];
            flush = 1'b1;
        end else begin
            next_pc_f = inc_pc_f;
            flush = 1'b0;
        end
    else begin
        next_pc_f = inc_pc_f;
        flush = 1'b0;
    end

always @(posedge clk or negedge nreset)
    if (!nreset)
        pc_f <= 23'd0;
    else if (fetch)
        pc_f <= next_pc_f;

// cir_d Logic
assign fetch = (state == FETCH) ? 1'b1 : 1'b0;
always @(posedge clk)
    if (fetch) begin
        cir_d <= instruction_data;
    end

always @(posedge clk)
    if (decode) begin
        cir_e <= cir_d;
        result_e <= result_d;
    end

always @(posedge clk or negedge nreset)
    if (!nreset) begin
        decode <= 1'b0;
        execute <= 1'b0;
    end 
    else begin
        decode <= fetch && !flush && !do_halt_e;
        execute <= decode && !flush && !do_halt_e;
    end

// State Logic
always @(posedge clk or negedge nreset)
    if (!nreset)
        state <= BUBBLE;
    else
        state <= next_state;

always @(*)
    if (do_halt_e || (state == HALTED))
        next_state = HALTED;
    else if (!flush && decode && ((opcode_d == LDR) || (opcode_d == STR)))
        next_state = BUBBLE;
    else
        next_state = FETCH;

// Status Register Logic
assign execute_cmp = execute && (opcode_e == CMP);
always @(posedge clk or negedge nreset)
    if (!nreset)
        status <= 4'b0000;
    else if (execute_cmp)
        status <= cmp_result;

endmodule

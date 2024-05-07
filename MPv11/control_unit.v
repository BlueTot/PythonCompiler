module control_unit (nreset, clk, ram_read, ram_write, ram_address, instruction_data, ra, rb, rc, reg_write, load_e, immediate_e, opcode_e, addressing_mode_e, cmp_result);

/////////////////////////////////////////
// Inputs and Outputs
/////////////////////////////////////////
input nreset, clk;

output load_e, addressing_mode_e;
output [4:0] immediate_e;
output [3:0] opcode_e;
input [3:0] cmp_result;
output ram_read, ram_write, reg_write;
output [7:0] ram_address;
output [2:0] ra, rb, rc;
input [15:0] instruction_data;

/////////////////////////////////////////
// Local Parameters
/////////////////////////////////////////
localparam 
    FETCH  = 2'b00,
    BUBBLE = 2'b01,
    HALTED = 2'b10;

localparam 
    MOV = 4'b0100,
    MVN = 4'b1011, 
    BAL = 4'b0110,
    BCOND = 4'b0111,
    CMP = 4'b0101,
    AND = 4'b1000,
    ORR = 4'b1001,
    EOR = 4'b1010,
    LSL = 4'b1100,
    LSR = 4'b1101,
    ADD = 4'b0010,
    SUB = 4'b0011,
    STR  = 4'b0001,
    LDR  = 4'b0000,
    HALT = 4'b1111;

/////////////////////////////////////////
// Wires
/////////////////////////////////////////
wire alu_op_d;
wire fetch;
wire execute_cmp;
wire [3:0] opcode_d;
reg flush;

// Program Counter Logic
reg [7:0] next_pc_f;
wire [7:0] inc_pc_f;

// State logic
reg [1:0] next_state;

/////////////////////////////////////////
// Registers
/////////////////////////////////////////
reg [3:0] status; // Status Register
reg [15:0] cir_d; // Current Instruction Register in decode
reg [15:0] cir_e; // Current Instruction Register in execute
reg [7:0] pc_f; // Program Counter
reg [1:0] state; // Halted. Fetch, Bubble
reg alu_op_e;
reg execute_store_e, execute_load_e, do_halt_e, decode, execute;

/////////////////////////////////////////
// Logic for Module
/////////////////////////////////////////

// Control for the ALU
assign opcode_d = cir_d[15:12];
assign opcode_e = cir_e[15:12];
assign addressing_mode_e = cir_e[11];
assign immediate_e = cir_e[10:6];
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
        (opcode_d == SUB));

// Control for the RAM
assign ram_read = fetch || (execute && execute_load_e);
assign ram_write = execute && execute_store_e;
assign reg_write = execute && (execute_load_e || alu_op_e);


// Control for the Register File
assign ra = execute_store_e ? cir_e[2:0] : cir_e[5:3]; // Store instruction or ALU op
assign rb = cir_e[8:6];
assign rc = cir_e[2:0]; // Write port

// Address Mux
assign ram_address = fetch ? pc_f : cir_e[10:3];

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
assign inc_pc_f = pc_f + 8'd1;

always @(*)
    if (execute && (opcode_e == BAL)) begin // Branch Always
        next_pc_f = cir_e[7:0];
        flush = 1'b1;
    end else if (execute && (opcode_e == BCOND))
        // More to do here
        if ((cir_e[11:10] == 2'b00) && status[0]) begin
            next_pc_f = cir_e[7:0];
            flush = 1'b1;
        end else if ((cir_e[11:10] == 2'b11) && status[1]) begin
            next_pc_f = cir_e[7:0];
            flush = 1'b1;
        end else if ((cir_e[11:10] == 2'b01) && status[3]) begin
            next_pc_f = cir_e[7:0];
            flush = 1'b1;
        end else if ((cir_e[11:10] == 2'b10) && status[2]) begin
            next_pc_f = cir_e[7:0];
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
        pc_f <= 8'd0;
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

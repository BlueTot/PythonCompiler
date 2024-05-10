module processor (clk, nreset, address_bus, rdata_bus, wdata_bus, control_bus);

/////////////////////////////////////////
// Inputs and Outputs
/////////////////////////////////////////
input clk, nreset;
output [23:0] address_bus;
output [1:0] control_bus;
output [31:0] wdata_bus;
input [31:0] rdata_bus;

/////////////////////////////////////////
// Wires
/////////////////////////////////////////
wire ram_read, ram_write, reg_write;
wire [2:0] ra, rb, rc;
wire load, addressing_mode;
wire [20:0] immediate;
wire [3:0] opcode;
wire [31:0] reg_a_data, reg_b_data;
wire [31:0] reg_write_data, alu_result;
wire [3:0] cmp_result;

/////////////////////////////////////////
// Logic for Module
/////////////////////////////////////////
assign control_bus = {ram_read, ram_write};
assign reg_write_data = load ? rdata_bus : alu_result;
assign wdata_bus = reg_a_data;

/////////////////////////////////////////
// Instances
/////////////////////////////////////////
control_unit cu (
    .nreset (nreset), 
    .clk    (clk), 
    .ram_read         (ram_read), 
    .ram_address      (address_bus), 
    .instruction_data (rdata_bus),
    .ra (ra),
    .rb (rb),
    .rc (rc),
    .ram_write        (ram_write),
    .reg_write        (reg_write),

    //  For ALU Control
    .load_e            (load),
    .immediate_e       (immediate), 
    .opcode_e          (opcode), 
    .addressing_mode_e (addressing_mode),
    .cmp_result        (cmp_result),
    .result_d (alu_result)
    );

regfile ureg (
    .clk (clk), 
    .ra (ra), 
    .rb (rb), 
    .rc (rc), 
    .write_enable (reg_write), 
    .write_data   (reg_write_data), 
    .read_data_a  (reg_a_data), 
    .read_data_b  (reg_b_data)
);

alu ualu (
    .reg_a_data (reg_a_data), 
    .reg_b_data (reg_b_data), 
    .immediate  (immediate), 
    .opcode     (opcode), 
    .addressing_mode (addressing_mode),
    .result (alu_result),
    .cmp_result(cmp_result)
    );

endmodule

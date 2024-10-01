module regfile (clk, ra, rb, rc, write_enable, write_data, read_data_a, read_data_b);

/////////////////////////////////////////
// Inputs and Outputs
/////////////////////////////////////////
input clk;
input [2:0] ra, rb, rc;
input write_enable;
input [31:0] write_data;

output [31:0] read_data_a, read_data_b;

/////////////////////////////////////////
// Wires
/////////////////////////////////////////
reg [31:0] read_data_a, read_data_b; // These are wires
wire wen0, wen1, wen2, wen3, wen4, wen5, wen6, wen7;

/////////////////////////////////////////
// Registers
/////////////////////////////////////////
reg [31:0] r0, r1, r2, r3, r4, r5, r6, r7;

/////////////////////////////////////////
// Logic for Module
/////////////////////////////////////////
// Read Port A Multiplexor
always @(*) begin
    case (ra)
    3'd0 : read_data_a <= r0;
    3'd1 : read_data_a <= r1;
    3'd2 : read_data_a <= r2;
    3'd3 : read_data_a <= r3;
    3'd4 : read_data_a <= r4;
    3'd5 : read_data_a <= r5;
    3'd6 : read_data_a <= r6;
    3'd7 : read_data_a <= r7;
    default: read_data_a <= 31'bx;
    endcase
end

// Read Port B Multiplexor
always @(*) begin
    case (rb)
    3'd0 : read_data_b <= r0;
    3'd1 : read_data_b <= r1;
    3'd2 : read_data_b <= r2;
    3'd3 : read_data_b <= r3;
    3'd4 : read_data_b <= r4;
    3'd5 : read_data_b <= r5;
    3'd6 : read_data_b <= r6;
    3'd7 : read_data_b <= r7;
    default: read_data_b <= 31'bx;
    endcase
end

assign wen0 = write_enable && (rc == 3'd0);
assign wen1 = write_enable && (rc == 3'd1);
assign wen2 = write_enable && (rc == 3'd2);
assign wen3 = write_enable && (rc == 3'd3);
assign wen4 = write_enable && (rc == 3'd4);
assign wen5 = write_enable && (rc == 3'd5);
assign wen6 = write_enable && (rc == 3'd6);
assign wen7 = write_enable && (rc == 3'd7);

always @(posedge clk)
    if (wen0)
        r0 <= write_data;

always @(posedge clk)
    if (wen1)
        r1 <= write_data;

always @(posedge clk)
    if (wen2)
        r2 <= write_data;

always @(posedge clk)
    if (wen3)
        r3 <= write_data;

always @(posedge clk)
    if (wen4)
        r4 <= write_data;

always @(posedge clk)
    if (wen5)
        r5 <= write_data;

always @(posedge clk)
    if (wen6)
        r6 <= write_data;

always @(posedge clk)
    if (wen7)
        r7 <= write_data;

endmodule

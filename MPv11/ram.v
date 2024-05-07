module ram (Address, WriteData, ReadData, Clk, WE, RE);

/////////////////////////////////////////
// Inputs and Outputs
/////////////////////////////////////////
  input [7:0] Address;
  input [15:0] WriteData;
  output [15:0] ReadData;
  input Clk, WE, RE;

/////////////////////////////////////////
// Wires
/////////////////////////////////////////
  // For debugging!
  wire [15:0] addr_9, addr_10, addr_11;

/////////////////////////////////////////
// Memory Array
/////////////////////////////////////////
  reg [15:0] Mem [0:255];

/////////////////////////////////////////
// Logic for Module
/////////////////////////////////////////
  assign ReadData = RE ? Mem[Address] : 16'b0;

  always @(posedge Clk) begin
    if (WE)
      Mem[Address] <= WriteData;
  end

  // Debugging
  assign addr_9 = Mem[9];
  assign addr_10 = Mem[10];
  assign addr_11 = Mem[11];

endmodule

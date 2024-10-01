module ram (Address, WriteData, ReadData, Clk, WE, RE);

/////////////////////////////////////////
// Inputs and Outputs
/////////////////////////////////////////
  input [22:0] Address;
  input [31:0] WriteData;
  output [31:0] ReadData;
  input Clk, WE, RE;

/////////////////////////////////////////
// Wires
/////////////////////////////////////////
  // For debugging!
  wire[31:0] addr_1088, addr_1089, addr_1090, addr_1091, addr_1092, addr_1093, addr_1094, addr_1095, addr_1096, addr_1097;
  wire[31:0] addr_1024, addr_1025, addr_1026, addr_1027, addr_1028, addr_1029;

/////////////////////////////////////////
// Memory Array
/////////////////////////////////////////
  reg [31:0] Mem [0:16777215];

/////////////////////////////////////////
// Logic for Module
/////////////////////////////////////////
  assign ReadData = RE ? Mem[Address] : 31'b0;

  always @(posedge Clk) begin
    if (WE)
      Mem[Address] <= WriteData;
  end

  // Debugging
  assign addr_1024 = Mem[1024];
  assign addr_1025 = Mem[1025];
  assign addr_1026 = Mem[1026];
  assign addr_1027 = Mem[1027];
  assign addr_1028 = Mem[1028];
  assign addr_1029 = Mem[1029];
  assign addr_1088 = Mem[1088];
  assign addr_1089 = Mem[1089];
  assign addr_1090 = Mem[1090];
  assign addr_1091 = Mem[1091];
  assign addr_1092 = Mem[1092];
  assign addr_1093 = Mem[1093];
  assign addr_1094 = Mem[1094];
  assign addr_1095 = Mem[1095];
  assign addr_1096 = Mem[1096];
  assign addr_1097 = Mem[1097];

endmodule

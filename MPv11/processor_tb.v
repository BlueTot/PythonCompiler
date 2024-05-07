`timescale 1ns/1ps 

module processor_tb;

reg clk = 0;
reg nreset;

always #1 clk = !clk;

initial begin
    $readmemh("C:\\Users\\nhlo\\Documents\\GitHub\\PythonCompiler\\main\\memory.txt", u_ram.Mem,0,255);
    $dumpfile("iexec.vcd");
    $dumpvars(0,processor_tb);
    #1
    nreset = 0;
    #1
    nreset = 1;
    #10000
    $finish;
end

wire [7:0] addr;
wire [15:0] wdata;
wire [15:0] rdata;
wire we;
wire re;
wire [1:0] control_bus;

processor dut (
    .clk (clk), 
    .nreset (nreset), 
    .address_bus (addr), 
    .rdata_bus (rdata), 
    .wdata_bus (wdata), 
    .control_bus (control_bus)
    );

assign we = control_bus[0];
assign re = control_bus[1];

ram u_ram (
    .Address (addr), 
    .WriteData (wdata), 
    .ReadData (rdata), 
    .Clk (clk), 
    .WE (we), 
    .RE (re)
    );

endmodule

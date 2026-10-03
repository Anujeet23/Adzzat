// Data-hazard forwarding unit. When both EX/MEM and MEM/WB target the
// same source register, the MEM/WB (older) value is checked -- and
// therefore wins -- before EX/MEM is even considered, so the more
// recent EX/MEM value is incorrectly discarded. See
// /app/TASK_CONTRACT.md.
module forwarding_unit (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [4:0]  rs1,
    input  wire [4:0]  rs2,
    input  wire [4:0]  ex_mem_rd,
    input  wire        ex_mem_valid,
    input  wire [31:0] ex_mem_value,
    input  wire [4:0]  mem_wb_rd,
    input  wire        mem_wb_valid,
    input  wire [31:0] mem_wb_value,
    input  wire [31:0] regfile_rs1,
    input  wire [31:0] regfile_rs2,
    output reg  [31:0] rs1_value,
    output reg  [31:0] rs2_value
);
    always @(posedge clk) begin
        if (!rst_n) begin
            rs1_value <= 32'd0;
            rs2_value <= 32'd0;
        end else begin
            if (mem_wb_valid && (mem_wb_rd != 5'd0) && (mem_wb_rd == rs1))
                rs1_value <= mem_wb_value;
            else if (ex_mem_valid && (ex_mem_rd != 5'd0) && (ex_mem_rd == rs1))
                rs1_value <= ex_mem_value;
            else
                rs1_value <= regfile_rs1;

            if (mem_wb_valid && (mem_wb_rd != 5'd0) && (mem_wb_rd == rs2))
                rs2_value <= mem_wb_value;
            else if (ex_mem_valid && (ex_mem_rd != 5'd0) && (ex_mem_rd == rs2))
                rs2_value <= ex_mem_value;
            else
                rs2_value <= regfile_rs2;
        end
    end
endmodule

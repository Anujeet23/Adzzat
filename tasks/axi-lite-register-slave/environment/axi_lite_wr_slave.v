// AXI-Lite-style register write slave. After accepting a write, bvalid
// is asserted for exactly one cycle and then deasserted unconditionally
// -- even if bready was never observed high -- violating the AXI rule
// that VALID must stay asserted until READY is seen in the same cycle.
// A master that stalls bready for even one extra cycle silently loses
// the response. See /app/TASK_CONTRACT.md.
module axi_lite_wr_slave (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         awvalid,
    output reg          awready,
    input  wire [3:0]   awaddr,
    input  wire         wvalid,
    output reg          wready,
    input  wire [31:0]  wdata,
    output reg          bvalid,
    input  wire         bready,
    output wire [127:0] regs_flat
);
    localparam IDLE = 1'b0;
    localparam RESP = 1'b1;
    reg state;

    reg [31:0] regs0, regs1, regs2, regs3;

    assign regs_flat = {regs3, regs2, regs1, regs0};

    always @(posedge clk) begin
        if (!rst_n) begin
            state   <= IDLE;
            awready <= 1'b0;
            wready  <= 1'b0;
            bvalid  <= 1'b0;
            regs0   <= 32'd0;
            regs1   <= 32'd0;
            regs2   <= 32'd0;
            regs3   <= 32'd0;
        end else begin
            case (state)
                IDLE: begin
                    awready <= 1'b0;
                    wready  <= 1'b0;
                    if (awvalid && wvalid) begin
                        awready <= 1'b1;
                        wready  <= 1'b1;
                        case (awaddr[1:0])
                            2'd0: regs0 <= wdata;
                            2'd1: regs1 <= wdata;
                            2'd2: regs2 <= wdata;
                            2'd3: regs3 <= wdata;
                        endcase
                        bvalid <= 1'b1;
                        state  <= RESP;
                    end
                end
                RESP: begin
                    awready <= 1'b0;
                    wready  <= 1'b0;
                    bvalid  <= 1'b0;
                    state   <= IDLE;
                end
            endcase
        end
    end
endmodule

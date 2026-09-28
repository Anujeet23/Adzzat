// Synchronous FIFO. Full/empty flags are correct in isolation, but a write
// is gated only on the registered `full` flag, not on whether a
// simultaneous read is also freeing a slot in the very same cycle -- so a
// write issued in the same cycle as a read that empties the last slot of
// a full FIFO is silently dropped instead of succeeding. See
// /app/TASK_CONTRACT.md.
module fifo #(
    parameter WIDTH = 8,
    parameter DEPTH = 8
) (
    input  wire             clk,
    input  wire             rst_n,
    input  wire             wr_en,
    input  wire [WIDTH-1:0] wr_data,
    input  wire             rd_en,
    output reg  [WIDTH-1:0] rd_data,
    output wire             full,
    output wire             empty
);
    localparam AW = $clog2(DEPTH);

    reg [WIDTH-1:0] mem [0:DEPTH-1];
    reg [AW-1:0] wp, rp;
    reg [AW:0] count;

    assign full  = (count == DEPTH);
    assign empty = (count == 0);

    always @(posedge clk) begin
        if (!rst_n) begin
            wp      <= {AW{1'b0}};
            rp      <= {AW{1'b0}};
            count   <= {(AW+1){1'b0}};
            rd_data <= {WIDTH{1'b0}};
        end else begin
            if (wr_en && !full) begin
                mem[wp] <= wr_data;
                wp <= wp + 1'b1;
            end
            if (rd_en && !empty) begin
                rd_data <= mem[rp];
                rp <= rp + 1'b1;
            end

            if ((wr_en && !full) && !(rd_en && !empty))
                count <= count + 1'b1;
            else if (!(wr_en && !full) && (rd_en && !empty))
                count <= count - 1'b1;
        end
    end
endmodule

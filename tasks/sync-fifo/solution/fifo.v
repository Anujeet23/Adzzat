// Reference implementation. A write is allowed whenever the FIFO isn't
// full, OR it is full but a read is firing in the same cycle (freeing the
// slot the write needs); a read is allowed whenever the FIFO isn't empty.
// Occupancy is updated from exactly those two "fire" conditions, so a
// simultaneous write+read at full leaves occupancy unchanged (one out,
// one in) instead of silently dropping the write.
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

    wire rd_fire = rd_en && !empty;
    wire wr_fire = wr_en && (!full || rd_fire);

    always @(posedge clk) begin
        if (!rst_n) begin
            wp      <= {AW{1'b0}};
            rp      <= {AW{1'b0}};
            count   <= {(AW+1){1'b0}};
            rd_data <= {WIDTH{1'b0}};
        end else begin
            if (wr_fire) begin
                mem[wp] <= wr_data;
                wp <= wp + 1'b1;
            end
            if (rd_fire) begin
                rd_data <= mem[rp];
                rp <= rp + 1'b1;
            end

            if (wr_fire && !rd_fire)
                count <= count + 1'b1;
            else if (!wr_fire && rd_fire)
                count <= count - 1'b1;
        end
    end
endmodule

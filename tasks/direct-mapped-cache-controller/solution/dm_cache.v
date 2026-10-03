// Reference implementation. On a miss, if the line being evicted is
// valid and dirty, its data is written back to the backing store at
// its own (reconstructed) address before the line is overwritten.
module dm_cache #(
    parameter ADDR_WIDTH  = 8,
    parameter INDEX_WIDTH = 3,
    parameter DATA_WIDTH  = 8
) (
    input  wire                  clk,
    input  wire                  rst_n,
    input  wire                  req,
    input  wire                  we,
    input  wire [ADDR_WIDTH-1:0] addr,
    input  wire [DATA_WIDTH-1:0] wdata,
    output reg                   done,
    output reg                   hit,
    output reg  [DATA_WIDTH-1:0] rdata
);
    localparam LINES = 1 << INDEX_WIDTH;
    localparam TAG_WIDTH = ADDR_WIDTH - INDEX_WIDTH;

    reg [DATA_WIDTH-1:0] cache_data  [0:LINES-1];
    reg [TAG_WIDTH-1:0]  cache_tag   [0:LINES-1];
    reg                  cache_valid[0:LINES-1];
    reg                  cache_dirty[0:LINES-1];
    reg [DATA_WIDTH-1:0] mem [0:(1<<ADDR_WIDTH)-1];

    integer k;
    wire [TAG_WIDTH-1:0]   req_tag   = addr[ADDR_WIDTH-1:INDEX_WIDTH];
    wire [INDEX_WIDTH-1:0] req_index = addr[INDEX_WIDTH-1:0];
    reg line_hit;

    initial begin
        for (k = 0; k < (1 << ADDR_WIDTH); k = k + 1) mem[k] = k[DATA_WIDTH-1:0];
    end

    always @(posedge clk) begin
        if (!rst_n) begin
            done <= 1'b0;
            hit  <= 1'b0;
            for (k = 0; k < LINES; k = k + 1) begin
                cache_valid[k] <= 1'b0;
                cache_dirty[k] <= 1'b0;
            end
        end else begin
            done <= 1'b0;
            if (req) begin
                line_hit = cache_valid[req_index] && (cache_tag[req_index] == req_tag);
                hit  <= line_hit;
                done <= 1'b1;
                if (line_hit) begin
                    if (we) begin
                        cache_data[req_index]  <= wdata;
                        cache_dirty[req_index] <= 1'b1;
                    end else begin
                        rdata <= cache_data[req_index];
                    end
                end else begin
                    if (cache_valid[req_index] && cache_dirty[req_index]) begin
                        mem[{cache_tag[req_index], req_index}] <= cache_data[req_index];
                    end
                    cache_valid[req_index] <= 1'b1;
                    cache_tag[req_index]   <= req_tag;
                    cache_dirty[req_index] <= we;
                    if (we) begin
                        cache_data[req_index] <= wdata;
                        rdata <= wdata;
                    end else begin
                        cache_data[req_index] <= mem[addr];
                        rdata <= mem[addr];
                    end
                end
            end
        end
    end
endmodule

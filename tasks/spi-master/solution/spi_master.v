// Reference implementation. Reloads the half-bit-period counter at
// `half_count == CLKS_PER_HALF_BIT - 1`, so every sck edge lands exactly
// CLKS_PER_HALF_BIT cycles after the previous one, with no drift.
module spi_master #(
    parameter WIDTH = 8,
    parameter CLKS_PER_HALF_BIT = 4
) (
    input  wire             clk,
    input  wire             rst_n,
    input  wire             start,
    input  wire [WIDTH-1:0] tx_data,
    input  wire             miso,
    output reg              busy,
    output reg              done,
    output reg  [WIDTH-1:0] rx_data,
    output reg              sck,
    output reg              mosi
);
    localparam EDGE_W = 5;

    reg [7:0] half_count;
    reg [EDGE_W-1:0] edge_idx;
    reg [WIDTH-1:0] shift_reg;

    always @(posedge clk) begin
        if (!rst_n) begin
            busy       <= 1'b0;
            done       <= 1'b0;
            rx_data    <= {WIDTH{1'b0}};
            sck        <= 1'b0;
            mosi       <= 1'b0;
            half_count <= 8'd0;
            edge_idx   <= {EDGE_W{1'b0}};
            shift_reg  <= {WIDTH{1'b0}};
        end else begin
            done <= 1'b0;
            if (!busy) begin
                sck <= 1'b0;
                if (start) begin
                    busy       <= 1'b1;
                    shift_reg  <= tx_data;
                    mosi       <= tx_data[WIDTH-1];
                    half_count <= 8'd0;
                    edge_idx   <= {EDGE_W{1'b0}};
                end
            end else begin
                if (half_count == CLKS_PER_HALF_BIT - 8'd1) begin
                    half_count <= 8'd0;
                    sck <= ~sck;
                    if (edge_idx[0] == 1'b0) begin
                        rx_data <= {rx_data[WIDTH-2:0], miso};
                    end else begin
                        mosi      <= shift_reg[WIDTH-2];
                        shift_reg <= {shift_reg[WIDTH-2:0], 1'b0};
                    end
                    if (edge_idx == (2 * WIDTH - 1)) begin
                        busy <= 1'b0;
                        done <= 1'b1;
                    end
                    edge_idx <= edge_idx + 1'b1;
                end else begin
                    half_count <= half_count + 8'd1;
                end
            end
        end
    end
endmodule

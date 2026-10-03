// UART transmitter. The bit-duration counter reloads one cycle too late
// (`clk_count == CLKS_PER_BIT` instead of `CLKS_PER_BIT - 1`), so every
// bit in the frame -- start, all 8 data bits, and the stop bit -- is
// held one cycle longer than it should be, drifting cumulatively across
// the frame. See /app/TASK_CONTRACT.md.
module uart_tx #(
    parameter CLKS_PER_BIT = 4
) (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       tx_start,
    input  wire [7:0] tx_data,
    output reg        tx_busy,
    output reg        tx,
    output reg        tx_done
);
    localparam IDLE  = 2'd0;
    localparam START = 2'd1;
    localparam DATA  = 2'd2;
    localparam STOP  = 2'd3;

    reg [1:0] state;
    reg [7:0] clk_count;
    reg [2:0] bit_index;
    reg [7:0] data_reg;

    always @(posedge clk) begin
        if (!rst_n) begin
            state     <= IDLE;
            clk_count <= 8'd0;
            bit_index <= 3'd0;
            tx        <= 1'b1;
            tx_busy   <= 1'b0;
            tx_done   <= 1'b0;
            data_reg  <= 8'd0;
        end else begin
            tx_done <= 1'b0;
            case (state)
                IDLE: begin
                    tx <= 1'b1;
                    if (tx_start) begin
                        tx_busy   <= 1'b1;
                        data_reg  <= tx_data;
                        clk_count <= 8'd0;
                        state     <= START;
                    end
                end
                START: begin
                    tx <= 1'b0;
                    if (clk_count == CLKS_PER_BIT) begin
                        clk_count <= 8'd0;
                        bit_index <= 3'd0;
                        state     <= DATA;
                    end else begin
                        clk_count <= clk_count + 8'd1;
                    end
                end
                DATA: begin
                    tx <= data_reg[bit_index];
                    if (clk_count == CLKS_PER_BIT) begin
                        clk_count <= 8'd0;
                        if (bit_index == 3'd7) begin
                            state <= STOP;
                        end else begin
                            bit_index <= bit_index + 3'd1;
                        end
                    end else begin
                        clk_count <= clk_count + 8'd1;
                    end
                end
                STOP: begin
                    tx <= 1'b1;
                    if (clk_count == CLKS_PER_BIT) begin
                        clk_count <= 8'd0;
                        state     <= IDLE;
                        tx_busy   <= 1'b0;
                        tx_done   <= 1'b1;
                    end else begin
                        clk_count <= clk_count + 8'd1;
                    end
                end
                default: state <= IDLE;
            endcase
        end
    end
endmodule

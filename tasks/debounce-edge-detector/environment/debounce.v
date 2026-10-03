// Button debouncer + edge detector. Once it starts timing toward a
// candidate value, a further change in btn_raw never restarts the
// timer -- it keeps counting toward the stale, originally-sampled
// candidate regardless. btn_rise/btn_fall are also derived directly
// from raw transitions instead of from btn_clean, so every noisy raw
// toggle produces a spurious pulse. See /app/TASK_CONTRACT.md.
module debounce #(
    parameter DEBOUNCE_CYCLES = 4
) (
    input  wire clk,
    input  wire rst_n,
    input  wire btn_raw,
    output reg  btn_clean,
    output reg  btn_rise,
    output reg  btn_fall
);
    reg [7:0] count;
    reg       candidate;
    reg       counting;
    reg       prev_raw;

    always @(posedge clk) begin
        if (!rst_n) begin
            btn_clean <= 1'b0;
            btn_rise  <= 1'b0;
            btn_fall  <= 1'b0;
            count     <= 8'd0;
            candidate <= 1'b0;
            counting  <= 1'b0;
            prev_raw  <= 1'b0;
        end else begin
            btn_rise <= 1'b0;
            btn_fall <= 1'b0;

            if (btn_raw && !prev_raw) btn_rise <= 1'b1;
            if (!btn_raw && prev_raw) btn_fall <= 1'b1;
            prev_raw <= btn_raw;

            if (!counting) begin
                if (btn_raw != btn_clean) begin
                    counting  <= 1'b1;
                    candidate <= btn_raw;
                    count     <= 8'd1;
                end
            end else begin
                if (count == DEBOUNCE_CYCLES - 1'b1) begin
                    btn_clean <= candidate;
                    counting  <= 1'b0;
                end else begin
                    count <= count + 8'd1;
                end
            end
        end
    end
endmodule

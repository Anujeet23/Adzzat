// Reference implementation. Restarts the debounce timer against the
// new value whenever btn_raw changes mid-count, and derives
// btn_rise/btn_fall from btn_clean's own transition, not from raw.
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

    always @(posedge clk) begin
        if (!rst_n) begin
            btn_clean <= 1'b0;
            btn_rise  <= 1'b0;
            btn_fall  <= 1'b0;
            count     <= 8'd0;
            candidate <= 1'b0;
            counting  <= 1'b0;
        end else begin
            btn_rise <= 1'b0;
            btn_fall <= 1'b0;

            if (!counting) begin
                if (btn_raw != btn_clean) begin
                    counting  <= 1'b1;
                    candidate <= btn_raw;
                    count     <= 8'd1;
                end
            end else begin
                if (btn_raw != candidate) begin
                    candidate <= btn_raw;
                    count     <= 8'd1;
                    if (btn_raw == btn_clean) begin
                        counting <= 1'b0;
                    end
                end else if (count == DEBOUNCE_CYCLES - 1'b1) begin
                    btn_clean <= candidate;
                    counting  <= 1'b0;
                    if (candidate && !btn_clean) btn_rise <= 1'b1;
                    if (!candidate && btn_clean) btn_fall <= 1'b1;
                end else begin
                    count <= count + 8'd1;
                end
            end
        end
    end
endmodule

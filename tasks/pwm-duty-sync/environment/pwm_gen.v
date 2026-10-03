// PWM generator. Compares the counter against the live `duty` input
// directly every cycle, so a write to `duty` takes effect on the very
// next clock edge regardless of where the counter is -- it is never
// latched and held off until the next period boundary, so a mid-period
// change glitches the current period's waveform. See
// /app/TASK_CONTRACT.md.
module pwm_gen #(
    parameter WIDTH = 8
) (
    input  wire             clk,
    input  wire             rst_n,
    input  wire [WIDTH-1:0] period,
    input  wire [WIDTH-1:0] duty,
    output reg              pwm_out
);
    reg [WIDTH-1:0] counter;

    always @(posedge clk) begin
        if (!rst_n) begin
            counter <= {WIDTH{1'b0}};
            pwm_out <= 1'b0;
        end else begin
            pwm_out <= (counter < duty);
            if (counter == period - 1'b1) begin
                counter <= {WIDTH{1'b0}};
            end else begin
                counter <= counter + 1'b1;
            end
        end
    end
endmodule

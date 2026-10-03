// Reference implementation. `duty` is latched into `duty_reg` only at
// the moment the counter wraps (period boundary), and `pwm_out` always
// compares against `duty_reg`, never the live `duty` input -- so a
// mid-period write has no effect until the next period begins.
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
    reg [WIDTH-1:0] duty_reg;

    always @(posedge clk) begin
        if (!rst_n) begin
            counter  <= {WIDTH{1'b0}};
            duty_reg <= {WIDTH{1'b0}};
            pwm_out  <= 1'b0;
        end else begin
            pwm_out <= (counter < duty_reg);
            if (counter == period - 1'b1) begin
                counter  <= {WIDTH{1'b0}};
                duty_reg <= duty;
            end else begin
                counter <= counter + 1'b1;
            end
        end
    end
endmodule

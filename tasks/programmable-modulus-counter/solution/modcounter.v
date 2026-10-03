// Reference implementation. Wraps at `count == modulus - 1` (so exactly
// `modulus` distinct values are produced), and `load` resets `count` to
// 0 in the same cycle the new modulus is latched.
module modcounter #(
    parameter WIDTH = 8
) (
    input  wire             clk,
    input  wire             rst_n,
    input  wire             load,
    input  wire [WIDTH-1:0] mod_in,
    input  wire             en,
    output reg  [WIDTH-1:0] count,
    output reg              overflow
);
    reg [WIDTH-1:0] modulus;

    always @(posedge clk) begin
        if (!rst_n) begin
            count    <= {WIDTH{1'b0}};
            modulus  <= {WIDTH{1'b0}};
            overflow <= 1'b0;
        end else begin
            overflow <= 1'b0;
            if (load) begin
                modulus <= mod_in;
                count   <= {WIDTH{1'b0}};
            end else if (en) begin
                if (count == modulus - 1'b1) begin
                    count    <= {WIDTH{1'b0}};
                    overflow <= 1'b1;
                end else begin
                    count <= count + 1'b1;
                end
            end
        end
    end
endmodule

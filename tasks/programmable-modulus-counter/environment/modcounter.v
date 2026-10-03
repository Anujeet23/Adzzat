// Programmable-modulus counter. `count` wraps one value too late (it
// reaches `modulus` itself before wrapping, giving modulus+1 distinct
// values instead of modulus), and `load` updates the modulus register
// without resetting `count`, so a stale count can sit outside the new
// modulus's valid range. See /app/TASK_CONTRACT.md.
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
            end else if (en) begin
                if (count >= modulus) begin
                    count    <= {WIDTH{1'b0}};
                    overflow <= 1'b1;
                end else begin
                    count <= count + 1'b1;
                end
            end
        end
    end
endmodule

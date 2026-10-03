// Reference implementation. Rotates the priority pointer to
// `chosen + 1` (wrapping via natural 2-bit overflow since N=4), so the
// just-granted requester becomes lowest priority for the next cycle.
module rr_arbiter #(
    parameter N = 4
) (
    input  wire         clk,
    input  wire         rst_n,
    input  wire [N-1:0] req,
    output reg  [N-1:0] grant
);
    reg [1:0] ptr;
    integer i;
    reg found;
    reg [1:0] idx;
    reg [1:0] chosen;

    always @(posedge clk) begin
        if (!rst_n) begin
            ptr   <= 2'd0;
            grant <= {N{1'b0}};
        end else begin
            grant <= {N{1'b0}};
            found = 1'b0;
            chosen = 2'd0;
            for (i = 0; i < N; i = i + 1) begin
                idx = ptr + i[1:0];
                if (!found && req[idx]) begin
                    found = 1'b1;
                    chosen = idx;
                end
            end
            if (found) begin
                grant[chosen] <= 1'b1;
                ptr <= chosen + 2'd1;
            end
        end
    end
endmodule

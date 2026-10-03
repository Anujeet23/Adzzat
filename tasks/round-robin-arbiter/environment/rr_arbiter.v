// Round-robin arbiter, N=4. After granting requester `chosen`, the
// priority pointer rotates back onto `chosen` itself instead of past
// it, so a requester holding its request line continuously is granted
// again on every subsequent cycle, starving everyone else. See
// /app/TASK_CONTRACT.md.
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
                ptr <= chosen;
            end
        end
    end
endmodule

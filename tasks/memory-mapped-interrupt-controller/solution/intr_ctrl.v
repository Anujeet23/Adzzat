// Reference implementation. `ack` clears only `pending[irq_id]`, the
// specific source currently being reported, leaving every other
// pending bit untouched.
module intr_ctrl #(
    parameter N = 4
) (
    input  wire         clk,
    input  wire         rst_n,
    input  wire [N-1:0] irq_in,
    input  wire [N-1:0] irq_enable,
    input  wire         ack,
    output reg           irq_out,
    output reg  [N-1:0]  pending,
    output reg  [1:0]    irq_id
);
    reg [N-1:0] irq_in_prev;
    integer i;
    reg found;
    reg [1:0] chosen;

    always @(posedge clk) begin
        if (!rst_n) begin
            pending     <= {N{1'b0}};
            irq_in_prev <= {N{1'b0}};
            irq_out     <= 1'b0;
            irq_id      <= 2'd0;
        end else begin
            for (i = 0; i < N; i = i + 1) begin
                if (irq_in[i] && !irq_in_prev[i]) begin
                    pending[i] <= 1'b1;
                end
            end
            irq_in_prev <= irq_in;

            if (ack) begin
                pending[irq_id] <= 1'b0;
            end

            found = 1'b0;
            chosen = 2'd0;
            for (i = 0; i < N; i = i + 1) begin
                if (!found && pending[i] && irq_enable[i]) begin
                    found = 1'b1;
                    chosen = i[1:0];
                end
            end
            irq_out <= found;
            irq_id  <= chosen;
        end
    end
endmodule

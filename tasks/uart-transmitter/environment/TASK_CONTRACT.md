# UART transmitter — contract

Source: an original, minimal starter at `/app/repo/uart_tx.v`, not a fork of an existing project.

## Port list

```
module uart_tx #(parameter CLKS_PER_BIT = 4) (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       tx_start,
    input  wire [7:0] tx_data,
    output reg        tx_busy,
    output reg        tx,
    output reg        tx_done
);
```

`CLKS_PER_BIT` is fixed at `4` for grading. `rst_n` is active-low, synchronous. Frame: start bit (`0`), 8 data bits LSB-first, stop bit (`1`), each held exactly `CLKS_PER_BIT` cycles. `tx` idles high.

## Guarantees

1. **Exact bit duration.** Every bit in the frame is held for exactly `CLKS_PER_BIT` cycles -- no cumulative drift.
2. **Bit order.** Data bits transmit LSB-first.
3. **`tx_busy` coverage.** High for the entire frame duration, low otherwise.
4. **`tx_done` pulse.** High for exactly one cycle, on the last cycle of the stop bit.
5. **Back-to-back correctness.** A `tx_start` pulse issued immediately after `tx_busy` drops starts a new, correctly-timed frame with no corruption from the previous one.

## What's out of scope

Parity, configurable baud/frame format, flow control, and any `CLKS_PER_BIT` value other than its fixed default of `4`.

## Delivery

Copy the complete `uart_tx.v` file to `/app/submission/uart_tx.v`. The verifier compiles and simulates only that file, in Icarus Verilog, in a separate container from the one you worked in. It does not read `/app/repo`.

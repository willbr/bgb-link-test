https://wiki.forth-ev.de/lib/exe/fetch.php/en:projects:a-start-with-forth:3_instruction_forth.pdf

1. Initialize the processor.
2. Initialize the serial port.
3. Repeat the following forever:
Get a byte from the serial port.
If byte = 01 [fetch]
A. Get address from the serial port.
B. Fetch the byte from that address.
C. Send the byte to the serial port.
Else If byte = 02 [store]
A. Get address from the serial port.
B. Get a byte from the serial port.
C. Store the byte at that address.
Else If byte = 03 [call]
A. Get address from the serial port.
B. Jump to the subroutine at that address.
End If.





# The 3 instructions are

XC@ fetch a byte
XC! store a byte
XCALL jump to a subroutine
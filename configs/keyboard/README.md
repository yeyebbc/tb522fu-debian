# White keyboard backlight candidate

Not hardware accepted or installed. Production remains CI39.

Patches0165–0168 add `lenovo:white:kbd_backlight` with a brightness range of
0..228. Steady white uses mode1 and equal RGB components100; the independent
brightness opcode is0x34. These fields come from the TB522FU stock SDK and
shipped keyboard module. No proprietary application or firmware is included.

The UART parent owns the GPIO60 direction gate through standard RS485
properties. Its pre-send delay is1ms, rounding the stock450us minimum up to the
binding's millisecond units; the DMA completion interrupt releases the line.
Receive stays active for local echo. Timer cancellation and chained DMA are
handled in the UART driver. The keyboard driver checks the exact14-byte padded
request echo, matching stock kernel setting writes. An echo is transport evidence,
not proof of illumination. Separate replies are counted without inventing their
payload semantics. Commands have bounded timeouts and no background retries.

Default requested brightness is57, restored once after the keyboard announces
synchronization. Changes made while detached or with the lid closed are saved
for the next active sync. The normal LED class exposes brightness to desktop
software. Older receive-only device trees retain their original TX-disabled path.
RGB effects, physical Fn+Space behavior and suspend remain unverified.

Before promotion, verify physical off/white/brightness changes with a camera,
unchanged keyboard/trackpad/lid nodes and packet decoding, no UART faults, Wi-Fi
traffic and Bluetooth initialization/discovery after the shared UART change.
Then verify the installed boot path and clean Android return. Keep the accepted
kernel as rollback; do not infer hardware success from this source or CI build.

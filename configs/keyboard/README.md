# White keyboard backlight

Installed CI44 passed recorded white off/on and normal-boot acceptance.
The LED is binary: no dimming is advertised. CI41 and CI42 both produced
visually indistinguishable nonzero dimming steps; those mappings were not
promoted. No further speculative dimming commands are planned.

Patches0165–0170 add `lenovo:white:kbd_backlight` with max_brightness1:
0 means off,1 means steady white. Steady mode1 uses equal RGB100 when on,
zero when off, with the known0x34enabled228/off0 command. These exact endpoint
packets were exercised in CI42. Fields come from the TB522FU stock SDK and
shipped keyboard module. No proprietary application or firmware is included.

The UART parent owns the GPIO60 direction gate through standard RS485
properties. Its pre-send delay is1ms, rounding the stock450us minimum up to the
binding's millisecond units; the DMA completion interrupt releases the line.
Receive stays active for local echo. Timer cancellation and chained DMA are
handled in the UART driver. The keyboard driver checks the exact14-byte padded
request echo, matching stock kernel setting writes. An echo is transport evidence,
not proof of illumination. Separate replies are counted without inventing their
payload semantics. Commands have bounded timeouts and no background retries.

Default requested brightness is1 (on), restored once after the keyboard announces
synchronization. Changes made while detached or with the lid closed are saved
for the next active sync. The normal LED class exposes brightness to desktop
software. Older receive-only device trees retain their original TX-disabled path.
Dimming, RGB effects, physical Fn+Space behavior and suspend remain unverified.

Bounded and normal installed CI44 tests verified three physical off/white
cycles, visible GNOME, preserved input nodes and packet decoding, no relevant
UART faults, Wi-Fi traffic and Bluetooth automatic setup/discovery/idle/quick
power reopening. Android return and full filesystem checks passed. CI39 is
retained for rollback. Physical typing/Fn+Space and suspend still need testing.
The same build includes the attributed upstream Bluetooth IBS lifecycle fix
(patch0171) following the CI42 second-setup timeout.

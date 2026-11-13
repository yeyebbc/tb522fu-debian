# Per-device Bluetooth identity

The WCN7861 controller needs its stock public address after registration. Keep
the address in `/etc/tb522fu/bluetooth-address`, a root-owned mode0600 file,
containing one colon-separated address from this device's stock Android data.
Neither the address nor the firmware/calibration belongs in this repository.

`device/` includes a udev rule, a systemd template and a bounded oneshot helper.
The rule matches the board UART; the helper additionally validates the live
device tree and HCI ancestry. It uses Linux MGMT to configure only a controller
missing exactly its public address. Already configured controllers are checked
without modification; a different address fails. Other adapters are ignored.
BlueZ retains its normal power, discovery and pairing policy. No periodic
keepalive, reset, firmware rewrite or global locale setting is involved.

The template is ordered before `bluetooth.service` when both are starting.
If BlueZ is already running, its standard IndexAdded handling discovers the
newly configured controller. udev starts the instance again after a genuine
device removal/addition. A boot-scoped private receipt is written under `/run`.

Protocol reference: [BlueZ 5.82 MGMT API](https://github.com/bluez/bluez/blob/5.82/doc/mgmt-api.txt).
Offline refusal and reindexing tests pass. The udev-started service automatically
provisions and verifies the address in fresh bounded and installed CI39 boots,
with no manual provisioning command in either inspector. BlueZ discovery receives
fresh MGMT DeviceFound packets; idle commands and a full power off/on pass while
Wi-Fi stays associated. The installed image is accepted on the test tablet.
Pairing and reconnection with a user-selected peripheral remain untested.

The initial controller setup plus address-triggered setup takes about 66 seconds;
subsequent power reopening takes about 34 seconds. The service does not apply a
power policy or repeat initialization to hide failures.

A later bounded CI42 boot exposed an intermittent second-setup failure: a stray
IBS wake acknowledgement preceded a firmware command timeout. Installed CI44
includes the unchanged [upstream power-off state reset](https://lore.kernel.org/r/20261014180201.57109-1-birk.skyum@pm.me),
which drains old sleep workers/timers and resets host state when the controller
loses power. Automatic address setup, fresh discovery, idle HCI replies and
quick off/on passed in both bounded and normal installed boots. The normal test
measured both host IBS states asleep after power-off, a0.500-second off interval,
and a real HCI reply after reopening. Wi-Fi remained associated. No firmware,
calibration, pacing, timeout or retry changes were made. Pairing, peripheral
traffic/reconnect and suspend remain untested.

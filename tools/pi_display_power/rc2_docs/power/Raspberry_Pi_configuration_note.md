# Raspberry Pi 5 configuration note

The Pi is powered from regulated 5 V on its GPIO header (not a USB-C PD adapter), so it cannot negotiate 5 A and will assume a 3 A limit (USB peripheral current limited to 600 mA).

Set `PSU_MAX_CURRENT=5000` in the bootloader EEPROM config (`sudo -E rpi-eeprom-config --edit`, add the line, reboot) **only after all of the following are verified on the bench**:

- [ ] RSDW40F-05 produces a stable 5 V at TP3/TP4 under no load, 50 % and peak load (scope: ripple + transient on `5V_PI`)
- [ ] Harness carries the required current continuously: connector/wire temperature rise stays acceptable after 30 min at worst-case load (Pi 5 stress test + display at full brightness + peripherals)
- [ ] Voltage **at the Pi 5V pins** stays within 4.75–5.25 V at worst-case load (measure at the header, not at TP4)
- [ ] `vcgencmd get_throttled` reports `0x0` under load; no undervoltage in `dmesg`
- [ ] Pi current and display current measured separately (the display is fed from J_DISP, not through the Pi pins) and recorded; Pi branch <= 5.0 A, total <= 6.0 A

**The Pi USB-C power input must not be connected to a power source while the 5 V harness is fitted** (no second 5 V supply; back-feed hazard). USB-C may still be used for data/other permitted functions (e.g. device mode) without supplying VBUS power.
Do not raise the output with TRIM to compensate for wiring unless the measured Pi-pin voltage requires it and stays inside Raspberry Pi limits.

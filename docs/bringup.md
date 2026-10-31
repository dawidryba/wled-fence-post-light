# Bring-up and test procedure

Write the measured value next to the expected one for each point. `[E]` means the lamp with the ESP32, `[S]` the lamps without it.

## 0. Before building the chain

- [ ] Loop resistance of each Cat5e run: at the far end, short the 3 +12 V wires to the 4 GND wires and measure with an ohmmeter. Expected for copper, 5 m, 3 + 4 wires: about 0.25 Ω. At 0.35 Ω or more you likely have CCA cable or bad joints, so re-run `calc/spadek_cat5e.py`.
- [ ] Mini560 Pro: measure the unloaded output, 5.0 to 5.2 V, **before** soldering C8.
- [ ] Fuse at the supply: 7.5 A slow-blow or ATO (inrush at switch-on is 25 to 50 A for under 1 ms).

## 1. Each board on its own

Use a lab supply, limited to 100 mA at first, then 1.5 A.

- [ ] Resistance from V12P, V12SW, V5LED and V5ESP to GND: no shorts.
- [ ] 12 V on J1 gives about 12 V at TP1. Reversed polarity (briefly, 100 mA limit): no current.
- [ ] Lamp [S]: TP2 equals TP1 (wire across the Q2 pads). Lamp [E]: TP2 about 0 V until WLED switches it on.
- [ ] TP9 about equal to TP2, TP3 = 5.0 to 5.2 V, TP4 [E] = 5.0 to 5.2 V.
- [ ] Oscilloscope on the first LED data input (TP5): levels 0 and 5 V, T0H at most 400 ns (SK6812 datasheet).

## 2. WLED settings (lamp [E])

- LED type **SK6812 RGBW**, colour order **GRB**, LED count 40 × number of lamps (240 for 6 lamps).
- Data GPIO **16**, Relay GPIO **26**, relay active high.
- ABL: **LED current = custom 40 mA** (never less, because WLED would then pass more current than its model assumes), **max current = 3600 mA** to start with. WLED subtracts about 100 mA for the ESP.
- Do not connect USB to the ESP while the board is powered from 12 V.

## 3. Chain of 6 lamps: voltage

Condition: TP9 at least 8 V. Measure **TP9 (V12LED)** on lamps 5 and 6 at brightness 255:

- [ ] Worst case: W = 255 on lamps 4 to 6 plus full RGB on lamps 5 and 6, the rest off.
- [ ] W = 255 on all lamps.
- [ ] Even RGBW white on all lamps.

If below 8 V, lower the WLED max current and repeat. Note the final value.

## 4. Converter undervoltage latch and start-up

- [ ] Reboot WLED while the lamps are on: all lamps come back.
- [ ] Switch off and on from the app after 0.5 s, 2 s and 5 s: all lamps come back.
- [ ] Interrupt the 12 V supply for 0.3 s, 1 s and 3 s: the ESP and all lamps come back (R10, R11).
- [ ] 20 cold starts of the whole chain (with C8): all lamps start every time. If far lamps do not start, reduce or omit C8 and check R10.
- [ ] Oscilloscope on V12P of lamp 1 at switch-on (C4 not fitted): dip and duration, and whether the supply trips.

## 5. Heat (observation)

- [ ] After 1 h of the intended program: temperature of the LED board and the translucent band. PETG softens at about 80 °C.

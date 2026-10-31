# Assembly guide

Order matters: **the electronics go in before the wedges.** The main PCB has the same 80×80 mm outline as the post, so the stops can only be added once the boards are inside.

## 1. Print

Use `enclosure/makerworld/Fence_post_light_80x80_PETG_AMS.3mf`. The plate holds the housing, printed upside down on the roof, and 4 wedges next to it. The wedges are as tall as the roof, so they print in the same black layers with no extra colour changes.

No supports, no brim. Swap in your own PETG if you like, but keep the band filament translucent.

Fit check after printing: slide one wedge into a corner slot from the bottom of the housing. It should move with light pressure. If it is tight, sand the wedge tongue, not the slot.

## 2. Heat-set inserts

Melt 4 M2.5 inserts into the standoffs under the roof (hole Ø3.3 × 5 mm).

## 3. Main board

Each lamp is built in one of two variants:

| | First lamp (with ESP32) | All other lamps |
|---|---|---|
| Fit | Q2, ZD2, R3, Q3, R4, R5, F2, C11, C12, U2, C13, C14, R11, U3, R6 | Leave those empty |
| Q2 position | MOSFET | Wire across the pads, D to S, at least 0.5 mm² |
| JP1 | Bridge A to centre | Bridge B to centre |

R2 is always fitted. Measure 5.0 to 5.2 V at the Mini560 output **before** soldering C8.

## 4. LED boards

1. Snap the boards out of the panel and file the burrs, especially on the long edge at the centre, which rests against the main board.
2. Push the 4 boards into the slots LB1 to LB4. The tabs have different lengths, so a board only fits the correct way round.
3. Solder the tabs on both sides of the main board.

If a slot is too tight, sand the slot in the main board, not the tabs: the tabs have pads on both sides.

## 5. Test on the bench

Run sections 0 to 2 of the [bring-up guide](bringup.md) before closing anything up.

## 6. Mount in the housing

1. Pass the Cat5e cables through the hollow post, or bring them to the housing from below.
2. Connect the cables to J1 (in) and J2 (out), following the silkscreen. One wire per terminal, no twisting wires together.

   | Terminals | Function | Wire colours |
   |---|---|---|
   | 1 to 3 | +12 V | orange, white-orange, brown |
   | 4 to 7 | GND | blue, white-blue, white-brown, white-green |
   | 8 | Data | green |

3. Lift the electronics into the housing from below and fasten the main board to the standoffs with 4 M2.5 screws. Near the ESP32 antenna at (−31, −31) use a nylon screw. At (−31, 31) use a screw head of at most 4.5 mm or a nylon washer, because a trace runs under it.

## 7. Wedges

Slide one wedge into each of the 4 corner slots from the bottom, tongue first, until it stops. The wedge bottom ends up 25 mm above the bottom edge of the housing. Nothing is visible from outside.

To open the lamp again, pull the wedges back down.

## 8. On the post

Slide the lamp onto the post until the post top rests on the wedges. The ribs centre it. The lamp is held only by friction and its own weight, so secure it yourself if it is exposed to strong wind.

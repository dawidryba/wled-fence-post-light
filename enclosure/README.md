# Enclosure

Parametric FreeCAD model of the housing. Everything comes from `build.py`, so change a parameter at the top of the file and rebuild.

## Files

| File | Contents |
|---|---|
| `makerworld/Fence_post_light_80x80_PETG_AMS.3mf` | Ready Bambu Studio project: housing + 4 wedges on one plate, stock PETG presets |
| `exports/lampka_czarny_dol.stl` | Black base zone (Z 0 to 39) |
| `exports/lampka_pas_transparentny.stl` | Translucent band zone (Z 39 to 79) |
| `exports/lampka_czarny_daszek.stl` | Black roof zone (Z 79 to 83) |
| `exports/lampka_kliny_x4.stl` | The 4 post stop wedges, laid out for printing |
| `exports/lampka.step`, `exports/lampka_klin.step` | Housing and one wedge as STEP |

The three housing STL files are colour zones of **one object**. Load them together as parts of a single object and assign filaments. They are not separate parts to glue.

STL files are in the lamp's own orientation, with the roof up. Flip the housing for printing so the roof is on the bed. `druk.py` does this for you.

## Print settings

| Setting | Value |
|---|---|
| Orientation | Roof on the bed |
| Layer height | 0.20 mm |
| Walls | 9, so the 4 mm wall is solid perimeters and the band glows evenly |
| Infill | 15 % gyroid |
| Supports, brim | None |
| Colour changes | 2, with a prime tower |
| Time, material | About 6 h, 170 g (99 g black + 71 g translucent) |

## Post stops

The main PCB and the post have the same 80×80 mm outline, so a fixed stop that catches the post would also block the PCB on its way in. Instead, each corner has a dovetail slot cut into the wall, open at the bottom. After the electronics are in, a printed wedge slides up each slot and the post rests on the wedges at Z = 25 mm.

Nothing sticks into the shaft during assembly, nothing shows from outside, and no threads are involved. The wedge is 10 mm along each wall, so posts with rounded corners still get support.

## Fit report

`build.py` prints a report at the end:

```
Wkładanie elektroniki od dołu: OK                 electronics clear the housing on the way in
KOLIZJE: 0                                        no collisions in the final position
Słupek ↔ lampka: 0.000 mm³                        post clears the housing
klin ↔ lampka: 0.000 mm³                          wedges fit their slots
ścianka za rowkiem: 1.24 mm                       wall left behind each slot
```

These are geometric checks on nominal dimensions. Print tolerances still apply, and this revision has not been test printed yet.

## Rebuilding

```bash
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd build.py
python3 druk.py
python3 druk_makerworld.py
```

`build.py` needs `pcb/step/electronics_assembly.step`. Code comments are in Polish.

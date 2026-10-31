# PCBs

Two boards, designed in EasyEDA Pro. A lamp uses one main board and four LED boards.

| Folder | Contents |
|---|---|
| [`easyeda/`](easyeda/) | Full project for [EasyEDA Pro](https://pro.easyeda.com/). Load it with **Import Professional** on the start page |
| [`gerber/`](gerber/) | Gerber and drill files for the main board and the LED panel |
| [`manufacturing/`](manufacturing/) | BOM and pick-and-place CSV files |
| [`step/`](step/) | 3D model of the assembled electronics in lamp coordinates, used by `enclosure/build.py` for the fit checks |

Schematics as PDF: [main board](../docs/schematic_main.pdf) · [LED board](../docs/schematic_led.pdf)

## Ordering

These are the settings used for the first batch at JLCPCB.

| | Main board (PCB1) | LED panel (PCB2_1) |
|---|---|---|
| Size | 80 × 80 mm | 149.96 × 87.6 mm, 8 boards in a 1 × 8 panel |
| Thickness | 1.6 mm | 1.6 mm |
| Copper | 1 oz | 1 oz |
| Solder mask | Any, first batch green | Black |
| Surface finish | HASL | HASL |
| Assembly | None, soldered by hand | Top side by the factory |

One panel makes 2 lamps.

**In the LED panel BOM, set J1 to "do not place".** It only represents the pads on the board tabs.

The main board has square corners, which is what the housing expects. The current revision needs no corner chamfers.

## Sourcing notes

- The BOM lists manufacturer part numbers. LCSC numbers for the main board are in [`docs/pl/schemat.md`](../docs/pl/schemat.md). Check that each line matches the right part when importing the BOM.
- The Mini560 Pro modules, the ESP32 D1 Mini and the KF235-3.81 terminals are bought separately.
- Check the KF235 footprint against your terminals with a 1:1 printout before soldering. The ESP32 pinout comes from a third-party library, so verify it against your module.

Full part list and net descriptions, in Polish: [`docs/pl/schemat.md`](../docs/pl/schemat.md).

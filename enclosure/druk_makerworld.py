"""
Projekt Bambu Studio dla MakerWorld: makerworld/Fence_post_light_80x80_PETG_AMS.3mf

Uruchom (po druk.py): python3 druk_makerworld.py

MakerWorld odrzuca pliki z własnymi presetami, więc tu są systemowe filamenty Bambu bez zmian, proces systemowy
ze zmianami w different_settings_to_system i brak G-code (MakerWorld tnie sam). Własne profile SUNLU
(temperatury pod ten wydruk) zostają w exports/lampka_slupek_PETG.3mf z druk.py.
"""

import json
import os
import re
import subprocess
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "exports", "bambu")
DST = os.path.join(HERE, "makerworld", "Fence_post_light_80x80_PETG_AMS.3mf")
BAMBU = "/Applications/BambuStudio.app/Contents/MacOS/BambuStudio"
PROFILES = "/Applications/BambuStudio.app/Contents/Resources/profiles/BBL"
PLATE = "Textured PEI Plate"

PRINTER = "Bambu Lab P1S 0.4 nozzle"
PROCESS = "0.20mm Standard @BBL X1C"
FILAMENTS = [("Bambu PETG HF @BBL P1S 0.4 nozzle", "#1A1A1A"), ("Bambu PETG Translucent @BBL X1C", "#DDEEFF")]
OVERRIDES = {
    "wall_loops": "9", "wall_generator": "arachne",
    "top_shell_layers": "5", "bottom_shell_layers": "5",
    "sparse_infill_density": "15%", "skeleton_infill_density": "15%", "skin_infill_density": "15%",
    "sparse_infill_pattern": "gyroid",
    "seam_position": "aligned",
    "enable_support": "0",
    "brim_type": "no_brim",
    "enable_prime_tower": "1", "prime_tower_width": "35",
    "wipe_tower_x": ["205"], "wipe_tower_y": ["40"],
    "outer_wall_speed": ["80", "80"], "inner_wall_speed": ["150", "150"],
    "bridge_speed": ["30", "30"],
    "initial_layer_speed": ["30", "30"], "initial_layer_infill_speed": ["50", "50"],
}

_INDEX = {}
for root, _, fs in os.walk(PROFILES):
    for f in fs:
        if f.endswith(".json"):
            _INDEX.setdefault(f[:-5], os.path.join(root, f))


def flatten(name):
    preset = json.load(open(_INDEX[name]))
    out = {}
    if "inherits" in preset:
        out.update(flatten(preset["inherits"]))
    for inc in preset.get("include", []):
        out.update(flatten(inc))
    out.update({k: v for k, v in preset.items() if k not in ("inherits", "include")})
    return out


def run(args):
    res = subprocess.run([BAMBU, *args], capture_output=True, text=True, timeout=1800)
    if res.returncode:
        raise SystemExit(f"CLI {res.returncode}: {res.stdout[-2000:]} {res.stderr[-2000:]}")


def stats(out_dir):
    plate = json.load(open(os.path.join(out_dir, "result.json")))["sliced_plates"][0]
    return plate["total_predication"] / 60.0, [round(f["total_used_g"], 1) for f in plate["filaments"]]


def gui_project(src, dst, changed):
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            name, data = item.filename, zin.read(item.filename)
            if name.endswith((".gcode", ".gcode.md5")) or name == "Metadata/_rels/model_settings.config.rels":
                continue
            if name == "Metadata/project_settings.config":
                cfg = json.loads(data)
                cfg["different_settings_to_system"][0] = ";".join(sorted(changed))
                cfg["default_filament_colour"] = [""] * len(FILAMENTS)
                data = json.dumps(cfg, indent=4, ensure_ascii=False).encode()
            elif name == "Metadata/slice_info.config":
                data = re.sub(rb"\s*<plate>.*</plate>", b"", data, flags=re.S)
            elif name == "Metadata/model_settings.config":
                data = re.sub(rb'\s*<metadata key="gcode_file"[^>]*/>', b"", data)
            zout.writestr(name, data)


os.makedirs(os.path.dirname(DST), exist_ok=True)
with tempfile.TemporaryDirectory() as tmp:
    system = flatten(PROCESS)
    changed = [k for k, v in OVERRIDES.items() if system.get(k) != v]
    json.dump(flatten(PRINTER), open(f"{tmp}/machine.json", "w"), indent=1, ensure_ascii=False)
    json.dump({**system, **OVERRIDES, "print_settings_id": PROCESS}, open(f"{tmp}/process.json", "w"), indent=1, ensure_ascii=False)
    fils = []
    for i, (name, colour) in enumerate(FILAMENTS):
        fils.append(f"{tmp}/fil{i}.json")
        json.dump({**flatten(name), "filament_colour": [colour]}, open(fils[-1], "w"), indent=1, ensure_ascii=False)

    sliced, check = f"{tmp}/sliced", f"{tmp}/check"
    os.makedirs(sliced)
    os.makedirs(check)
    run(["--load-settings", f"{tmp}/machine.json;{tmp}/process.json", "--load-filaments", ";".join(fils),
         "--load-assemble-list", os.path.join(SRC, "assemble.json"), "--assemble", "--curr-bed-type", PLATE,
         "--slice", "0", "--outputdir", sliced, "--export-3mf", "sliced.3mf"])
    minutes, grams = stats(sliced)
    gui_project(f"{sliced}/sliced.3mf", DST, changed)
    run(["--slice", "0", "--outputdir", check, "--export-3mf", "check.3mf", DST])
    re_minutes, re_grams = stats(check)

with zipfile.ZipFile(DST) as z:
    cfg = json.loads(z.read("Metadata/project_settings.config"))
    assert not [n for n in z.namelist() if "gcode" in n], "G-code w projekcie"
    assert b"<plate>" not in z.read("Metadata/slice_info.config")
    assert b"gcode_file" not in z.read("Metadata/model_settings.config")
assert cfg["print_settings_id"] == PROCESS and cfg["printer_settings_id"] == PRINTER
assert cfg["filament_settings_id"] == [f for f, _ in FILAMENTS]
assert cfg["filament_colour"] == [c for _, c in FILAMENTS] and cfg["curr_bed_type"] == PLATE
assert cfg["inherits_group"] == [""] * 4 and cfg["wall_loops"] == "9"
assert abs(re_minutes - minutes) < 5 and all(abs(a - b) < 1 for a, b in zip(re_grams, grams)), "ponowne cięcie daje inny wynik"
print(f"{minutes:.0f} min, {grams} g | ponownie: {re_minutes:.0f} min, {re_grams} g | {os.path.getsize(DST) // 1024} KB")
print("płukanie:", cfg["flush_volumes_matrix"])
print("zmiany:", cfg["different_settings_to_system"][0])

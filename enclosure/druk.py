"""
Projekt Bambu Studio (P1S + AMS) dla lampki: exports/lampka_slupek_PETG.3mf

Uruchom (po build.py): python3 druk.py

- STL z exports/ obrócone 180° wokół X: daszek na stole (bez podpór).
- 3 części jednego obiektu: czarny daszek / transparentny pas / czarny dół → AMS zmienia kolor 2×.
- Obok 4 kliny-ograniczniki: drukują się w warstwach daszka, bez dodatkowych zmian koloru.
- Profile = fabryczne Bambu (P1S 0.4, 0.20mm Standard @BBL X1C, SUNLU PETG @BBL X1C) + delty niżej.
"""

import json
import os
import shutil
import struct
import subprocess
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.join(HERE, "exports")
OUT_DIR = os.path.join(EXP, "bambu")
OUT_3MF = os.path.join(EXP, "lampka_slupek_PETG.3mf")
BAMBU = "/Applications/BambuStudio.app/Contents/MacOS/BambuStudio"
PROFILES = "/Applications/BambuStudio.app/Contents/Resources/profiles/BBL"
H_TOTAL = 83.0

PARTS = [  # (STL, filament 1=czarny 2=transparent)
    ("lampka_czarny_daszek.stl", 1),
    ("lampka_pas_transparentny.stl", 2),
    ("lampka_czarny_dol.stl", 1),
]

WEDGES = "lampka_kliny_x4.stl"   # 4 kliny-ograniczniki obok lampki: wysokość daszka, ten sam czarny filament

PROCESS = {
    "type": "process", "from": "User", "inherits": "0.20mm Standard @BBL X1C",
    "name": "0.20mm Lampka PETG rozproszony", "print_settings_id": "0.20mm Lampka PETG rozproszony",
    "compatible_printers": ["Bambu Lab P1S 0.4 nozzle"],
    "layer_height": "0.2",
    # ścianka 4 mm w całości z obwodów (0,42 + 8×0,45 ≥ 4) — bez wzoru wypełnienia prześwitującego w pasie
    "wall_loops": "9",
    "wall_generator": "arachne",
    "top_shell_layers": "5", "bottom_shell_layers": "5",
    "sparse_infill_density": "15%", "sparse_infill_pattern": "gyroid",
    "seam_position": "aligned",           # szew ląduje w narożnikach
    "enable_support": "0",
    "brim_type": "no_brim",               # daszek 100×100 na stole trzyma się sam
    "enable_prime_tower": "1", "prime_tower_width": "35",
    "wipe_tower_x": ["205"], "wipe_tower_y": ["40"],   # fabryczne (165, 250) wychodzi poza stół
    # PETG: wolniej niż fabryczne 200/300 — równomierna ścianka = równe światło
    "outer_wall_speed": ["80", "80"], "inner_wall_speed": ["150", "150"],
    "bridge_speed": ["30", "30"],         # mostki nad rowkami wentylacji (22 mm)
    "initial_layer_speed": ["30", "30"], "initial_layer_infill_speed": ["50", "50"],
}

FIL_BASE = {"type": "filament", "from": "User", "inherits": "SUNLU PETG @BBL X1C",
            "compatible_printers": ["Bambu Lab P1S 0.4 nozzle"],
            # stół teksturowany 75 °C (Twoje profile PETG), wachlarz off przez 3 warstwy
            "textured_plate_temp": ["75"], "textured_plate_temp_initial_layer": ["75"],
            "hot_plate_temp": ["75"], "hot_plate_temp_initial_layer": ["75"],
            "close_fan_the_first_x_layers": ["3"]}
FILAMENTS = [
    dict(FIL_BASE, name="SUNLU PETG czarny - lampka", filament_settings_id=["SUNLU PETG czarny - lampka"],
         filament_colour=["#1A1A1A"]),
    dict(FIL_BASE, name="SUNLU PETG transparent - lampka", filament_settings_id=["SUNLU PETG transparent - lampka"],
         filament_colour=["#DDEEFF"],
         nozzle_temperature=["250", "250"]),   # +5 °C: lepsze sklejenie warstw = jednolity pas
]


def flip_stl(src, dst):
    """Obrót 180° wokół X + podniesienie: (x, y, z) → (x, −y, H−z). Binarny lub ASCII STL → binarny."""
    data = open(src, "rb").read()
    tris = []
    if data[:5] == b"solid" and b"facet" in data[:300]:
        vs = [tuple(map(float, l.split()[1:4])) for l in data.decode().splitlines() if l.strip().startswith("vertex")]
        tris = [vs[k:k + 3] for k in range(0, len(vs), 3)]
    else:
        n = struct.unpack("<I", data[80:84])[0]
        for k in range(n):
            f = struct.unpack("<12f", data[84 + 50 * k: 84 + 50 * k + 48])
            tris.append([f[3:6], f[6:9], f[9:12]])
    with open(dst, "wb") as o:
        o.write(b"lampka".ljust(80, b" ") + struct.pack("<I", len(tris)))
        for t in tris:
            o.write(struct.pack("<3f", 0, 0, 0))
            for x, y, z in t:
                o.write(struct.pack("<3f", x, -y, H_TOTAL - z))
            o.write(b"\0\0")
    return len(tris)


_INDEX = {}
for root, _, fs in os.walk(PROFILES):
    for f in fs:
        if f.endswith(".json"):
            _INDEX.setdefault(f[:-5], os.path.join(root, f))


def flatten(preset):
    """Rozwija inherits/include z profili systemowych (CLI BS 2.x crashuje na dziedziczeniu z podkatalogów)."""
    out = {}
    if "inherits" in preset:
        out.update(flatten(json.load(open(_INDEX[preset["inherits"]]))))
    for inc in preset.get("include", []):
        out.update(flatten(json.load(open(_INDEX[inc]))))
    out.update({k: v for k, v in preset.items() if k not in ("inherits", "include")})
    return out


os.makedirs(OUT_DIR, exist_ok=True)
objs = []
for stl, fil in PARTS:
    dst = os.path.join(OUT_DIR, stl)
    print(stl, flip_stl(os.path.join(EXP, stl), dst), "trójkątów")
    objs.append({"path": dst, "count": 1, "filaments": [fil], "assemble_index": [0],
                 "pos_x": [128.0], "pos_y": [128.0], "pos_z": [0.0]})
shutil.copy(os.path.join(EXP, WEDGES), os.path.join(OUT_DIR, WEDGES))
objs.append({"path": os.path.join(OUT_DIR, WEDGES), "count": 1, "filaments": [1], "assemble_index": [0],
             "pos_x": [190.0], "pos_y": [90.0], "pos_z": [0.0]})
json.dump({"plates": [{"plate_name": "lampka", "need_arrange": False, "objects": objs}]},
          open(os.path.join(OUT_DIR, "assemble.json"), "w"), indent=1)

files = {"machine.json": {"inherits": "Bambu Lab P1S 0.4 nozzle"},
         "process.json": PROCESS, "fil_czarny.json": FILAMENTS[0], "fil_transparent.json": FILAMENTS[1]}
for n, d in files.items():
    flat = flatten(d)
    if n != "machine.json":
        flat["from"] = "User"
    json.dump(flat, open(os.path.join(OUT_DIR, n), "w"), indent=1, ensure_ascii=False)

machine = os.path.join(OUT_DIR, "machine.json")
cmd = [BAMBU, "--debug", "1",
       "--load-settings", f"{machine};{os.path.join(OUT_DIR, 'process.json')}",
       "--load-filaments", f"{os.path.join(OUT_DIR, 'fil_czarny.json')};{os.path.join(OUT_DIR, 'fil_transparent.json')}",
       "--load-assemble-list", os.path.join(OUT_DIR, "assemble.json"),
       "--assemble", "--curr-bed-type", "Textured PEI Plate",
       "--slice", "0", "--export-3mf", OUT_3MF]   # cięcie = test, że projekt jest drukowalny
res = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
print("CLI exit:", res.returncode)
if res.returncode:
    print(res.stdout[-3000:], res.stderr[-3000:])

# --- weryfikacja: ustawienia w projekcie ---
with zipfile.ZipFile(OUT_3MF) as z:
    cfg = json.loads(z.read("Metadata/project_settings.config"))
    for k in ("printer_settings_id", "print_settings_id", "filament_settings_id", "filament_colour", "curr_bed_type",
              "layer_height", "wall_loops", "nozzle_temperature", "textured_plate_temp", "enable_prime_tower",
              "enable_support", "flush_volumes_matrix", "outer_wall_speed"):
        print(f"  {k} = {cfg.get(k)}")
    for n in z.namelist():
        if n.endswith(".gcode"):
            print("  plik:", n, z.getinfo(n).file_size)
    print(z.read("Metadata/slice_info.config").decode())

"""Agent:
schreibe mir hier code welcher aus den files in s1p_results aus den files values.py ein
file generiert:

table_results.typ

da ist eine tabelle drin welche ich in typst imporiren kann.

Spalten
Kopplung angepasst: / zu viel / zu wenig
VNA kalibriert: Antennenfusspunkt / beim VNA
Resonanzfrequenz MHz auf 6 stellen nach komma
BSWR 2.62 Hz auf 0 stellen nach komma
Dämpfung Kabel dB auf 3 stellen nach komma
Laufzeit Kabel ns auf 1 stellen nach komma

files mit 50 ohm sind angepasst
files mit 80 ohm sind zu gross
files mit 30 ohm sind zu wenig



20260807_2311_peter_tubby_30_ohm_fusspunkt_10MHz_values.py	28482	0.005	5.21	0.943
20260807_2311_peter_tubby_30_ohm_kabel_10MHz_values.py	28259	0.354	62.59	0.928
20260807_2315_peter_tubby_80_ohm_fusspunkt_10MHz_values.py	28364	0.007	8.31	0.943
20260807_2315_peter_tubby_80_ohm_kabel_10MHz_values.py	28339	0.383	67.05	0.954
20260807_2317_peter_tubby_50_ohm_kabel_10MHz_values.py	28367	0.357	65.50	0.998
20260807_2318_peter_tubby_50_ohm_fusspunkt_10MHz_values.py



reihenfolge: zu erst Antennenfusspunkt ohm aufsteigend dann beim VNA ohm aufsteigend


"""

import importlib.util
import pathlib
import re

S1P_RESULTS = pathlib.Path(__file__).parent / "s1p_results"
OUTPUT = pathlib.Path(__file__).parent / "table_results.typ"


def load_values(path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None
    mod = importlib.util.module_from_spec(spec)
    assert mod is not None
    spec.loader.exec_module(mod)
    return mod


def kopplung(stem: str) -> str:
    if "_50_ohm_" in stem:
        return "50 Ω"
    if "_80_ohm_" in stem:
        return "zu viel"
    if "_30_ohm_" in stem:
        return "zu wenig"
    return "?"


def vna_kalibriert(stem: str) -> str:
    if "_fusspunkt_" in stem:
        return "Fuss- \\\npunkt"
    if "_kabel_" in stem:
        return "beim VNA"
    return "?"


def build_table() -> str:
    def sort_key(f: pathlib.Path):
        ohm_match = re.search(r"_(\d+)_ohm_", f.stem)
        ohm = int(ohm_match.group(1)) if ohm_match else 0
        vna_order = 0 if "_fusspunkt_" in f.stem else 1
        return (vna_order, ohm)

    files = sorted(S1P_RESULTS.glob("*_values.py"), key=sort_key)
    rows = []
    for f in files:
        if f.name == "__init__.py":
            continue
        mod = load_values(f)
        m = mod.model
        rows.append(
            (
                kopplung(f.stem),
                vna_kalibriert(f.stem),
                f"{m.f0_Hz / 1e6:.3f}",
                f"{m.BSWR2_62_Hz:.0f}",
                f"{mod.swr_values.swr_min:.2f}",
                f"{m.alpha_db:.3f}",
                f"{m.tau_s * 1e9:.1f}",
            )
        )

    header = (
        "[Kopp-\\\nlung]",
        "[VNA cal]",
        "[f\\\n(MHz)]",
        '[$B_"SWR 2.62"$\\\n(Hz)]',
        "[SWR min]",
        "[Att.\\\n(dB)]",
        "[Delay\\\n(ns)]",
    )

    def fmt_row(cells):
        return "  " + ", ".join(f"[{c}]" for c in cells) + ","

    lines = [
        f"// Generiert von {pathlib.Path(__file__).name} -- nicht manuell bearbeiten",
        "#{",
        "  set text(size: 9pt)",
        "  table(",
        "    columns: (auto, auto, auto, auto, auto, auto, auto),",
        "    inset: (x: 4pt, y: 3pt),",
        "    table.header(",
        "      " + ", ".join(header) + ",",
        "    ),",
    ]
    for row in rows:
        lines.append("  " + fmt_row(row))
    lines.append("  )")
    lines.append("}")
    return "\n".join(lines) + "\n"


OUTPUT.write_text(build_table(), encoding="utf-8")
print(f"Geschrieben: {OUTPUT}")

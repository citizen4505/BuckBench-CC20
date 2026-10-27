# Nástroje

`schgen/` generuje KiCad schéma ze skriptu:

```
cd tools/schgen
python3 build.py                      # zapíše ../../hardware/buckbench.kicad_sch
kicad-cli sch export netlist -o /tmp/buckbench.net ../../hardware/buckbench.kicad_sch
kicad-cli sch export pdf -o ../../hardware/buckbench.pdf ../../hardware/buckbench.kicad_sch
```

`verify.py` porovná zamýšlené spoje (`netpins.json`, který vytvoří `build.py`) s netlistem z KiCadu.

Schéma můžeš upravovat i přímo v KiCadu – pak už ale generátor nepouštěj, přepsal by ruční změny.

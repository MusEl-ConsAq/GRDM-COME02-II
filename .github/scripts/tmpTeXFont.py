#!/usr/bin/env python3
import yaml

# File di input e output
config_file = "styles/config.yml"
output_file = "styles/config_fonts.tex"

try:
    with open(config_file, "r") as f:
        cfg = yaml.safe_load(f)
except FileNotFoundError:
    print(f"Errore: '{config_file}' non trovato.", file=sys.stderr)
    sys.exit(1)
except yaml.YAMLError as e:
    print(f"Errore leggendo YAML: {e}", file=sys.stderr)
    sys.exit(1)

# Prendi il font dal YAML in modo sicuro
font_value = cfg.get("environment", {}).get("font")
if not font_value or not isinstance(font_value, str):
    font = "liberation"
else:
    font = font_value.lower()

# Validazione base
if font not in ["arial", "liberation"]:
    print(f"Font '{font}' non riconosciuto, uso 'liberation' come default.", file=sys.stderr)
    font = "liberation"

# Scrivi il file .tex
with open(output_file, "w") as f:
    f.write(f"\\def\\chosenfont{{{font}}}\n")

print(f"File '{output_file}' generato con \\chosenfont = '{font}'")

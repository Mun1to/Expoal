"""Empaqueta assets/icon-256.png en assets/expoal.ico (entrada PNG, válida en Vista+)."""
import struct
from pathlib import Path

root = Path(__file__).parent.parent
png = (root / "assets" / "icon-256.png").read_bytes()

# Cabecera ICONDIR + una entrada ICONDIRENTRY (0 en ancho/alto significa 256)
header = struct.pack("<HHH", 0, 1, 1)
entry = struct.pack("<BBBBHHII", 0, 0, 0, 0, 1, 32, len(png), 6 + 16)
(root / "assets" / "expoal.ico").write_bytes(header + entry + png)
print("assets/expoal.ico generado")

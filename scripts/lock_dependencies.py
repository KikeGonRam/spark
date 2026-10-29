"""Fija una resolución ya instalada usando hashes publicados por PyPI.

No resuelve versiones ni instala paquetes. Revisar la resolución y volver a validar
el lock después de generarlo. Solo admite paquetes name==version de PyPI.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
from urllib.request import urlopen


def package_hashes(requirement):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+==[A-Za-z0-9_.+!-]+", requirement):
        raise ValueError("La resolución solo debe contener paquetes name==version.")
    name, version = requirement.split("==", 1)
    with urlopen(f"https://pypi.org/pypi/{name}/{version}/json", timeout=30) as response:
        metadata = json.load(response)
    hashes = sorted({item["digests"]["sha256"] for item in metadata["urls"] if not item.get("yanked")})
    if not hashes or any(not re.fullmatch(r"[a-f0-9]{64}", value) for value in hashes):
        raise ValueError("PyPI no proporcionó artefactos válidos para " + name)
    return requirement, hashes


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze-file", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    requirements = sorted(set(line.strip() for line in args.freeze_file.read_text(encoding="utf-8-sig").splitlines()
                              if line.strip() and not line.startswith("#")))
    with ThreadPoolExecutor(max_workers=8) as pool:
        packages = list(pool.map(package_hashes, requirements))
    lines = ["# Resolución revisada de Python 3.12; hashes de artefactos publicados por PyPI.",
             "# Generar con scripts/lock_dependencies.py; instalar con --require-hashes.", ""]
    continuation = " " + chr(92)
    for requirement, hashes in packages:
        lines.append(requirement + continuation)
        lines.extend("    --hash=sha256:" + value + (continuation if i < len(hashes) - 1 else "")
                     for i, value in enumerate(hashes))
        lines.append("")
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Lock generado: {len(packages)} paquetes.")


if __name__ == "__main__":
    main()

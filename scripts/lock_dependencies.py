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
    return requirement, hashes, metadata["urls"]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, choices=("ci", "dashboard"))
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    inputs = root / ".dependency-locks"
    if args.profile == "ci":
        freeze_file, output = inputs / "ci.freeze", root / "requirements-ci.lock"
    else:
        freeze_file, output = inputs / "dashboard.freeze", root / "requirements-dashboard.lock"
    if not freeze_file.resolve().is_relative_to(inputs.resolve()) or output.resolve().parent != root:
        raise ValueError("Los archivos deben permanecer en las rutas locales de dependencias.")
    requirements = sorted(set(line.strip() for line in freeze_file.read_text(encoding="utf-8-sig").splitlines()
                              if line.strip() and not line.startswith("#")))
    with ThreadPoolExecutor(max_workers=8) as pool:
        packages = list(pool.map(package_hashes, requirements))
    lines = ["# Resolución revisada de Python 3.12; hashes de artefactos publicados por PyPI.",
             "# Generar con scripts/lock_dependencies.py; instalar con --require-hashes.", ""]
    continuation = " " + chr(92)
    for requirement, hashes, _files in packages:
        lines.append(requirement + continuation)
        lines.extend("    --hash=sha256:" + value + (continuation if i < len(hashes) - 1 else "")
                     for i, value in enumerate(hashes))
        lines.append("")
    output.write_text("\n".join(lines), encoding="utf-8")
    if args.profile == "dashboard":
        manifest = ['lock-version = "1.0"', 'created-by = "urbanblade-lock-dependencies"',
                    'requires-python = "==3.12.*"',
                    'environments = ["sys_platform == \'linux\' and platform_machine == \'x86_64\'"]', '']
        for requirement, _hashes, files in packages:
            name, version = requirement.split("==", 1)
            name = re.sub(r"[-_.]+", "-", name).lower()
            manifest.extend(['[[packages]]', 'name = ' + json.dumps(name),
                             'version = ' + json.dumps(version)])
            for item in sorted(files, key=lambda entry: entry["filename"]):
                if item.get("yanked"):
                    continue
                if item["packagetype"] == "bdist_wheel":
                    manifest.append('[[packages.wheels]]')
                elif name == "pyspark" and item["packagetype"] == "sdist":
                    manifest.append('[packages.sdist]')
                else:
                    continue
                manifest.extend(['name = ' + json.dumps(item["filename"]),
                                 'url = ' + json.dumps(item["url"]), 'size = ' + str(item["size"]),
                                 'hashes = {sha256 = ' + json.dumps(item["digests"]["sha256"]) + '}', ''])
        pylock = root / "pylock.toml"
        if pylock.resolve().parent != root:
            raise ValueError("pylock debe permanecer en la raíz del proyecto.")
        pylock.write_text("\n".join(manifest), encoding="utf-8")
    print(f"Lock generado: {len(packages)} paquetes.")


if __name__ == "__main__":
    main()

"""Comprobaciones de estructura y archivos privados sin leer sus contenidos."""

from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def main():
    files = subprocess.check_output(
        ['git', 'ls-files', '--cached', '--others', '--exclude-standard'], cwd=ROOT, text=True
    ).splitlines()
    invalid = []
    for filename in files:
        path = ROOT / filename
        if not path.is_file():
            continue  # Local refactors can contain unstaged deletions; GitHub checks the resulting tree.
        name = path.name.lower()
        if ((name == '.env' or name.startswith('.env.')) and name != '.env.example') or path.suffix.lower() in {
            '.pem', '.key', '.p12', '.jks', '.keystore', '.parquet', '.joblib', '.pkl'
        }:
            invalid.append(filename)
        if re.search(r'(?i)service.?account|adminsdk|accesskeys|credentials.*\.json$', filename):
            invalid.append(filename)
    required = ['README.md', 'SECURITY.md', 'CONTRIBUTING.md', 'LICENSE', 'LICENSING.md',
                'docs/arquitectura.md', 'docs/desarrollo.md', 'docs/operacion.md',
                'dashboard/app.py', 'pipelines/publicar_insights.py']
    missing = [filename for filename in required if not (ROOT / filename).is_file()]
    for path in (ROOT / '.github/workflows').glob('*.yml'):
        for uses in re.findall(r'^\s*-?\s*uses:\s*([^\s#]+)', path.read_text(encoding='utf-8'), re.MULTILINE):
            if not uses.startswith('./') and not re.fullmatch(r'[\w.-]+/[\w.-]+@[a-f0-9]{40}', uses):
                invalid.append(str(path.relative_to(ROOT)) + ': Action sin SHA completo')
    documents = list(ROOT.glob('*.md')) + list((ROOT / 'docs').rglob('*.md'))
    for document in documents:
        for target in re.findall(r'\]\(([^)]+)\)', document.read_text(encoding='utf-8')):
            target = target.split('#')[0].split(' "')[0]
            if not target or ':' in target or target.startswith('/'):
                continue
            if not (document.parent / target).exists():
                invalid.append(str(document.relative_to(ROOT)) + ': enlace local inexistente: ' + target)
    if invalid or missing:
        print('Archivos o referencias a revisar:', sorted(set(invalid)))
        print('Rutas obligatorias ausentes:', missing)
        return 1
    print('Estructura, enlaces, Actions fijadas y nombres de archivos privados: correctos.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

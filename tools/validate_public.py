"""Validate the public snapshot without contacting apps or external services."""
from pathlib import Path
import json
import re
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]


def validate():
    errors = []
    required = ['README.md', 'AGENTS.md', 'LICENSE', 'NOTICE', 'THIRD_PARTY_NOTICES.md',
                'prompts/START_HERE.md', 'docs/SETUP.md', 'workflows/PIPELINE_WORKFLOW.md']
    for name in required:
        if not (ROOT / name).is_file():
            errors.append('Missing entry: ' + name)
    private_parts = {'projects', 'handoffs', 'tasks', 'local', '.git', '__pycache__', '.venv', 'node_modules'}
    private_extensions = {'.rvt', '.rfa', '.rte', '.rft', '.blend', '.skp', '.sqlite', '.sqlite3', '.db'}
    checked = 0
    for path in ROOT.rglob('*'):
        relative = path.relative_to(ROOT)
        if any(part in private_parts for part in relative.parts) or not path.is_file():
            continue
        if path.suffix.lower() in private_extensions:
            errors.append('Private model/database: ' + relative.as_posix())
        if path.suffix != '.md':
            continue
        checked += 1
        text = re.sub(r'```.*?```', '', path.read_text(encoding='utf-8-sig'), flags=re.S)
        for match in re.finditer(r'\]\(([^)]+)\)', text):
            url = match.group(1).split(' "')[0].strip('<>')
            if not url or re.match(r'^[a-z][a-z+.-]*:', url, re.I) or url.startswith(('#', '/', '[', '<')):
                continue
            target = unquote(url.split('#')[0])
            if not (path.parent / target).exists():
                errors.append(f'{relative.as_posix()}: broken link {url}')
    notice = (ROOT / 'NOTICE').read_text(encoding='utf-8') if (ROOT / 'NOTICE').exists() else ''
    if 'Required Notice:' not in notice:
        errors.append('Missing Required Notice')
    return {'markdown_files': checked, 'errors': errors}


if __name__ == '__main__':
    result = validate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(bool(result['errors']))

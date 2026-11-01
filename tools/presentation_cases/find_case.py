"""Find a few credited presentation references; does not download images or design a board."""
import argparse
import json
from pathlib import Path
import re

BASE = Path(__file__).resolve().parents[2] / 'knowledge' / 'presentation-cases'


def entries():
    return json.loads((BASE / 'catalog.json').read_text(encoding='utf-8'))['entries']


def search(query, limit=3):
    words = [w.casefold() for w in re.split(r'\s+', query.strip()) if w]
    hits = []
    for entry in entries():
        content = ' '.join([entry['title'], *entry['tags'], entry['format']]).casefold()
        score = sum(1 for word in words if word in content)
        if score:
            hits.append({**entry, 'score': score})
    return sorted(hits, key=lambda e: (-e['score'], e['id']))[:limit]


def check():
    errors, ids = [], set()
    for entry in entries():
        if entry.get('id') in ids:
            errors.append('duplicate id: ' + entry['id'])
        ids.add(entry.get('id'))
        for key in ['id', 'title', 'author', 'source', 'kind', 'format', 'tags', 'visual_review', 'lesson', 'limits', 'license', 'card']:
            if not entry.get(key):
                errors.append(f"{entry.get('id')}: missing {key}")
        path = (BASE / entry.get('card', '')).resolve()
        if not path.is_relative_to(BASE) or not path.is_file():
            errors.append(f"{entry.get('id')}: missing or invalid card")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--query')
    parser.add_argument('--limit', type=int, default=3)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    if args.check:
        errors = check()
        print(json.dumps({'entries': len(entries()), 'errors': errors}, ensure_ascii=False))
        return bool(errors)
    if not args.query or args.limit < 1:
        parser.error('provide --query and a positive --limit')
    hits = search(args.query, args.limit)
    if args.json:
        print(json.dumps(hits, ensure_ascii=False, indent=2))
    elif not hits:
        print('没有匹配参考；需要新查原始来源，不用无关结果凑数。')
    else:
        for hit in hits:
            print(f"{hit['id']} | {hit['title']} | {hit['kind']}")
            print(f"  来源: {hit['source']}\n  方法: {hit['lesson']}\n  限制: {hit['limits']}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

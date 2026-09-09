import json
from pathlib import Path

# Patch Stellaluna book_vocab.json to add vocab_words and all_words if missing

def main():
    p = Path('assets/themes/stellaluna/book_vocab.json')
    if not p.exists():
        print('ERROR: file not found:', p)
        return 1
    try:
        data = json.loads(p.read_text(encoding='utf-8'))
    except Exception as e:
        print('ERROR: invalid JSON:', e)
        return 1

    words = [
        'bat','bird','branch','cave','mango','moon','moth','nest','owl','wing','night'
    ]

    changed = False
    if not isinstance(data, dict):
        print('ERROR: root is not an object')
        return 1
    if not data.get('vocab_words'):
        data['vocab_words'] = words
        changed = True
    if not data.get('all_words'):
        data['all_words'] = words
        changed = True

    if changed:
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print('OK: updated vocab_words/all_words in', p)
    else:
        print('OK: vocab already present')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())

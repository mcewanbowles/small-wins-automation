import json
vocab = json.loads(open(r'assets/themes/llama_llama_back_to_school/book_vocab.json', encoding='utf-8').read())
print('Title:', vocab.get('title'))
print()
print('Yes/No Questions:')
for i, q in enumerate(vocab.get('yes_no_questions', [])):
    print(f'  {i}: q={q.get("question")!r}  key={q.get("image_key")!r}  ans={q.get("answer")!r}')
print()
print('Icon search terms:')
for k, v in (vocab.get('icon_search_terms') or {}).items():
    print(f'  {k}: {v}')

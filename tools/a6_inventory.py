"""Read historical sabotage cases without executing their destructive runners."""
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
cases = []
for script in sorted((ROOT / 'engine').glob('sabotage_*.py')):
    tree = ast.parse(script.read_text(encoding='utf-8'))
    assignment = next((node for node in tree.body if isinstance(node, ast.Assign)
                       and any(isinstance(target, ast.Name) and target.id == 'SABOTAGEN'
                               for target in node.targets)), None)
    if assignment is None:
        continue
    for index, (name, file, old, new) in enumerate(ast.literal_eval(assignment.value), 1):
        source = (ROOT / 'engine' / file).read_text(encoding='utf-8')
        cases.append(dict(id=f'{script.stem}:{index:03d}', script=script.name,
                          name=name, file=file, old=old, new=new,
                          matches=source.count(old)))
if __name__ == '__main__':
    from collections import Counter
    print(json.dumps(dict(total=len(cases), by_script=Counter(x['script'] for x in cases),
                          missing=[x for x in cases if not x['matches']],
                          multiple=[x for x in cases if x['matches'] > 1]),
                     ensure_ascii=False, indent=2))

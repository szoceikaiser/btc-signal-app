"""Fresh-process checkpoint reader. No writes, network or signal delivery."""
import gzip
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'engine'))
import execution_v1 as v
import strategy_core as sc

with gzip.open(sys.argv[1], 'rt', encoding='utf-8') as stream:
    payload = json.load(stream)
data = json.loads(Path(payload['input_path']).read_text(encoding='utf-8'))
result = v.resume_v1([sc.Candle(**c) for c in data['candles']],
                     [sc.FlowPoint(**f) for f in data['flow']], payload['checkpoint'])
digest = hashlib.sha256(json.dumps(result, sort_keys=True, allow_nan=False).encode()).hexdigest()
print(json.dumps(dict(result='PASS', sha256=digest)))

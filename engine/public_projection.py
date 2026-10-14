"""Explicit public field selection. No transport, commands, config or receipts."""
import math
from production_contract import canonical

NUMBER = 'number'
TEXT = 'text'
ZONES = {k: NUMBER for k in ('impuls_start','impuls_ende','impuls_start_ts','impuls_ende_ts',
    'level_05','gp_upper','gp_lower','level_0786','invalidation','ext1','ext2','abstand_pct')}
ZONES['richtung'] = TEXT
RUNG = {'preis': NUMBER, 'zone': [NUMBER], 'tranche': NUMBER, 'was': TEXT}
STATE = {'direction': TEXT, 'pos_state': TEXT, 'last_signal_ts': NUMBER,
         'last_close': NUMBER, 'updated_at': TEXT, 'zones': ZONES, 'zonen_vorschau': ZONES,
         'widerstand': {k: NUMBER for k in ('gp_von','gp_bis','ausbruch')},
         'plan': {'richtung': TEXT, 'anteil_pct': NUMBER, 'einstand': NUMBER, 'kurs': NUMBER,
                  'stop': {'preis': NUMBER, 'grund': TEXT},
                  'nachkauf': [RUNG], 'teilgewinn': [RUNG]}}
SIGNAL = {'ts': NUMBER, 'price': NUMBER, 'type': TEXT, 'tag': TEXT,
          'tranche_pct': NUMBER, 'reason': TEXT, 'signal_reason': TEXT,
          'signal_id': TEXT, 'id': TEXT, 'sequence': NUMBER}


def select(value, schema):
    if value is None:
        return None
    if schema == NUMBER:
        if type(value) not in (int, float) or not math.isfinite(value):
            raise ValueError('Invalid public number')
        return value
    if schema == TEXT:
        if not isinstance(value, str) or len(value) > 1024:
            raise ValueError('Invalid public label')
        return value
    if isinstance(schema, list):
        if not isinstance(value, list) or len(value) > 10000:
            raise ValueError('Invalid public list')
        return [select(v, schema[0]) for v in value]
    if not isinstance(value, dict):
        raise ValueError('Invalid public object')
    return {k: select(value[k], s) for k, s in schema.items() if k in value}


def project(snapshot, observed_ms, pins):
    engine = snapshot['engine']
    # Only the signal rows are selected from the private delivery journal.
    value = {'schema': 'btc-public-projection-v1', 'observed_ms': observed_ms,
             'signal_asof_ms': engine['last_signal_ts'], 'pins': pins,
             'state': select(engine, STATE),
             'signals': {'signals': select(engine['_delivery']['signals']['signals'], [SIGNAL])}}
    body = canonical(value).encode()
    if len(body) > 750*1024:
        raise ValueError('Public projection byte budget exceeded')
    return body

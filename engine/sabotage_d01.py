"""D01-Mutationen im Speicher, keine Datei und kein Netzwerk werden veraendert."""
import inspect
import json
import backtest as bt
import test_d01_kerzenschluss as tests


def main():
    mutations = [
        ('aufbau_filter_entfernt', 'build_series',
         'int(k[0]) + CANDLE_MS <= cutoff', 'True'),
        ('binance_ende_minus_1_als_abgeschlossen', 'fetch_candles_range',
         'int(k[0]) + CANDLE_MS <= end_ms', 'int(k[6]) <= end_ms'),
        ('gespeicherter_stichtag_ignoriert', 'closed_series',
         'c.ts + CANDLE_MS <= end_ms', 'c.ts + CANDLE_MS <= int(time.time() * 1000)'),
        ('flow_nicht_mitgeschnitten', 'closed_series',
         '[f for _, f in pairs]', 'list(flow)'),
        ('schlussgrenze_exklusiv', 'build_series',
         'int(k[0]) + CANDLE_MS <= cutoff', 'int(k[0]) + CANDLE_MS < cutoff'),
        ('halbfenster_nach_anfang', 'closed_series',
         'c.ts + CANDLE_MS <= end_ms', 'c.ts <= end_ms'),
    ]
    results = {}
    for label, target, old, new in mutations:
        original = getattr(bt, target)
        source = inspect.getsource(original)
        assert source.count(old) == 1, label
        ns = bt.__dict__  # Test-Mocks (Uhr/API) gelten auch fuer die Mutation.
        exec(compile(source.replace(old, new), '<D01-' + label + '>', 'exec'), ns)
        setattr(bt, target, ns[target])
        caught = []
        try:
            for name, fn in vars(tests).items():
                if name.startswith('test_') and callable(fn):
                    try:
                        fn()
                    except AssertionError:
                        caught.append(name)
            assert caught, 'Sabotage ueberlebt: ' + label
            results[label] = caught
        finally:
            setattr(bt, target, original)
    print(json.dumps(results, indent=2))
    print(f'{len(results)}/{len(mutations)} Sabotagen erkannt')


if __name__ == '__main__':
    main()

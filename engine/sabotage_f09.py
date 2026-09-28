"""Gezielte F09-Gegenproben im Speicher; keine Produktionsdatei wird veraendert."""
import inspect
import json

import backtest
import test_f09_wiederanlage as tests


def main():
    original = backtest.simulate
    source = inspect.getsource(original)
    guard = 'if sell > 0 and 0 < units - sell <= 8 * math.ulp(peak_units):'
    reset = 'alloc, peak_units, l_avg = cash * deploy_pct, 0.0, 0.0'
    mutations = {
        'rundungsabgleich_entfernt': (guard, 'if False:'),
        'absolute_grenze_loescht_echten_kleinbestand': (
            guard, 'if sell > 0 and 0 < units - sell < 1e-12:'),
        'alter_hoechstbestand_bleibt_im_neuen_zyklus': (
            reset, 'alloc, l_avg = cash * deploy_pct, 0.0'),
    }
    result = {}
    try:
        for label, (old, new) in mutations.items():
            assert source.count(old) == 1, f'{label}: Vorlage muss genau einmal treffen'
            namespace = dict(backtest.__dict__)
            exec(compile(source.replace(old, new), f'<F09-{label}>', 'exec'), namespace)
            backtest.simulate = namespace['simulate']
            caught = []
            for name, fn in sorted(vars(tests).items()):
                if name.startswith('test_') and callable(fn):
                    try:
                        fn()
                    except AssertionError:
                        caught.append(name)
            assert caught, f'Sabotage ueberlebt: {label}'
            result[label] = caught
    finally:
        backtest.simulate = original
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f'{len(result)} von {len(mutations)} Sabotagen erkannt; Produktionsdatei unveraendert.')


if __name__ == '__main__':
    main()

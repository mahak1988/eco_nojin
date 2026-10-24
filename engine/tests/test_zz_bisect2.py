

def test_zz_1_eval_pkg():
    import engine.hydroma.eval

    assert engine.hydroma.eval is not None


def test_zz_2_split_manifest():
    from engine.hydroma.eval.benchmark_split_manifest import load_split_manifest

    assert load_split_manifest is not None


def test_zz_3_stage39_benchmark():
    from engine.hydroma.eval.stage39_benchmark import compute_benchmark_metrics

    assert compute_benchmark_metrics is not None


def test_zz_4_weather():
    from engine.hydroma.simulation.weather_source import fetch_daily_weather

    assert fetch_daily_weather is not None

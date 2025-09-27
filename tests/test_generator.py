from agent.generator import generate_candidates

def test_generate_basic():
    out = generate_candidates('global internship', n=10, use_cache=False)
    assert isinstance(out, list)
    assert len(out) == 10
    for item in out:
        assert 'keyword' in item and 'est_volume' in item and 'est_competition' in item and 'score' in item

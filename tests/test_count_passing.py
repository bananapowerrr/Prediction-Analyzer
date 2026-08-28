import unittest
from core.models import Market
from data.filters import count_passing


def _m(**kw):
    defaults = dict(id="m1", question="Q", liquidity=1000, spread=0.02, volume_24h=500)
    defaults.update(kw)
    return Market(**defaults)


class TestCountPassing(unittest.TestCase):

    def test_empty_list(self):
        self.assertEqual(count_passing([], 100, 0.05, 100), 0)

    def test_all_pass(self):
        markets = [
            _m(id="a", liquidity=5000, spread=0.01, volume_24h=1000),
            _m(id="b", liquidity=2000, spread=0.03, volume_24h=800),
        ]
        self.assertEqual(count_passing(markets, 1000, 0.05, 500), 2)

    def test_none_pass(self):
        markets = [
            _m(id="a", liquidity=100, spread=0.10, volume_24h=10),
            _m(id="b", liquidity=50, spread=0.20, volume_24h=5),
        ]
        self.assertEqual(count_passing(markets, 1000, 0.05, 500), 0)

    def test_some_pass(self):
        markets = [
            _m(id="pass1", liquidity=5000, spread=0.01, volume_24h=1000),
            _m(id="fail_liq", liquidity=50, spread=0.01, volume_24h=1000),
            _m(id="fail_spread", liquidity=5000, spread=0.50, volume_24h=1000),
            _m(id="fail_vol", liquidity=5000, spread=0.01, volume_24h=1),
            _m(id="pass2", liquidity=3000, spread=0.03, volume_24h=600),
        ]
        self.assertEqual(count_passing(markets, 1000, 0.05, 100), 2)

    def test_boundary_exact_threshold(self):
        markets = [_m(id="edge", liquidity=1000, spread=0.05, volume_24h=500)]
        self.assertEqual(count_passing(markets, 1000, 0.05, 500), 1)

    def test_boundary_just_below_threshold(self):
        markets = [_m(id="below", liquidity=999.99, spread=0.0501, volume_24h=499.99)]
        self.assertEqual(count_passing(markets, 1000, 0.05, 500), 0)

    def test_single_passing(self):
        self.assertEqual(count_passing([_m()], 500, 0.10, 200), 1)

    def test_single_failing(self):
        self.assertEqual(count_passing([_m(liquidity=1)], 500, 0.10, 200), 0)

    def test_only_liquidity_fails(self):
        markets = [_m(id="a", liquidity=10, spread=0.01, volume_24h=9999)]
        self.assertEqual(count_passing(markets, 100, 0.05, 100), 0)

    def test_only_spread_fails(self):
        markets = [_m(id="a", liquidity=9999, spread=0.99, volume_24h=9999)]
        self.assertEqual(count_passing(markets, 100, 0.05, 100), 0)

    def test_only_volume_fails(self):
        markets = [_m(id="a", liquidity=9999, spread=0.01, volume_24h=1)]
        self.assertEqual(count_passing(markets, 100, 0.05, 100), 0)

    def test_two_fail_one_pass(self):
        markets = [
            _m(id="a", liquidity=1, spread=0.01, volume_24h=1),
            _m(id="b", liquidity=1, spread=0.99, volume_24h=1),
            _m(id="c", liquidity=9999, spread=0.01, volume_24h=9999),
        ]
        self.assertEqual(count_passing(markets, 100, 0.05, 100), 1)

    def test_thresholds_very_permissive(self):
        markets = [_m(id="x"), _m(id="y"), _m(id="z")]
        self.assertEqual(count_passing(markets, 0, 1.0, 0), 3)

    def test_thresholds_very_strict(self):
        markets = [_m(id="x"), _m(id="y")]
        self.assertEqual(count_passing(markets, float("inf"), -1, float("inf")), 0)


if __name__ == "__main__":
    unittest.main()

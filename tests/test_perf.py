import timeit
from fluxcov.coverage import ELFCache


def test_cache():
    cache = ELFCache("cache")
    assert cache is not None
    first = timeit.timeit(
        "cache.get('./bin/example_test.out')", globals=locals(), number=1
    )
    cached = timeit.timeit(
        "cache.get('./bin/example_test.out')", globals=locals(), number=1
    )
    print(first, cached)
    assert first > cached

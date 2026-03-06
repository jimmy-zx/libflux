from typing import Self
from fluxcov.coverage import ELF, Coverage
from fluxcov.binding import Closable, Globals, Instance


class Bench(Closable):
    def __init__(self, elf: ELF, shm_path: str) -> None:
        self.elf = elf
        self.shm_path = shm_path
        self.globals = Globals.create()
        self.instance = Instance.create(shm_path)

    def close(self) -> None:
        self.globals.close()
        self.instance.close()

    def check(self) -> bool:
        return self.instance.check(self.globals)

    def context(self) -> "BenchContext":
        return BenchContext(self)


class BenchContext(Closable):
    def __init__(self, bench: Bench) -> None:
        self.bench = bench
        self.cov_prev: Coverage | None = None
        self.cov_after: Coverage | None = None
        self.cov_cur: Coverage | None = None

    def __enter__(self) -> Self:
        self.cov_prev = Coverage(self.bench.elf, self.bench.globals.counters)
        return self

    def close(self) -> None:
        self.cov_after = Coverage(self.bench.elf, self.bench.globals.counters)
        self.cov_cur = Coverage(self.bench.elf, self.bench.instance.counters)

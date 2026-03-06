import argparse
import io
import lief
from capstone import Cs, CsInsn, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86Op, X86_OP_IMM
from elftools.elf.elffile import ELFFile

from fluxcov.binding import NUM_TRACKED_BITS


class ELF:
    def __init__(
        self,
        data: bytes,
        symbol: str = "__sanitizer_cov_trace_pc",
        num_tracked_bits: int = NUM_TRACKED_BITS,
        path: bool = False,
    ) -> None:
        self.data = data
        self.symbol = symbol
        self.num_tracked_bits = num_tracked_bits
        assert not path

        self.imm_calls = self.get_imm_calls_for_elf()
        self.plt_table = self.get_plt_table()
        self.call_sites = self.collect_call_sites_for_symbol(symbol=symbol)
        self.buckets = self.bucket_to_pcs()

    @classmethod
    def from_path(cls, path: str) -> "ELF":
        with open(path, "rb") as fp:
            return cls(fp.read())

    def get_imm_calls_for_elf(self) -> list[tuple[int, int]]:
        stream = io.BytesIO(self.data)
        elf = ELFFile(stream)
        text = elf.get_section_by_name(".text")
        code = text.data()
        addr = text["sh_addr"]

        md = Cs(CS_ARCH_X86, CS_MODE_64)
        md.detail = True

        i: CsInsn
        calls: list[tuple[str, str]] = []
        for i in md.disasm(code, addr):
            if i.mnemonic == "call":
                if len(i.operands) != 1:
                    continue
                op: X86Op = i.operands[0]
                if op.type != X86_OP_IMM:
                    continue
                # deemed return addr, target
                calls.append((i.address + i.size, op.imm))
        return calls

    def get_plt_table(self) -> dict[int, str]:
        elf = lief.parse(self.data)
        plt = elf.get_section(".plt")
        stub0 = plt.virtual_address + 0x10
        stub_size = 0x10

        relocs: dict[int, str] = {}
        for idx, rel in enumerate(elf.pltgot_relocations):
            relocs[stub0 + idx * stub_size] = rel.symbol.name
        return relocs

    def collect_call_sites_for_symbol(
        self,
        symbol: str = "__sanitizer_cov_trace_pc",
    ) -> list[int]:
        calls: list[int] = []
        for addr, imm in self.imm_calls:
            if imm not in self.plt_table:
                continue
            if self.plt_table[imm] != symbol:
                continue
            calls.append(addr)
        return calls

    def pc_to_bucket(self, pc: int) -> int:
        return pc & ((1 << self.num_tracked_bits) - 1)

    def bucket_to_pcs(self) -> dict[int, list[int]]:
        buckets: dict[int, list[int]] = {}
        for pc in self.call_sites:
            bucket = self.pc_to_bucket(pc)
            buckets[bucket] = buckets.get(pc, []) + [pc]
        return buckets


class Coverage:
    def __init__(self, elf: ELF, dump: list[int], no_check: bool = False) -> None:
        self.elf = elf
        self.dump = dump

        self.hits: dict[int, int] = {}
        for bucket, count in enumerate(self.dump):
            if count != 0:
                self.hits[bucket] = count

        assert no_check or not self.validate()

    def validate(self) -> list[int]:
        invalid: list[int] = []
        for bucket in self.hits:
            if bucket not in self.elf.buckets:
                invalid.append(bucket)
        return invalid


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("elf", type=str)
    parser.add_argument("-d", "--dump", type=str)
    args = parser.parse_args()

    with open(args.elf, "rb") as fp:
        elf = ELF(fp.read())

    dump: list[int] = []
    if args.dump:
        with open(args.dump, "rb") as fp:
            dump = list(fp.read())

    coverage = Coverage(elf, dump)

    for bucket, pcs in elf.buckets.items():
        print(f"Bucket {hex(bucket)} ->", end=" ")
        print(",".join(hex(pc) for pc in pcs), end=" ")
        print(coverage.hits.get(bucket, 0))

    print(f"Coverage: {len(coverage.hits) / len(elf.buckets) * 100}%")

    invalid = coverage.validate()
    if invalid:
        raise Exception(f"The following buckets are invalid: {invalid}")


if __name__ == "__main__":
    main()

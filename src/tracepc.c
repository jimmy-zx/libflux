#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>

#include "utils.h"

static const char *__trace_pc_dump_file;
static const char *__trace_pc_shm_path;
static struct counters_t *__trace_pc_counters;
static uintptr_t __trace_pc_last_pc;

__attribute__((no_instrument_function, noinline)) void __sanitizer_cov_trace_pc(
    void) {
  uintptr_t pc = (uintptr_t)__builtin_return_address(0);
#ifdef PATH_COVERAGE
  uintptr_t idx = (pc ^ (__trace_pc_last_pc >> 1)) & (kNumCounters - 1);
#else
  uintptr_t idx = pc & (kNumCounters - 1);
#endif
  __trace_pc_counters->counters[idx]++;
#ifdef PATH_COVERAGE
  __trace_pc_last_pc = pc;
#endif
}

__attribute__((no_instrument_function, constructor)) static void
__trace_pc_init(void) {
  __trace_pc_last_pc = 0;
  __trace_pc_dump_file = getenv("FLUXCOV_DUMP");

  // allocate counters buffer
  if ((__trace_pc_shm_path = getenv("FLUXCOV_SHM")) != NULL) {
    if ((__trace_pc_counters = fluxcov_shm_open(
             __trace_pc_shm_path, O_RDWR,
             /*mode=*/0, PROT_READ | PROT_WRITE, false)) == NULL) {
      errExit("fluxcov_shm_open");
    }
    memset(__trace_pc_counters, 0, sizeof(struct counters_t));
  } else if ((__trace_pc_counters = calloc(1, sizeof(struct counters_t))) ==
             NULL) {
    errExit("fuzzer failed to init: calloc\n");
  }
}

__attribute__((no_instrument_function, destructor)) static void __trace_pc_fini(
    void) {
  // dump to file
  if (__trace_pc_dump_file != NULL) {
    int fd = open(__trace_pc_dump_file, O_WRONLY | O_CREAT | O_TRUNC,
                  S_IRUSR | S_IWUSR | S_IRGRP | S_IROTH);
    if (fd < 0) {
      errExit("fuzzer failed to dump: open");
    }
    ssize_t res = write(fd, __trace_pc_counters, sizeof(struct counters_t));
    if (res < 0) {
      errExit("fuzzer failed to dump: write");
    }
    close(fd);
  }

  // tear down counters buffer
  if (__trace_pc_shm_path != NULL) {
    if (fluxcov_shm_close(__trace_pc_shm_path, __trace_pc_counters, false) ==
        -1) {
      errExit("fluxcov_shm_close");
    }
  } else {
    free(__trace_pc_counters);
  }
}

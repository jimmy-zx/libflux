#include <fcntl.h>
#include <libgen.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>

#include "utils.h"

static struct {
  const char *filter;
  const char *dump_file;
  const char *shm_path;
  bool dump_pid;
  bool cumulative;
} __trace_pc_config;

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
  __trace_pc_config.filter = getenv("FLUXCOV_FILTER");
  __trace_pc_config.dump_file = getenv("FLUXCOV_DUMP");
  __trace_pc_config.shm_path = getenv("FLUXCOV_SHM");
  __trace_pc_config.dump_pid = (getenv("FLUXCOV_DUMP_PID") != NULL);
  __trace_pc_config.cumulative = (getenv("FLUXCOV_CUM") != NULL);

  if (__trace_pc_config.filter != NULL) {
    char *exec = get_exec();
    if (exec == NULL) {
      fprintf(stderr, "Unable to get argv[0]. Exiting...");
      exit(EXIT_FAILURE);
    }
    char *base = basename(exec);
    if (strcmp(__trace_pc_config.filter, base) != 0) {
      __trace_pc_config.dump_file = NULL;
      __trace_pc_config.dump_pid = NULL;
    }
    free(exec);
  }

  if (getenv("FLUXCOV_HELP") != NULL) {
    char *exec = get_exec();
    printf(
        "\nBEGIN FLUXCOV_HELP\n"
        "Options:\n"
        "\tFLUXCOV_DUMP=[path=%s]: dump the execution result to [path]\n"
        "\tFLUXCOV_SHM=[shm_path=%s]: store the execution result via shm_open "
        "[shm_path]\n"
        "\tFLUXCOV_DUMP_PID=[any=%d]: add pid to [path]\n"
        "\tFLUXCOV_CUM=[any=%d]: if enabled, memory buffer will not be "
        "cleared\n"
        "\tFLUXCOV_FILTER=[filter=%s]: only dump if basename(argv[0]) == "
        "[filter]\n"
        "Debug:\n"
        "\tpid=%lld\n"
        "\targv[0]=%s\n"
        "END FLUXCOV_HELP\n\n",
        __trace_pc_config.dump_file, __trace_pc_config.shm_path,
        (int)__trace_pc_config.dump_pid, (int)__trace_pc_config.cumulative,
        __trace_pc_config.filter, (long long)getpid(), exec);
    free(exec);
  }

  // allocate counters buffer
  if (__trace_pc_config.shm_path != NULL) {
    if ((__trace_pc_counters = fluxcov_shm_open(
             __trace_pc_config.shm_path, O_RDWR,
             /*mode=*/0, PROT_READ | PROT_WRITE, false)) == NULL) {
      errExit("fluxcov_shm_open");
    }
  } else if ((__trace_pc_counters = malloc(sizeof(struct counters_t))) ==
             NULL) {
    errExit("fuzzer failed to init: calloc\n");
  }

  if (!__trace_pc_config.cumulative) {
    memset(__trace_pc_counters, 0, sizeof(struct counters_t));
  }
}

__attribute__((no_instrument_function, destructor)) static void __trace_pc_fini(
    void) {
  // dump to file
  if (__trace_pc_config.dump_file != NULL) {
    const char *buf = __trace_pc_config.dump_file;
    if (__trace_pc_config.dump_pid) {
      pid_t pid = getpid();
      int len = snprintf(NULL, 0, "%s.%lld", __trace_pc_config.dump_file,
                         (long long)pid);
      if (len < 0) {
        errExit("snprintf");
      }
      char *buf_w = alloca(len + 1);
      snprintf(buf_w, len, "%s.%lld", __trace_pc_config.dump_file,
               (long long)pid);
      buf = buf_w;
    }
    int fd = open(buf, O_WRONLY | O_CREAT | O_TRUNC,
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
  if (__trace_pc_config.shm_path != NULL) {
    if (fluxcov_shm_close(__trace_pc_config.shm_path, __trace_pc_counters,
                          false) == -1) {
      errExit("fluxcov_shm_close");
    }
  } else {
    free(__trace_pc_counters);
  }
}

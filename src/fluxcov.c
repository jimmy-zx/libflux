#include "fluxcov.h"

#include <errno.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "utils.h"

#define RETURN(value)  \
  do {                 \
    if (err != NULL) { \
      *err = errno;    \
    }                  \
    return (value);    \
  } while (0);
#define RETURN1(value)   \
  do {                   \
    if (err != NULL) {   \
      *err = prev_errno; \
    }                    \
    return (value);      \
  } while (0);

struct fluxcov_globals *fluxcov_init(int *err) {
  errno = 0;
  void *ptr = calloc(1, sizeof(struct fluxcov_globals));
  RETURN(ptr);
}

int fluxcov_fini(struct fluxcov_globals *globals, int *err) {
  errno = 0;
  free(globals);
  RETURN(0);
}

struct fluxcov_instance *fluxcov_start(const char *path, int *err) {
  errno = 0;
  struct fluxcov_instance *instance = malloc(sizeof(struct fluxcov_instance));
  if (instance == NULL) {
    RETURN(NULL);
  }
  if ((instance->path = malloc((strlen(path) + 1) * sizeof(char))) == NULL) {
    free(instance);
    RETURN(NULL);
  }
  strcpy(instance->path, path);
  if ((instance->counters =
           fluxcov_shm_open(path, O_RDWR | O_CREAT | O_TRUNC | O_EXCL,
                            S_IRUSR | S_IWUSR | S_IRGRP | S_IROTH,
                            PROT_READ | PROT_WRITE, true)) == NULL) {
    int prev_errno = errno;
    free(instance->path);
    free(instance);
    RETURN1(NULL);
  }
  RETURN(instance);
}

bool fluxcov_check(struct fluxcov_globals *globals,
                   struct fluxcov_instance *instance, uint8_t max_global_value,
                   int *err) {
  errno = 0;
  bool flag = false;
  for (size_t idx = 0; idx < kNumCounters; idx++) {
    uint8_t global_value = globals->counters.counters[idx];
    if (global_value < instance->counters->counters[idx] &&
        global_value <= max_global_value) {
      globals->counters.counters[idx] = instance->counters->counters[idx];
      flag = true;
    }
  }
  int prev_errno = 0;
  RETURN1(flag);
}

int fluxcov_end(struct fluxcov_instance *instance, int *err) {
  errno = 0;
  int res = fluxcov_shm_close(instance->path, instance->counters, true);
  int prev_errno = errno;
  free(instance->path);
  free(instance);
  RETURN1(res);
}

uint64_t fluxcov_sum(struct counters_t *counters) {
  uint64_t sum = 0;
  for (size_t i = 0; i < kNumCounters; i++) {
    sum += counters->counters[i];
  }
  return sum;
}

uint64_t fluxcov_count(struct counters_t *counters) {
  uint64_t count = 0;
  for (size_t i = 0; i < kNumCounters; i++) {
    count += counters->counters[i] > 0;
  }
  return count;
}

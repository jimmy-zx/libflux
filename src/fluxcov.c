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
           fluxcov_shm_open(path, O_RDWR | O_CREAT | O_TRUNC,
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
                   struct fluxcov_instance *instance, int *err) {
  errno = 0;
  bool flag = false;
  for (size_t idx = 0; idx < kNumCounters; idx++) {
    if (globals->counters.counters[idx] < instance->counters->counters[idx]) {
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

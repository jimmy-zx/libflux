#ifndef UTILS_H_
#define UTILS_H_

#include <fcntl.h>
#include <limits.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>

#ifdef DEBUG
#define DEBUG_PERROR(msg) \
  {                       \
    perror(msg);          \
  }
#else
#define DEBUG_PERROR(msg) \
  {                       \
  }
#endif

#ifndef kNumTrackedBits
#define kNumTrackedBits 18
#endif

#define kNumCounters ((uintptr_t)1 << kNumTrackedBits)

struct counters_t {
  uint8_t counters[kNumCounters];
};

static inline void errExit(const char *msg) {
  perror(msg);
  exit(EXIT_FAILURE);
}

static inline void *fluxcov_shm_open(const char *name, int oflag, mode_t mode,
                                     int prot, bool truncate) {
  int fd = shm_open(name, oflag, mode);
  if (fd < 0) {
    DEBUG_PERROR("fluxcov_shm_open: shm_open");
    return NULL;
  }
  if (truncate && ftruncate(fd, sizeof(struct counters_t))) {
    DEBUG_PERROR("fluxcov_shm_open: ftruncate");
    return NULL;
  }
  void *ptr = mmap(
      /*addr=*/NULL, sizeof(struct counters_t), prot, MAP_SHARED, fd,
      /*offset=*/0);
  if (ptr == MAP_FAILED) {
    DEBUG_PERROR("fluxcov_shm_open: mmap");
    return NULL;
  }
  if (close(fd) == -1) {
    DEBUG_PERROR("fluxcov_shm_open: close");
    return NULL;
  }
  return ptr;
}

static inline int fluxcov_shm_close(const char *name, void *ptr, bool unlink) {
  if (munmap(ptr, sizeof(struct counters_t)) == -1) {
    DEBUG_PERROR("fluxcov_shm_close: munmap");
    return -1;
  }
  if (unlink) {
    if (shm_unlink(name)) {
      DEBUG_PERROR("fluxcov_shm_close: shm_unlink");
      return -1;
    }
  }
  return 0;
}

static inline char *get_exec(void) {
  int fd = open("/proc/self/cmdline", O_RDONLY);
  if (fd < 0) {
    DEBUG_PERROR("get_exec: open");
    return NULL;
  }
  char *buf = malloc(PATH_MAX + 1);
  if (buf == NULL) {
    close(fd);
    DEBUG_PERROR("get_exec: malloc");
    return NULL;
  }
  ssize_t count = read(fd, buf, PATH_MAX + 1);
  close(fd);
  if (count < 0) {
    free(buf);
    DEBUG_PERROR("get_exec: read");
    return NULL;
  }
  if (strnlen(buf, PATH_MAX + 1) > PATH_MAX) {
    free(buf);
    return NULL;
  }
  return buf;
}

#endif  // UTILS_H_

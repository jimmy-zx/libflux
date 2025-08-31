CFLAGS ?= -Wall -Wextra -Wpedantic -g -DDEBUG -DPATH_COVERAGE
CFLAGS += -fPIC -Iinclude

OBJ_DIR := obj
SRC_DIR := src
EXAMPLE_DIR := examples
HEADERS := include

LIB_DIR := lib
BIN_DIR := bin

LIBS := $(LIB_DIR)/libfluxcov.so $(LIB_DIR)/libtracepc.so
BINS := $(BIN_DIR)/no_aslr.out
EXAMPLES := $(BIN_DIR)/example_test.out $(BIN_DIR)/example_branch.out

all: $(OBJ_DIR) libs bins

libs: $(LIB_DIR) $(OBJ_DIR) $(LIBS)

bins: $(BIN_DIR) $(OBJ_DIR) $(BINS) $(EXAMPLES)

$(OBJ_DIR):
	mkdir -p $(OBJ_DIR)

$(LIB_DIR):
	mkdir -p $(LIB_DIR)

$(BIN_DIR):
	mkdir -p $(BIN_DIR)

$(LIB_DIR)/libfluxcov.so: $(OBJ_DIR)/fluxcov.o
	$(CC) $(CFLAGS) -shared -o $@ $^

$(LIB_DIR)/libtracepc.so: $(OBJ_DIR)/tracepc.o
	$(CC) $(CFLAGS) -shared -o $@ $^

$(BIN_DIR)/no_aslr.out: $(OBJ_DIR)/no_aslr.o
	$(CC) $(CFLAGS) -o $@ $^

$(BIN_DIR)/example_%.out: $(OBJ_DIR)/example_%.o
	$(CC) $(CFLAGS) -o $@ $^ -Llib -ltracepc -lfluxcov

$(OBJ_DIR)/example_%.o: $(EXAMPLE_DIR)/%.c $(HEADERS)
	$(CC) $(CFLAGS) -fsanitize-coverage=trace-pc -c $< -o $@

$(OBJ_DIR)/%.o: $(SRC_DIR)/%.c $(HEADERS)
	$(CC) $(CFLAGS) -c $< -o $@

.PHONY : test format check clean

test: all
	pytest

format:
	clang-format -i $(SRC_DIR)/* $(HEADERS)/* $(EXAMPLE_DIR)/*
	black python

check:
	clang-format --dry-run $(SRC_DIR)/* $(HEADERS)/* $(EXAMPLE_DIR)/*
	clang-tidy $(SRC_DIR)/* $(HEADERS)/* $(EXAMPLE_DIR)/*
	black --check python

clean:
	rm -rf $(OBJ_DIR) $(LIB_DIR) $(BIN_DIR)

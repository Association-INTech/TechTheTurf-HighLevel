//
// Created by Loïc on 01/04/2024.
//

#ifndef ASTAR_MIN_HEAP_H
#define ASTAR_MIN_HEAP_H
#include <stdint.h>


struct ContextFunction {
    uint32_t* (*function)(uint32_t value, void* context);
    void* context;
};

struct MinHeap {
    uint32_t MAX_SIZE, length, *values, *indices;
    struct ContextFunction *key;
};

uint32_t* call_context_function(const struct ContextFunction *f, uint32_t value);
void heap_init(struct MinHeap *heap, uint32_t max_size, struct ContextFunction *key);
void heap_clear(struct MinHeap *heap);
void heap_push(struct MinHeap *heap, uint32_t value);
void heap_update(struct MinHeap *heap, uint32_t value);
uint32_t heap_extract_min(struct MinHeap *heap);

#endif //ASTAR_MIN_HEAP_H

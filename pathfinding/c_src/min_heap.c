//
// Created by Loïc on 01/04/2024.
//
#include "min_heap.h"
#include "stdlib.h"


uint32_t * call_context_function(const struct ContextFunction * const f, const uint32_t value) {
    return f->function(value, f->context);
}

int is_lower(const uint32_t * pair1, uint32_t * pair2) {
    int result;
    if (pair1[0] < pair2[0])
        result = 1;
    else if (pair1[0] == pair2[0])
        result =  pair1[1] < pair2[1];
    else
        result =  0;
    free(pair2);
    return result;
}

void heap_init(struct MinHeap* const heap, const uint32_t max_size, struct ContextFunction *key) {
    heap->MAX_SIZE = max_size;
    heap->length = 0;
    heap->indices = (uint32_t*) malloc(sizeof(uint32_t) * max_size);
    heap->values = (uint32_t*) malloc(sizeof(uint32_t) * max_size);
    heap->key = key;

    for (int index = 0; index < max_size; index++) {
        heap->indices[index] = UINT32_MAX;
        heap->values[index] = 0;
    }
}

void heap_clear(struct MinHeap *const heap) {
    free(heap->indices);
    free(heap->values);
}

void heap_push(struct MinHeap *const heap, const uint32_t value) {
    heap->indices[value] = heap->length;
    heap->values[heap->length++] = value;
    heap_update(heap, value);
}

void heap_update(struct MinHeap *const heap, const uint32_t value) {
    uint32_t index = heap->indices[value];
    uint32_t parent_index = (index - 1) / 2;
    uint32_t *key = call_context_function(heap->key, value);

    while (index >= 1 && is_lower(key, call_context_function(heap->key, heap->values[parent_index]))) {
        // Exchange in the array
        heap->values[index] = heap->values[parent_index];
        heap->values[parent_index] = value;

        // Exchange in indices
        heap->indices[value] = parent_index;
        heap->indices[heap->values[index]] = index;

        index = parent_index;
        parent_index = (parent_index - 1) / 2;
    }
}

uint32_t heap_extract_min(struct MinHeap *heap) {
    // Minimum is out
    uint32_t result = heap->values[0];
    heap->indices[result] = UINT32_MAX;

    // Last value becomes root
    heap->values[0] = heap->values[--heap->length];
    heap->indices[heap->values[0]] = 0;

    uint64_t index = 0;
    while (2 * index + 1 < heap->length) {
        uint32_t* minimum = call_context_function(heap->key, heap->values[index]);
        uint64_t min_index = index, left = 2 * index + 1, right = 2 * index + 2;

        if (left < heap->length && !is_lower(minimum, call_context_function(heap->key, heap->values[left]))) {
            free(minimum);
            minimum = call_context_function(heap->key, heap->values[left]);
            min_index = left;
        }

        if (right < heap->length && !is_lower(minimum, call_context_function(heap->key, heap->values[right]))) {
            min_index = right;
        }
        free(minimum);

        // Current is the minimum, no need to go further down
        if (min_index == index) break;


        // Values exchange
        uint32_t tmp = heap->values[index];
        heap->values[index] = heap->values[min_index];
        heap->values[min_index] = tmp;

        // Index exchange
        heap->indices[tmp] = min_index;
        heap->indices[heap->values[index]] = index;

        index = min_index;
    }

    return result;
}
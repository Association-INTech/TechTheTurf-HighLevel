//
// Created by Loïc on 01/04/2024.
//
#include "min_heap.h"
#include "stdlib.h"

KeyValue KEY0, KEY1;

void call_context_function(const ContextFunction * const f, const uint32_t value) {
    return f->function(value, f->context, &KEY0);
}

uint8_t compare_keys() {
    if (KEY0.f_score < KEY1.f_score)
        return 1;
    if (KEY0.f_score == KEY1.f_score)
        return KEY0.heuristic < KEY1.heuristic;
    return 0;
}

uint8_t call_and_compare(const ContextFunction * const f, const uint32_t value) {
    f->function(value, f->context, &KEY1);
    return compare_keys();
}

void heap_init(MinHeap* const heap, const uint32_t max_size, ContextFunction *key) {
    heap->length = 0;
    heap->indices = (uint32_t*) malloc(sizeof(uint32_t) * max_size);
    heap->values = (uint32_t*) malloc(sizeof(uint32_t) * max_size);
    heap->key = key;

    for (uint32_t index = 0; index < max_size; index++) {
        heap->indices[index] = UINT32_MAX;
        heap->values[index] = 0;
    }
}

void heap_clear(MinHeap *const heap) {
    free(heap->indices);
    free(heap->values);
}

void heap_push(MinHeap *const heap, const uint32_t value) {
    heap->indices[value] = heap->length;
    heap->values[heap->length++] = value;
    heap_update(heap, value);
}

void heap_update(MinHeap *const heap, const uint32_t value) {
    uint32_t index = heap->indices[value];
    uint32_t parent_index = (index - 1) / 2;
    call_context_function(heap->key, value);

    while (index >= 1 && call_and_compare(heap->key, heap->values[parent_index])) {
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

uint32_t heap_extract_min(MinHeap *heap) {
    // Minimum is out
    uint32_t result = heap->values[0];
    heap->indices[result] = UINT32_MAX;

    // Last value becomes root
    heap->values[0] = heap->values[--heap->length];
    heap->indices[heap->values[0]] = 0;

    uint64_t index = 0;
    while (2 * index + 1 < heap->length) {
        call_context_function(heap->key, heap->values[index]);

        uint64_t min_index = index;

        uint64_t left = 2 * index + 1;
        if (left < heap->length && !call_and_compare(heap->key, heap->values[left])) {
            KEY0.value = KEY1.value;
            min_index = left;
        }

        uint64_t right = 2 * index + 2;
        if (right < heap->length && !call_and_compare(heap->key, heap->values[right]))
            min_index = right;

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
//
// Created by Loïc on 01/04/2024.
//

#ifndef ASTAR_MIN_HEAP_H
#define ASTAR_MIN_HEAP_H
#include <stdint.h>


typedef union {
    struct {
        uint32_t f_score;
        uint32_t heuristic;
    };
    uint64_t value;
} KeyValue;


typedef struct {
    void (*function)(uint32_t value, void* context, KeyValue* output);
    void* context;
} ContextFunction;

typedef struct {
    uint32_t length, *values, *indices;
    ContextFunction *key;
} MinHeap;

/**
 * KEY0 < KEY1
 * @return
 */
uint8_t compare_keys();

/**
 * Fill KEY0 with f(value)
 * @param f
 * @param value
 */
void call_context_function(const ContextFunction *f, uint32_t value);


/**
 * Fill KEY1 with f(value) and compare KEY0 and KEY1
 * @param f
 * @param value
 * @return KEY0 < KEY1
 */
uint8_t call_and_compare(const ContextFunction * f, uint32_t value);

/**
 * Allocate heap arrays
 * @param heap
 * @param max_size
 * @param key
 */
void heap_init(MinHeap *heap, uint32_t max_size, ContextFunction *key);

/**
 * Free heap arrays
 * @param heap
 */
void heap_clear(MinHeap *heap);

/**
 * Add an element to the heap, conserve order, O(log n)
 * @param heap
 * @param value
 */
void heap_push(MinHeap *heap, uint32_t value);


/**
 * Raise an item up the heap to conserve order, O(log n)
 * @param heap
 * @param value
 */
void heap_update(MinHeap *heap, uint32_t value);

/**
 * Remove minimum item, reorder the heap, O(log n)
 * @param heap
 * @return
 */
uint32_t heap_extract_min(MinHeap *heap);

#endif //ASTAR_MIN_HEAP_H

//
// Created by Loïc on 01/04/2024.
//
#include "stdlib.h"
#include "stdio.h"
#include "min_heap.h"

uint64_t identity(const uint32_t value, void* context) {
    return value;
}
struct ContextFunction ID = {
        .function = identity,
        .context = NULL
};

int check_indices(struct MinHeap *heap) {
    int result = 1;
    for (int index = 0; index < heap->length; index++) {
        result = result & (index == heap->indices[heap->values[index]]);
    }
    return result;
}


int main(int argc, char** args) {
    struct MinHeap heap;
    heap_init(&heap, 100, &ID);
    for (int index = 0; index < 100; index++) {
        heap_push(&heap, index);
    }
    for (int index = 0; index < 100; index++) {
        printf("%d      : %d\n", heap_extract_min(&heap), check_indices(&heap));
    }
    return 0;
}
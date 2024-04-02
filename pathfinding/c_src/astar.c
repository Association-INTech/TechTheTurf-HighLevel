#include "astar.h"
#include "min_heap.h"
#include "stdlib.h"
#include "stdio.h"
#define ABS(X) (((X) < 0) ? -(X) : (X))
#define MIN(A, B) (((A) < (B) ? (A) : (B)))
#define MAX(A, B) (((A) > (B) ? (A) : (B)))

const uint64_t ONE = 10, SQRT2 = 14;
const uint64_t COSTS[2] = {ONE, SQRT2};


uint32_t * f_score(uint32_t node, void* context) {
    uint32_t** _context = (uint32_t**) context;
    uint64_t cost = _context[0][node], heuristic = _context[1][node];
//    return ((cost + heuristic) * SHIFT32) + heuristic; // plante jsp pk
    uint32_t *res = malloc(sizeof(uint32_t) * 2);
    res[0] = cost + heuristic;
    res[1] = heuristic;
    return res;
}

int check_indices(struct MinHeap *heap) {
    int result = 1;
    for (int index = 0; index < heap->length; index++) {
        result = result & (index == heap->indices[heap->values[index]]);
    }
    return result;
}

int check_order(struct MinHeap *heap) {
    int result = 1;
    for (int index = 1; index < heap->length; index++) {
        result = result & (call_context_function(heap->key, heap->values[(index - 1) / 2]) <= call_context_function(heap->key, heap->values[index]));
    }
    return result;
}

uint32_t* grid_astar(const uint32_t width, const uint32_t height, const uint8_t * const grid, const uint32_t start_node, const uint32_t end_node) {
    uint32_t* costs = (uint32_t*) malloc(width * height * sizeof(uint32_t));
    uint32_t* heuristics = (uint32_t*) malloc(width * height * sizeof(uint32_t));
    uint32_t* predecessors = (uint32_t*) malloc(width * height * sizeof(uint32_t));
    for (int index = 0; index < width * height; index++) {
        costs[index] = UINT32_MAX;
        predecessors[index] = UINT32_MAX;
        heuristics[index] = UINT32_MAX;
    }
    uint32_t* const context[2] = {costs, heuristics};
    struct ContextFunction heap_key = {
        .function = f_score,
        .context = (void*) context
    };
    struct MinHeap heap;
    heap_init(&heap, width * height, &heap_key);

    const int64_t end_x = end_node % width, end_y = end_node / width;
    costs[start_node] = 0;
    // compute start heuristic
    const int32_t DX = ABS(start_node % width - end_x);
    const int32_t DY = ABS(start_node / width - end_y);
    heuristics[start_node] = (SQRT2 - ONE) * MIN(DX, DY) + ONE * MAX(DX, DY);
    heap_push(&heap, start_node);

    while (heap.length) {
        uint32_t current_node = heap_extract_min(&heap);
        if (current_node == end_node) break;

        uint32_t x = current_node % width, y = current_node / width;
        for (int nb_index = 0; nb_index < 9; nb_index = nb_index + 1 + (nb_index == 3)) {
            int32_t dx = nb_index % 3 - 1, dy = nb_index / 3 - 1;
            uint32_t neighbor = width * (y + dy) + x + dx;
            if (x + dx < 0 || x + dx >= width || y + dy < 0 || y + dy >= height || grid[neighbor]) continue;
            uint32_t cost = costs[current_node] + COSTS[ABS(dx) + ABS(dy) - 1];

            // Have I met that guy before
            if (costs[neighbor] == UINT32_MAX) {
                // Never met
                costs[neighbor] = cost;
                predecessors[neighbor] = current_node;

                // compute heuristic
                dx = ABS(x + dx - end_x);
                dy = ABS(y + dy - end_y);
                heuristics[neighbor] = (SQRT2 - ONE) * MIN(dx, dy) + ONE * MAX(dx, dy);

                heap_push(&heap, neighbor);
            // Is it a better way
            } else if (cost < costs[neighbor]) {
                // Much Better
                costs[neighbor] = cost;
                predecessors[neighbor] = current_node;
                heap_update(&heap, neighbor);
            }
        }
    }
    heap_clear(&heap);
    free(costs);
    free(heuristics);
    int path_length = 0;
    uint32_t current = end_node;
    while (current != UINT32_MAX) {
        path_length += 1;
//        printf("%d\n", current);
        current = predecessors[current];
    }
    uint32_t* result = (uint32_t*) malloc((path_length+1) * sizeof(uint32_t));
    current = end_node;
    result[path_length] = UINT32_MAX;
    while (path_length) {
        result[--path_length] = current;
        current = predecessors[current];
    }
    free(predecessors);
    return result;
}
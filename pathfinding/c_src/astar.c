#include "astar.h"
#include "min_heap.h"
#include "stdlib.h"
#define MIN(A, B) (((A) < (B) ? (A) : (B)))
#define MAX(A, B) (((A) > (B) ? (A) : (B)))
#define IS_NEGATIVE(X) ((X) & 0x80000000)

uint32_t ABS(uint32_t x) {
    return IS_NEGATIVE(x) ? -x : x;
}

const uint32_t ONE = 10, SQRT2 = 14;
const uint32_t COSTS[2] = {ONE, SQRT2};


void f_score(uint32_t node_index, void* context, KeyValue* output) {
    Node* node = &((Node*)context)[node_index];
    output->f_score = node->cost + node->heuristic;
    output->heuristic = node->heuristic;
}

uint32_t* grid_astar(const uint32_t width, const uint32_t height, const uint8_t * const grid, const uint32_t start_node, const uint32_t end_node) {
    // Convert end index to position
    const uint32_t end_x = end_node / height, end_y = end_node % height;

    // Initialize nodes
    Node* nodes = (Node*) malloc(sizeof(Node) * width * height);
    for (uint32_t index = 0; index < width * height; index++) {
        nodes[index].cost = -1;
        nodes[index].heuristic = -1;
        nodes[index].previous = -1;
    }

    // Initialize heap
    ContextFunction heap_key = {
        .function = f_score,
        .context = (void*) nodes
    };
    MinHeap heap;
    heap_init(&heap, width * height, &heap_key);

    // Initialize start node
    nodes[start_node].cost = 0;
    // compute start heuristic
    const uint32_t DX = ABS(start_node / height - end_x);
    const uint32_t DY = ABS(start_node % height - end_y);
    nodes[start_node].heuristic = (SQRT2 - ONE) * MIN(DX, DY) + ONE * MAX(DX, DY);
    heap_push(&heap, start_node);

    while (heap.length) {
        uint32_t current_node = heap_extract_min(&heap);
        if (current_node == end_node) break;

        uint32_t x = current_node / height, y = current_node % height;
        for (int nb_index = 0; nb_index < 9; nb_index = nb_index + 1 + (nb_index == 3)) {
            uint32_t dx = nb_index % 3 - 1;
            uint32_t dy = nb_index / 3 - 1;
            uint32_t neighbor = height * (x + dx) + y + dy;

            // Is it a valid neigh bor
            if (IS_NEGATIVE(x + dx) || x + dx >= width || IS_NEGATIVE(y + dy)|| y + dy >= height || grid[neighbor]) continue;

            uint32_t cost = nodes[current_node].cost + COSTS[ABS(dx) + ABS(dy) - 1];

            // Have I met that guy before
            if (nodes[neighbor].cost == UINT32_MAX) {
                // Never met
                nodes[neighbor].cost = cost;
                nodes[neighbor].previous = current_node;

                // compute heuristic
                dx = ABS(x + dx - end_x);
                dy = ABS(y + dy - end_y);
                nodes[neighbor].heuristic = (SQRT2 - ONE) * MIN(dx, dy) + ONE * MAX(dx, dy);

                heap_push(&heap, neighbor);
            // Is it a better way
            } else if (cost < nodes[neighbor].cost) {
                // Much Better
                nodes[neighbor].cost = cost;
                nodes[neighbor].previous = current_node;
                heap_update(&heap, neighbor);
            }
        }
    }
    heap_clear(&heap);

    // Measure path length
    int path_length = 0;
    uint32_t current = end_node;
    while (current != UINT32_MAX) {
        path_length += 1;
        current = nodes[current].previous;
    }

    // Build path
    uint32_t* result = (uint32_t*) malloc((path_length+1) * sizeof(uint32_t));
    current = end_node;
    result[path_length] = UINT32_MAX;
    while (path_length) {
        result[--path_length] = current;
        current = nodes[current].previous;
    }

    free(nodes);
    return result;
}
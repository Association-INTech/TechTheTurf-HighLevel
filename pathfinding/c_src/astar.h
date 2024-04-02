#ifndef ASTAR_ASTAR_H
#define ASTAR_ASTAR_H
#include <stdint.h>

uint32_t* grid_astar(uint32_t width, uint32_t height, const uint8_t * grid, uint32_t start_node, uint32_t end_node);

#endif //ASTAR_ASTAR_H

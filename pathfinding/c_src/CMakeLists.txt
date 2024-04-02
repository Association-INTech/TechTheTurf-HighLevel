cmake_minimum_required(VERSION 3.27)
project(Astar C)

set(CMAKE_C_STANDARD 11)
add_library(Astar SHARED astar.c
        min_heap.h
        min_heap.c
)

add_executable(test_heap test_heap.c)
target_link_libraries(test_heap Astar)
add_executable(test_astar
        test_astar.c)
target_link_libraries(test_astar Astar)

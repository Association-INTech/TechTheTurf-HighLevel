cmake_minimum_required(VERSION 3.27)
project(Astar C)

if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

set(CMAKE_C_FLAGS "-Wall -Wextra")
set(CMAKE_C_FLAGS_DEBUG "-g")
set(CMAKE_C_FLAGS_RELEASE "-Ofast")

set(CMAKE_C_STANDARD 11)
add_library(Astar SHARED astar.c
        min_heap.h
        min_heap.c
)


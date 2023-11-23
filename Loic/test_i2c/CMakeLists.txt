add_executable(test_i2c main2.c)
target_link_libraries(test_i2c pico_stdlib hardware_gpio hardware_i2c pico_time pico_i2c_slave)

pico_enable_stdio_usb(test_i2c 1)
pico_add_extra_outputs(test_i2c)
add_library(drivers
    # 在此添加驱动源文件
    # e.g. drv_uart.c
    # e.g. drv_spi.c
    # e.g. drv_i2c.c
)

target_include_directories(drivers PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/..)

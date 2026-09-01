# ============================================
# Firmware 顶层构建配置
# ============================================
cmake_minimum_required(VERSION 3.20)
project(firmware VERSION 1.0.0 LANGUAGES C CXX)

# ---- 编译选项 ----
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

# ---- 板级选择 ----
if(NOT DEFINED BOARD)
    set(BOARD "default")
endif()
message(STATUS "Target board: ${BOARD}")

# ---- 包含路径 ----
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${CMAKE_CURRENT_SOURCE_DIR}/boards/${BOARD}
)

# ---- 子模块 ----
add_subdirectory(src/app)
add_subdirectory(src/hal)
add_subdirectory(src/drivers)
add_subdirectory(src/services)

# ---- 可选: 第三方库 ----
# add_subdirectory(lib/some_lib)

# ---- 固件目标 ----
add_executable(${PROJECT_NAME}
    src/main.c
)

target_link_libraries(${PROJECT_NAME}
    app
    hal
    drivers
    services
)

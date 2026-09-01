/**
 * @file main.c
 * @brief 固件入口点
 *
 * 职责:
 *   - 系统初始化 (时钟/电源/外设)
 *   - 启动各服务模块
 *   - 进入主循环或 RTOS 调度
 */

#include "hal/hal_init.h"
#include "app/app_main.h"
#include "services/service_manager.h"

int main(void)
{
    /* 1. 硬件抽象层初始化 */
    hal_init();

    /* 2. 服务层启动 */
    service_manager_init();

    /* 3. 应用层入口 */
    app_run();

    /* 不应到达此处 */
    while (1) {
        /* idle / WFI */
    }

    return 0;
}

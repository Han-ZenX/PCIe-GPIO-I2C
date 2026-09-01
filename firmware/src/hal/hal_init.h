/**
 * @file hal_init.h
 * @brief 硬件抽象层 - 系统初始化接口
 */

#ifndef HAL_INIT_H
#define HAL_INIT_H

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief 初始化所有硬件外设
 *        包括: 时钟树、GPIO、UART、SPI、I2C、ADC 等
 */
void hal_init(void);

/**
 * @brief 系统复位
 */
void hal_reset(void);

#ifdef __cplusplus
}
#endif

#endif /* HAL_INIT_H */

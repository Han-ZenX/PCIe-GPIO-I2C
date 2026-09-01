/**
 * @file board_config.h
 * @brief 默认板级配置
 *
 * 此文件定义默认硬件引脚映射和参数。
 * 不同硬件版本应创建独立的 boards/<board_name>/board_config.h
 */

#ifndef BOARD_CONFIG_H
#define BOARD_CONFIG_H

/* ---- MCU 配置 ---- */
#define BOARD_NAME              "default"
#define MCU_TYPE                "STM32F407"
#define SYSTEM_CLOCK_HZ         168000000

/* ---- UART 引脚映射 ---- */
#define UART_DEBUG_TX_PIN       GPIO_PIN_9    /* PA9  */
#define UART_DEBUG_RX_PIN       GPIO_PIN_10   /* PA10 */
#define UART_DEBUG_BAUDRATE     115200

/* ---- SPI 引脚映射 ---- */
#define SPI_SCK_PIN             GPIO_PIN_5
#define SPI_MISO_PIN            GPIO_PIN_6
#define SPI_MOSI_PIN            GPIO_PIN_7
#define SPI_CS_PIN              GPIO_PIN_4

/* ---- I2C 引脚映射 ---- */
#define I2C_SCL_PIN             GPIO_PIN_6    /* PB6 */
#define I2C_SDA_PIN             GPIO_PIN_7    /* PB7 */

/* ---- LED / 按键 ---- */
#define LED_STATUS_PIN          GPIO_PIN_13   /* PC13 */
#define BTN_USER_PIN            GPIO_PIN_0    /* PA0  */

#endif /* BOARD_CONFIG_H */

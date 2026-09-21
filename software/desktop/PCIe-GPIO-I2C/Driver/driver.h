#ifndef DRIVER_H
#define DRIVER_H

#include "Driver_global.h"
#include <QObject>
#include <QString>

class QFile;
class QTextStream;

// 前置声明，避免把 bdaqctrl.h 暴露给上层
namespace Automation { namespace BDaq { class InstantDoCtrl; } }

/*
 * PCIE-1751 普通 DIO 模拟 I2C -> DS2482-100 -> 1-Wire -> DS2431
 *
 * 硬件依据: I2C_PCIE1751 EVAL Board (REV01)
 *   SCL     = P2_6  (SCSI-68 pin 25) -> 74HCT07 通道1 开漏输出
 *   SDA_OUT = P2_7  (SCSI-68 pin 26) -> 74HCT07 通道2 开漏输出
 *   SDA_IN  = P0_2  (SCSI-68 pin  3) <- 74HCT07 通道3 回读
 *
 * 74HCT07 为非反相集电极开漏缓冲，因此板卡侧逻辑与总线电平同相:
 *   写 0 = 拉低总线,  写 1 = 释放总线(由 2.2K 上拉为高)
 * 三个引脚全程保持固定方向，不需要切换端口方向。
 */
class DRIVER_EXPORT Driver : public QObject
{
    Q_OBJECT

public:
    // 日志级别。Trace 会逐字节记录 I2C 原始时序，条目很多，只在排查 I2C 层时开启。
    enum LogLevel {
        LogError = 0,   // 仅错误
        LogInfo  = 1,   // 事务级: 打开设备、读取开始/结束、最终结果
        LogDebug = 2,   // 命令级: DS2482 命令、状态寄存器、1-Wire 字节
        LogTrace = 3    // 字节级: 每个 I2C 字节与应答位
    };

    explicit Driver(const QString &strBID = "0", QObject *parent = NULL);
    ~Driver();

    // 只负责板卡层: 打开 PCIE-1751、配置端口方向、把总线置为空闲态。
    // 不访问 DS2482，这样即使 I2C 不通也能进入引脚自检。
    bool    Open();
    void    Close();
    bool    IsOpen() const { return m_bOpen; }

    // 器件层: 复位 DS2482 并开启有源上拉(APU)。读 ROM 前会自动调用。
    bool    InitDs2482();

    bool    ReadDs2431Rom(quint8 rom[8]);  // 读 DS2431 的 64 位 ROM(含家族码与 CRC 校验)
    QString LastError() const { return m_strError; }

    // ---------- 硬件自检 ----------
    // SDA 回环: 驱动 SDA_OUT 为 0/1，经总线由 SDA_IN 读回，验证
    // P2_7 -> 74HCT07 CH2 -> SDA 总线 -> CH3 -> P0_2 这条链路。
    bool    TestSdaLoopback(QString &report);
    // 扫描 0x08~0x77 全部 7 位地址，列出所有应答的从机。
    // 用于区分"DS2482 没工作"与"地址不是 0x18"。
    bool    ScanI2cBus(QString &report);
    // 直接设置 SCL 电平。SCL 硬件上没有回读通路，只能输出方波用万用表/示波器实测。
    void    SetSclLevel(bool bHigh);
    // 直接设置 SDA 电平。回环自检的回路不经过 DS2482 的 SDA(pin5)，
    // 因此 pin5 是否焊通只能靠在该引脚上实测方波。
    void    SetSdaLevel(bool bHigh);
    // 用通信时真正使用的 SclHigh/SclLow 连续翻转，验证总线在 I2C 速度下的实际行为，
    // 并报告实测翻转频率。万用表测 SCL 应读到约一半电源电压(占空比 50%)。
    void    TestBusToggle(int nSeconds, bool bScl, QString &report);
    // 释放 SDA 并持续监视 SDA_IN，由操作者在此期间手动把 SDA 短接到 GND。
    // 这是唯一能验证"外部器件拉低总线 -> 主机可感知"这条路径的方法，
    // 也正是 ACK 检测所依赖的路径(SDA 总线 -> 74HCT07 的 3A -> 3Y -> P0_2)。
    void    TestExternalPullLow(int nSeconds, QString &report);

    void    SetBitDelayUs(int us) { m_nBitDelayUs = us; }  // I2C 半位延时，默认 5us

    // ---------- 日志 ----------
    void     SetLogLevel(LogLevel level) { m_logLevel = level; }
    LogLevel GetLogLevel() const { return m_logLevel; }
    QString  LogFilePath() const { return m_strLogPath; }
    QString  LogDirPath() const;

    static QString RomToString(const quint8 rom[8]);       // 格式化为 "2D-xxxxxxxxxxxx-xx"

signals:
    // 供界面实时显示。level 为 LogLevel，界面可自行决定显示哪些级别。
    void LogMessage(int level, const QString &text);

private:
    // ---------- I2C 位操作层 ----------
    void    SclLow();
    void    SclHigh();
    void    SdaLow();
    void    SdaRelease();
    quint8  SdaRead();
    void    I2cStart();
    void    I2cStop();
    bool    I2cWriteByte(quint8 data);     // 返回从机是否应答
    quint8  I2cReadByte(bool bAck);

    // ---------- DS2482-100 层 ----------
    bool    Ds2482Reset();
    bool    Ds2482WriteConfig(quint8 cfg);
    bool    Ds2482SetReadPointer(quint8 code);
    bool    Ds2482ReadRegister(quint8 &value);
    bool    Ds2482WaitNotBusy(quint8 &status, int nTimeoutMs = 20);
    bool    OwReset(bool &bPresence);
    bool    OwWriteByte(quint8 data);
    bool    OwReadByte(quint8 &data);

    // ---------- 工具 ----------
    bool    WriteBit(int32_t port, int32_t bit, quint8 value);
    quint8  ReadBit(int32_t port, int32_t bit);
    static quint8  Crc8(const quint8 *data, int len);
    static QString StatusToString(quint8 status);          // 状态寄存器位解析

    // ---------- 日志 ----------
    void    InitLogFile();
    void    CloseLogFile();
    void    Log(LogLevel level, const QString &text);
    void    SetError(const QString &text);                 // 记录错误并写日志
    void    FlushLog();

    Automation::BDaq::InstantDoCtrl *m_instantDoCtrl;
    QString      m_description;      // "PCIE-1751,BID#0"
    QString      m_strError;
    bool         m_bOpen;
    int          m_nBitDelayUs;
    qint64       m_nIoErrors;     // 一次事务中 DAQNavi 读写失败的次数

    LogLevel     m_logLevel;
    QFile       *m_logFile;
    QTextStream *m_logStream;
    QString      m_strLogPath;
};

#endif // DRIVER_H

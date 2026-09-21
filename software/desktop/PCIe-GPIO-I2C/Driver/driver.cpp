#include "driver.h"
#include "bdaqctrl.h"
#include <windows.h>

#include <QCoreApplication>
#include <QDateTime>
#include <QDir>
#include <QElapsedTimer>
#include <QFile>
#include <QTextStream>
#include <QStringList>

using namespace Automation::BDaq;

// ---------------- 引脚映射 (I2C_PCIE1751 EVAL Board REV01) ----------------
static const int32_t PORT_SCL     = 2, BIT_SCL     = 6;   // SCSI-68 pin 25
static const int32_t PORT_SDA_OUT = 2, BIT_SDA_OUT = 7;   // SCSI-68 pin 26
static const int32_t PORT_SDA_IN  = 0, BIT_SDA_IN  = 2;   // SCSI-68 pin 3

// ---------------- DS2482-100 ----------------
static const quint8 DS2482_ADDR_W = 0x30;   // AD0=AD1=GND -> 7 位地址 0x18
static const quint8 DS2482_ADDR_R = 0x31;

static const quint8 CMD_DRST = 0xF0;        // Device Reset
static const quint8 CMD_SRP  = 0xE1;        // Set Read Pointer
static const quint8 CMD_WCFG = 0xD2;        // Write Configuration
static const quint8 CMD_1WRS = 0xB4;        // 1-Wire Reset
static const quint8 CMD_1WWB = 0xA5;        // 1-Wire Write Byte
static const quint8 CMD_1WRB = 0x96;        // 1-Wire Read Byte

static const quint8 PTR_DATA   = 0xE1;      // 指针代码: 读数据寄存器

static const quint8 ST_1WB = 0x01;          // 1-Wire 忙
static const quint8 ST_PPD = 0x02;          // 应答脉冲检测
static const quint8 ST_SD  = 0x04;          // 短路检测
static const quint8 ST_RST = 0x10;          // 器件复位

// ---------------- DS2431 ----------------
static const quint8 OW_CMD_READ_ROM    = 0x33;
static const quint8 DS2431_FAMILY_CODE = 0x2D;

// 十六进制格式化，统一用 "0xAB" 形式
static inline QString Hex(quint8 v)
{
    return "0x" + QString("%1").arg(v, 2, 16, QChar('0')).toUpper();
}

// 高精度延时(QPC 忙等)。I2C 位周期在微秒级，不能用 Sleep。
static void DelayMicroseconds(int microseconds)
{
    if (microseconds <= 0)
        return;

    LARGE_INTEGER freq, start, now;
    QueryPerformanceFrequency(&freq);
    QueryPerformanceCounter(&start);

    __int64 target = (__int64)((double)microseconds * freq.QuadPart / 1000000.0);

    do {
        QueryPerformanceCounter(&now);
    } while ((now.QuadPart - start.QuadPart) < target);
}

Driver::Driver(const QString &strBID, QObject *parent)
    : QObject(parent)
    , m_instantDoCtrl(NULL)
    , m_bOpen(false)
    , m_nBitDelayUs(5)          // I2C 标准模式要求 tLOW>=4.7us / tHIGH>=4.0us
    , m_nIoErrors(0)
    , m_logLevel(LogInfo)
    , m_logFile(NULL)
    , m_logStream(NULL)
{
    m_description = "PCIE-1751,BID#" + strBID;
    InitLogFile();
}

Driver::~Driver()
{
    Close();
    CloseLogFile();
}

// ============================================================ 日志

QString Driver::LogDirPath() const
{
    return QCoreApplication::applicationDirPath() + "/Log";
}

void Driver::InitLogFile()
{
    QString logDir = LogDirPath();
    QDir dir;
    if (!dir.exists(logDir))
        dir.mkpath(logDir);

    // 按天一个文件并追加，避免反复开关设备时堆积大量日志文件
    m_strLogPath = logDir + "/DS2431_" +
                   QDateTime::currentDateTime().toString("yyyyMMdd") + ".log";

    m_logFile = new QFile(m_strLogPath);
    if (!m_logFile->open(QIODevice::WriteOnly | QIODevice::Text | QIODevice::Append)) {
        delete m_logFile;
        m_logFile = NULL;
        m_strLogPath.clear();
        return;
    }

    m_logStream = new QTextStream(m_logFile);
    m_logStream->setCodec("UTF-8");

    // 注意: QTextStream 的 const char* 重载按 Latin-1 解释，中文必须显式转成 QString
    *m_logStream << "\n========================================\n"
                 << QString::fromUtf8("PCIE-1751 I2C -> DS2482-100 -> DS2431 调试日志\n")
                 << QString::fromUtf8("时间: ")
                 << QDateTime::currentDateTime().toString("yyyy-MM-dd HH:mm:ss") << "\n"
                 << QString::fromUtf8("设备: ") << m_description << "\n"
                 << QString::fromUtf8("引脚: SCL=P2_6(pin25)  SDA_OUT=P2_7(pin26)  SDA_IN=P0_2(pin3)\n")
                 << "========================================\n";
    m_logStream->flush();
}

void Driver::CloseLogFile()
{
    if (m_logStream != NULL) {
        m_logStream->flush();
        delete m_logStream;
        m_logStream = NULL;
    }
    if (m_logFile != NULL) {
        m_logFile->close();
        delete m_logFile;
        m_logFile = NULL;
    }
}

void Driver::Log(LogLevel level, const QString &text)
{
    if (level > m_logLevel)
        return;

    static const char *tags[] = { "ERROR", "INFO ", "DEBUG", "TRACE" };
    QString line = QString("[%1][%2] %3")
                   .arg(QDateTime::currentDateTime().toString("HH:mm:ss.zzz"))
                   .arg(tags[level])
                   .arg(text);

    if (m_logStream != NULL) {
        *m_logStream << line << "\n";
        // Debug/Trace 条目密集，逐条 flush 会拖慢 I2C 时序，留到事务结束统一落盘
        if (level <= LogInfo)
            m_logStream->flush();
    }

    emit LogMessage((int)level, text);
}

void Driver::FlushLog()
{
    if (m_logStream != NULL)
        m_logStream->flush();
}

void Driver::SetError(const QString &text)
{
    m_strError = text;
    Log(LogError, text);
    FlushLog();
}

// 状态寄存器位解析，排查 1-Wire 问题时最常看的就是它
QString Driver::StatusToString(quint8 status)
{
    return QString("%1 [1WB=%2 PPD=%3 SD=%4 LL=%5 RST=%6 SBR=%7 TSB=%8 DIR=%9]")
            .arg(Hex(status))
            .arg((status >> 0) & 1).arg((status >> 1) & 1)
            .arg((status >> 2) & 1).arg((status >> 3) & 1)
            .arg((status >> 4) & 1).arg((status >> 5) & 1)
            .arg((status >> 6) & 1).arg((status >> 7) & 1);
}

// ============================================================ 打开 / 关闭

bool Driver::Open()
{
    if (m_bOpen)
        return true;

    Log(LogInfo, QString::fromUtf8("正在打开设备 %1 ...").arg(m_description));

    m_instantDoCtrl = InstantDoCtrl::Create();
    if (m_instantDoCtrl == NULL) {
        SetError(QString::fromUtf8("创建 InstantDoCtrl 失败，请确认已安装研华 DAQNavi 驱动"));
        return false;
    }

    std::wstring description = m_description.toStdWString();
    DeviceInformation devInfo(description.c_str());
    ErrorCode ret = m_instantDoCtrl->setSelectedDevice(devInfo);
    if (ret != Success) {
        if (ret == ErrorPrivilegeNotAvailable)
            SetError(QString::fromUtf8("设备已被其它程序占用: ") + m_description);
        else if (ret == ErrorDeviceNotExist)
            SetError(QString::fromUtf8("设备不存在: ") + m_description);
        else
            SetError(QString::fromUtf8("打开设备失败，错误码 0x%1，设备 %2")
                     .arg((quint32)ret, 8, 16, QChar('0')).arg(m_description));
        Close();
        return false;
    }

    // 配置端口方向。PCIE-1751 按半字节配置方向:
    //   Port 0 -> 全部输入      (P0_2 = SDA_IN)
    //   Port 2 -> 低半字节输入 / 高半字节输出 (P2_6 = SCL, P2_7 = SDA_OUT)
    Array<DioPort> *ports = m_instantDoCtrl->getPortDirection();
    if (ports == NULL || ports->getCount() <= PORT_SCL) {
        SetError(QString::fromUtf8("读取端口方向配置失败"));
        Close();
        return false;
    }
    ports->getItem(PORT_SDA_IN).setDirection(Input);
    ports->getItem(PORT_SCL).setDirection(LinHout);

    // 回读确认方向真的写进去了(Input=0x00, LinHout=0xF0)
    quint8 dir0 = ports->getItem(PORT_SDA_IN).getDirectionMask();
    quint8 dir2 = ports->getItem(PORT_SCL).getDirectionMask();
    Log(LogDebug, QString::fromUtf8("端口方向已配置并回读: Port0 = %1(应为 0x00), Port2 = %2(应为 0xF0)%3")
        .arg(Hex(dir0)).arg(Hex(dir2))
        .arg((dir0 == 0x00 && dir2 == 0xF0) ? QString()
             : QString::fromUtf8("  <-- 方向未按预期生效，P2_6/P2_7 可能根本没有输出")));

    // 总线置为空闲态: SCL、SDA 均释放，由 2.2K 上拉为高
    SclHigh();
    SdaRelease();
    DelayMicroseconds(1000);

    // 注意: 读到 1 不足以证明验证板已上电 —— PCIE-1751 的 P0_2 内部自带 10k 上拉到 +5V，
    // 验证板断电时 74HCT07 输出高阻，P0_2 同样会读到 1。要确认供电请看 D1 指示灯或做 SDA 回环自检。
    quint8 idle = SdaRead();
    Log(LogDebug, QString::fromUtf8("总线空闲态回读 SDA_IN = %1%2")
        .arg(idle)
        .arg(idle ? QString::fromUtf8("(注意: 板卡内部有 10k 上拉，读到 1 不代表验证板已上电)")
                  : QString::fromUtf8("  <-- 异常，空闲时应为 1，SDA 被持续拉低")));

    m_bOpen = true;

    // 这里不访问 DS2482。板卡打开与器件通信是两件事，
    // 否则 I2C 不通时连引脚自检都无法进入。
    Log(LogInfo, QString::fromUtf8("板卡已就绪。可进行 SDA 回环自检 / SCL 方波输出 / 读取 DS2431 ID。"));
    FlushLog();
    return true;
}

// 复位 DS2482 并开启有源上拉。这是最小的 I2C 链路验证。
bool Driver::InitDs2482()
{
    if (!m_bOpen) {
        SetError(QString::fromUtf8("设备尚未打开"));
        return false;
    }

    if (!Ds2482Reset())
        return false;
    if (!Ds2482WriteConfig(0x01))       // APU = 1
        return false;

    Log(LogInfo, QString::fromUtf8("DS2482-100 已复位并开启有源上拉(APU)，I2C 链路正常"));
    FlushLog();
    return true;
}

void Driver::Close()
{
    if (m_instantDoCtrl != NULL) {
        m_instantDoCtrl->Dispose();
        m_instantDoCtrl = NULL;
        Log(LogInfo, QString::fromUtf8("设备已关闭"));
    }
    m_bOpen = false;
    FlushLog();
}

// ============================================================ 底层位读写

bool Driver::WriteBit(int32_t port, int32_t bit, quint8 value)
{
    if (m_instantDoCtrl == NULL)
        return false;

    ErrorCode ret = m_instantDoCtrl->WriteBit(port, bit, value);
    if (ret != Success) {
        ++m_nIoErrors;
        if (m_nIoErrors <= 5)       // 只记前几次，避免刷屏并拖慢时序
            Log(LogError, QString::fromUtf8("WriteBit(Port%1, bit%2, %3) 失败，错误码 0x%4")
                .arg(port).arg(bit).arg(value)
                .arg((quint32)ret, 8, 16, QChar('0')));
        return false;
    }
    return true;
}

quint8 Driver::ReadBit(int32_t port, int32_t bit)
{
    if (m_instantDoCtrl == NULL)
        return 1;

    quint8 data = 1;
    ErrorCode ret = m_instantDoCtrl->ReadBit(port, bit, &data);
    if (ret != Success) {
        ++m_nIoErrors;
        if (m_nIoErrors <= 5)
            Log(LogError, QString::fromUtf8("ReadBit(Port%1, bit%2) 失败，错误码 0x%3")
                .arg(port).arg(bit).arg((quint32)ret, 8, 16, QChar('0')));
    }
    return data;
}

// 用通信时真正使用的函数连续翻转总线，验证 I2C 速度下的实际行为
void Driver::TestBusToggle(int nSeconds, bool bScl, QString &report)
{
    if (!m_bOpen) {
        report = QString::fromUtf8("设备尚未打开");
        return;
    }

    const QString name = bScl ? QString::fromUtf8("SCL(U2 的 pin4)")
                              : QString::fromUtf8("SDA(U2 的 pin5)");
    Log(LogInfo, QString::fromUtf8("开始 %1 高速翻转，持续 %2 秒 ...").arg(name).arg(nSeconds));

    m_nIoErrors = 0;
    QElapsedTimer timer;
    timer.start();
    qint64 nCycles = 0;

    while (timer.elapsed() < (qint64)nSeconds * 1000) {
        if (bScl) {
            SclHigh();
            SclLow();
        } else {
            SdaRelease();
            SdaLow();
        }
        ++nCycles;
    }

    if (bScl)
        SclHigh();
    else
        SdaRelease();

    double ms = (double)timer.elapsed();
    double freq = (ms > 0) ? (nCycles * 1000.0 / ms) : 0.0;

    report = QString::fromUtf8("%1 高速翻转结束: %2 个周期 / %3 ms，实测频率 %4 Hz，DAQNavi 错误 %5 次")
             .arg(name).arg(nCycles).arg((qint64)ms)
             .arg(freq, 0, 'f', 0).arg(m_nIoErrors);
    report += QString::fromUtf8(
        "\n请在翻转期间用万用表直流档测该引脚: 占空比 50%，读数应约为电源的一半(约 2.5V)。"
        "\n  读到约 2.5V   -> 该引脚在 I2C 速度下确实在翻转"
        "\n  读到 0V 或 5V -> 引脚卡住，通信速度下并没有真正动作");

    Log(LogInfo, report);
    FlushLog();
}

// ============================================================ I2C 位操作层
// 74HCT07 非反相开漏: 写 0 拉低总线, 写 1 释放总线

void Driver::SclLow()
{
    WriteBit(PORT_SCL, BIT_SCL, 0);
    DelayMicroseconds(m_nBitDelayUs);
}

void Driver::SclHigh()
{
    WriteBit(PORT_SCL, BIT_SCL, 1);
    DelayMicroseconds(m_nBitDelayUs);
}

void Driver::SdaLow()
{
    WriteBit(PORT_SDA_OUT, BIT_SDA_OUT, 0);
    DelayMicroseconds(m_nBitDelayUs);
}

void Driver::SdaRelease()
{
    WriteBit(PORT_SDA_OUT, BIT_SDA_OUT, 1);
    DelayMicroseconds(m_nBitDelayUs);
}

quint8 Driver::SdaRead()
{
    return ReadBit(PORT_SDA_IN, BIT_SDA_IN) ? 1 : 0;
}

// START: SCL 为高时 SDA 由高变低
void Driver::I2cStart()
{
    SdaRelease();
    SclHigh();
    SdaLow();
    if (m_logLevel >= LogTrace) {
        // 此刻 SDA 正被主机拉低，回读应为 0；若仍为 1 则 SDA 驱动链路未通
        quint8 rb = SdaRead();
        Log(LogTrace, QString::fromUtf8("  I2C START (拉低 SDA 后回读 = %1，应为 0)%2")
            .arg(rb)
            .arg(rb ? QString::fromUtf8("  <-- SDA 拉不低，从机根本收不到 START") : QString()));
    }
    SclLow();
}

// STOP: SCL 为高时 SDA 由低变高
void Driver::I2cStop()
{
    SdaLow();
    SclHigh();
    SdaRelease();
    Log(LogTrace, QString::fromUtf8("  I2C STOP"));
}

// 写一个字节，高位在前；返回从机是否应答
// Trace 级会在每个位的 SCL 高电平期间回读 SDA_IN。I2C 是线与总线，
// 主机拉低时自己也应读回 0；若"写 0 却读回 1"，说明 SDA 驱动链路没通。
bool Driver::I2cWriteByte(quint8 data)
{
    bool bTrace = (m_logLevel >= LogTrace);
    QString bits;
    int nMismatch = 0;

    for (int i = 7; i >= 0; --i) {
        quint8 bit = (quint8)((data >> i) & 0x01);
        if (bit)
            SdaRelease();
        else
            SdaLow();
        SclHigh();
        if (bTrace) {
            quint8 rb = SdaRead();
            if (rb != bit)
                ++nMismatch;
            bits += QString("%1/%2 ").arg(bit).arg(rb);
        }
        SclLow();
    }

    // 第 9 个时钟读应答位，低电平为 ACK
    SdaRelease();
    SclHigh();
    quint8 ack = SdaRead();
    SclLow();

    if (bTrace) {
        Log(LogTrace, QString::fromUtf8("  I2C 写 %1  位(写/回读): %2 -> %3")
            .arg(Hex(data)).arg(bits.trimmed()).arg(ack == 0 ? "ACK" : "NACK"));
        if (nMismatch > 0)
            Log(LogTrace, QString::fromUtf8(
                "    ^ 有 %1 个位写入与回读不一致。写 0 却读回 1 = SDA 拉不低，"
                "请查验证板供电(D1)、共地、74HCT07 的 2A(pin3)/2Y(pin4) 焊接")
                .arg(nMismatch));
    } else {
        Log(LogDebug, QString::fromUtf8("  I2C 写 %1 -> %2")
            .arg(Hex(data)).arg(ack == 0 ? "ACK" : "NACK"));
    }

    return (ack == 0);
}

// 读一个字节，高位在前；bAck 为 true 时主机回 ACK
quint8 Driver::I2cReadByte(bool bAck)
{
    quint8 data = 0;

    SdaRelease();
    for (int i = 7; i >= 0; --i) {
        SclHigh();
        if (SdaRead())
            data |= (quint8)(1 << i);
        SclLow();
    }

    if (bAck)
        SdaLow();
    else
        SdaRelease();
    SclHigh();
    SclLow();
    SdaRelease();

    Log(LogTrace, QString::fromUtf8("  I2C 读 %1 -> 主机回 %2")
        .arg(Hex(data)).arg(bAck ? "ACK" : "NACK"));

    return data;
}

// ============================================================ 硬件自检

void Driver::SetSclLevel(bool bHigh)
{
    WriteBit(PORT_SCL, BIT_SCL, bHigh ? 1 : 0);
    Log(LogInfo, QString::fromUtf8("SCL(P2_6/pin25) 置为 %1，请用万用表测量验证板 SCL 网络")
        .arg(bHigh ? QString::fromUtf8("高(约 5V)") : QString::fromUtf8("低(约 0V)")));
}

void Driver::SetSdaLevel(bool bHigh)
{
    WriteBit(PORT_SDA_OUT, BIT_SDA_OUT, bHigh ? 1 : 0);
    Log(LogInfo, QString::fromUtf8("SDA(P2_7/pin26) 置为 %1，请把表笔直接压在 DS2482 的 SDA(pin5) 上测量")
        .arg(bHigh ? QString::fromUtf8("释放(上拉为高，约 5V)") : QString::fromUtf8("拉低(约 0V)")));
}

void Driver::TestExternalPullLow(int nSeconds, QString &report)
{
    if (!m_bOpen) {
        report = QString::fromUtf8("设备尚未打开");
        return;
    }

    // 主机完全释放总线，之后 SDA 的电平只由外部决定
    SclHigh();
    SdaRelease();
    DelayMicroseconds(1000);

    m_nIoErrors = 0;
    Log(LogInfo, QString::fromUtf8("SDA 已释放，开始监视 %1 秒。"
                                   "请在此期间用导线把 U2 的 pin5 短接到 GND。").arg(nSeconds));

    QElapsedTimer timer;
    timer.start();
    int nSamples = 0, nLow = 0;
    quint8 last = 0xFF;

    while (timer.elapsed() < (qint64)nSeconds * 1000) {
        quint8 v = SdaRead();
        ++nSamples;
        if (v == 0)
            ++nLow;
        if (v != last) {
            Log(LogDebug, QString::fromUtf8("  [%1 ms] SDA_IN = %2")
                .arg(timer.elapsed()).arg(v));
            last = v;
        }
        DelayMicroseconds(200000);   // 200ms
    }

    if (nLow > 0) {
        report = QString::fromUtf8(
            "外部拉低测试: 通过。%1/%2 次采样读到 0。"
            "\n回读通道正常(SDA 总线 -> 74HCT07 的 3A -> 3Y -> P0_2)，"
            "说明主机确实能感知外部器件拉低 SDA，ACK 检测路径没有问题。")
            .arg(nLow).arg(nSamples);
    } else {
        report = QString::fromUtf8(
            "外部拉低测试: 未检测到任何低电平(%1 次采样全为 1)。"
            "\n如果确实短接了 U2 的 pin5 到 GND，那么问题就在这里:"
            "\n  74HCT07 的 3A(pin5) 没有真正接到 SDA 总线。"
            "\n  这条路径此前从未被验证过 —— 回环自检和逐位回读都不经过它，"
            "\n  但 ACK 检测完全依赖它，因此表现就是「能发不能收」、永远 NACK。"
            "\n请断电测量: 74HCT07 的 pin5(3A) 与 pin4(2Y) 之间应为 0 欧姆(同一网络)，"
            "以及 74HCT07 的 pin5 与 U2 的 pin5 之间也应为 0 欧姆。")
            .arg(nSamples);
    }

    Log(LogInfo, report);
    FlushLog();
}

bool Driver::TestSdaLoopback(QString &report)
{
    if (!m_bOpen) {
        report = QString::fromUtf8("设备尚未打开");
        return false;
    }

    Log(LogInfo, QString::fromUtf8("开始 SDA 回环自检 ..."));

    SdaRelease();
    DelayMicroseconds(500);
    quint8 rel1 = SdaRead();        // 期望 1

    SdaLow();
    DelayMicroseconds(500);
    quint8 low = SdaRead();         // 期望 0

    SdaRelease();
    DelayMicroseconds(500);
    quint8 rel2 = SdaRead();        // 期望 1

    Log(LogDebug, QString::fromUtf8("  释放 -> %1，拉低 -> %2，再释放 -> %3")
        .arg(rel1).arg(low).arg(rel2));

    bool bPass = (rel1 == 1 && low == 0 && rel2 == 1);

    report = QString::fromUtf8("SDA 回环自检: 释放=%1(应为1)  拉低=%2(应为0)  再释放=%3(应为1)  ->  %4\n")
             .arg(rel1).arg(low).arg(rel2)
             .arg(bPass ? QString::fromUtf8("通过") : QString::fromUtf8("失败"));

    if (bPass) {
        report += QString::fromUtf8(
            "SDA 驱动与回读链路正常(P2_7 -> 74HCT07 CH2 -> SDA -> CH3 -> P0_2)。\n"
            "若 I2C 仍无应答，问题很可能在 SCL 一侧或 DS2482 供电/地址，"
            "请用下面的 SCL 方波输出配合万用表检查。");
    } else if (low == 1) {
        report += QString::fromUtf8(
            "SDA 拉不低。注意: P0_2 恒读回 1 也可能是板卡内部 10k 上拉造成的假象，\n"
            "并不能说明验证板已上电。按以下顺序排查:\n"
            "  1) 验证板 J1 的 +5V 电源是否接入、D1 电源指示灯是否点亮(REV01 为独立供电)\n"
            "  2) 74HCT07 的 VCC(pin14) / GND(pin7) 是否焊接良好\n"
            "  3) 2A(pin3) 是否接到 J1.4(P2_7)，2Y(pin4) 是否接到 SDA 网络\n"
            "  4) 未用通道输入 4A/5A/6A(pin 9/11/13) 是否确实接地\n"
            "  5) 用万用表测 SDA 网络: 空闲应约 5V，本自检拉低期间应约 0V");
    } else {
        report += QString::fromUtf8(
            "SDA 无法回到高电平，说明总线被持续拉低。请检查:\n"
            "  1) SDA 网络是否对地短路(焊锡连桥)\n"
            "  2) 上拉电阻 R2(2.2K) 是否焊接、是否确实接到 +5V\n"
            "  3) DS2482 的 SDA(pin5) 是否被损坏而常拉低");
    }

    Log(LogInfo, report);
    FlushLog();
    return bPass;
}

// 扫描整个 7 位地址空间。DS2482-100 由 AD0/AD1 决定地址，四种组合分别是
// 0x18(都接地) / 0x19 / 0x1A / 0x1B；若地址脚虚焊，地址会落在后三个之一。
bool Driver::ScanI2cBus(QString &report)
{
    if (!m_bOpen) {
        report = QString::fromUtf8("设备尚未打开");
        return false;
    }

    // 扫描共 112 个地址，逐位日志会刷屏，这里临时压到 Info 级
    LogLevel saved = m_logLevel;
    m_logLevel = LogInfo;

    Log(LogInfo, QString::fromUtf8("开始扫描 I2C 总线(0x08 ~ 0x77) ..."));

    QStringList found;
    for (quint8 addr = 0x08; addr <= 0x77; ++addr) {
        I2cStart();
        bool ack = I2cWriteByte((quint8)(addr << 1));   // 写方向
        I2cStop();
        if (ack)
            found << Hex(addr);
    }

    m_logLevel = saved;

    if (!found.isEmpty()) {
        report = QString::fromUtf8("扫描到 %1 个从机: %2\n")
                 .arg(found.count()).arg(found.join(", "));
        if (found.contains(Hex(0x18))) {
            report += QString::fromUtf8(
                "其中 0x18 正是 DS2482-100 的预期地址，I2C 链路正常。");
        } else {
            report += QString::fromUtf8(
                "但没有 0x18。DS2482-100 的地址由 AD0(pin8)/AD1(pin7) 决定:\n"
                "  两脚都接地 = 0x18，AD0 悬空/拉高 = 0x19，AD1 = 0x1A，两者都 = 0x1B。\n"
                "若扫到的是 0x19/0x1A/0x1B，说明芯片是好的，只是地址脚没有可靠接地。");
        }
    } else {
        report = QString::fromUtf8(
            "全部 112 个地址均无应答。SDA 与 SCL 通路都已验证正常，"
            "因此问题集中在 DS2482 本身，按以下顺序实测(表笔要直接搭在芯片引脚上，"
            "不要测 74HCT07 的输出端):\n"
            "  1) U2 的 VCC(pin1) 对 GND 是否为 5V  <-- 最可能。R1/R2 上拉接的是 5V 网络，\n"
            "     即使 5V 到 pin1 这一段断开，总线仍有高电平，前面的自检照样通过\n"
            "  2) U2 的 SCL(pin4)：点 SCL 方波时该引脚是否跟着跳变(验证不是虚焊)\n"
            "  3) U2 的 SDA(pin5)：空闲应约 5V\n"
            "  4) U2 的 GND(pin3) 对地是否导通\n"
            "  5) U2 的 AD0(pin8)/AD1(pin7) 对地应为 0V\n"
            "  上述都正常则考虑 U2 焊接假焊或芯片本身问题，可补焊后重试。");
    }

    Log(LogInfo, report);
    FlushLog();
    return !found.isEmpty();
}

// ============================================================ DS2482-100 层

bool Driver::Ds2482Reset()
{
    m_nIoErrors = 0;
    Log(LogDebug, QString::fromUtf8("DS2482 Device Reset (0xF0)"));

    I2cStart();
    bool ok = I2cWriteByte(DS2482_ADDR_W) && I2cWriteByte(CMD_DRST);
    I2cStop();
    if (!ok) {
        SetError(QString::fromUtf8("DS2482 无应答(从机地址 0x18)，请检查 I2C 接线与总线电平")
                 + (m_nIoErrors > 0
                    ? QString::fromUtf8("  [注意: 本次有 %1 次 DAQNavi 读写失败]").arg(m_nIoErrors)
                    : QString::fromUtf8("  [DAQNavi 读写全部成功]")));
        return false;
    }

    // Device Reset 后读指针指向状态寄存器，RST 位应为 1
    quint8 status = 0;
    if (!Ds2482ReadRegister(status))
        return false;

    Log(LogDebug, QString::fromUtf8("  复位后状态寄存器 = ") + StatusToString(status));

    if (!(status & ST_RST)) {
        SetError(QString::fromUtf8("DS2482 复位后 RST 位未置 1，状态寄存器 = ") + Hex(status));
        return false;
    }
    return true;
}

// 配置字节要求高四位为低四位的反码
bool Driver::Ds2482WriteConfig(quint8 cfg)
{
    quint8 byte = (quint8)(((~cfg) << 4) | (cfg & 0x0F));
    Log(LogDebug, QString::fromUtf8("DS2482 Write Configuration (0xD2)，配置 %1，实际写入 %2")
        .arg(Hex(cfg & 0x0F)).arg(Hex(byte)));

    I2cStart();
    bool ok = I2cWriteByte(DS2482_ADDR_W) && I2cWriteByte(CMD_WCFG) && I2cWriteByte(byte);
    I2cStop();
    if (!ok) {
        SetError(QString::fromUtf8("DS2482 写配置寄存器无应答"));
        return false;
    }

    // 写配置后读指针指向配置寄存器，读回校验(高四位读出恒为 0)
    quint8 readBack = 0;
    if (!Ds2482ReadRegister(readBack))
        return false;

    Log(LogDebug, QString::fromUtf8("  配置寄存器回读 = ") + Hex(readBack));

    if ((readBack & 0x0F) != (cfg & 0x0F)) {
        SetError(QString::fromUtf8("DS2482 配置寄存器回读不符: 期望 %1，实际 %2")
                 .arg(Hex(cfg & 0x0F)).arg(Hex(readBack)));
        return false;
    }
    return true;
}

bool Driver::Ds2482SetReadPointer(quint8 code)
{
    Log(LogTrace, QString::fromUtf8("DS2482 Set Read Pointer (0xE1) -> %1").arg(Hex(code)));

    I2cStart();
    bool ok = I2cWriteByte(DS2482_ADDR_W) && I2cWriteByte(CMD_SRP) && I2cWriteByte(code);
    I2cStop();
    if (!ok) {
        SetError(QString::fromUtf8("DS2482 设置读指针无应答，指针代码 ") + Hex(code));
        return false;
    }
    return true;
}

// 读当前读指针所指的寄存器
bool Driver::Ds2482ReadRegister(quint8 &value)
{
    I2cStart();
    if (!I2cWriteByte(DS2482_ADDR_R)) {
        I2cStop();
        SetError(QString::fromUtf8("DS2482 读操作无应答(从机地址 0x18)"));
        return false;
    }
    value = I2cReadByte(false);     // 最后一个字节回 NACK
    I2cStop();
    return true;
}

// 轮询状态寄存器直到 1WB 清零。DS2482 不做时钟拉伸，必须靠轮询等待。
// 注意: 每个 1-Wire 命令执行后读指针会自动指向状态寄存器(0xF0)，故此处无需再发 Set Read Pointer。
bool Driver::Ds2482WaitNotBusy(quint8 &status, int nTimeoutMs)
{
    LARGE_INTEGER freq, start, now;
    QueryPerformanceFrequency(&freq);
    QueryPerformanceCounter(&start);
    __int64 limit = (__int64)((double)nTimeoutMs * freq.QuadPart / 1000.0);

    int nPoll = 0;
    for (;;) {
        if (!Ds2482ReadRegister(status))
            return false;
        ++nPoll;

        if (!(status & ST_1WB)) {
            Log(LogTrace, QString::fromUtf8("  轮询 %1 次后 1-Wire 空闲，状态 = %2")
                .arg(nPoll).arg(StatusToString(status)));
            return true;
        }

        QueryPerformanceCounter(&now);
        if ((now.QuadPart - start.QuadPart) > limit) {
            SetError(QString::fromUtf8("等待 DS2482 1-Wire 空闲超时(%1 ms，轮询 %2 次)，状态 = %3")
                     .arg(nTimeoutMs).arg(nPoll).arg(StatusToString(status)));
            return false;
        }
    }
}

bool Driver::OwReset(bool &bPresence)
{
    Log(LogDebug, QString::fromUtf8("1-Wire Reset (0xB4)"));

    I2cStart();
    bool ok = I2cWriteByte(DS2482_ADDR_W) && I2cWriteByte(CMD_1WRS);
    I2cStop();
    if (!ok) {
        SetError(QString::fromUtf8("DS2482 1-Wire 复位命令无应答"));
        return false;
    }

    quint8 status = 0;
    if (!Ds2482WaitNotBusy(status))
        return false;

    Log(LogDebug, QString::fromUtf8("  复位结果状态 = ") + StatusToString(status));

    if (status & ST_SD) {
        SetError(QString::fromUtf8("1-Wire 总线短路(SD = 1)，请检查 IO 线是否对地短路"));
        return false;
    }
    bPresence = (status & ST_PPD) != 0;
    return true;
}

bool Driver::OwWriteByte(quint8 data)
{
    Log(LogDebug, QString::fromUtf8("1-Wire 写字节 (0xA5) -> ") + Hex(data));

    I2cStart();
    bool ok = I2cWriteByte(DS2482_ADDR_W) && I2cWriteByte(CMD_1WWB) && I2cWriteByte(data);
    I2cStop();
    if (!ok) {
        SetError(QString::fromUtf8("DS2482 1-Wire 写字节命令无应答，数据 ") + Hex(data));
        return false;
    }

    quint8 status = 0;
    return Ds2482WaitNotBusy(status);
}

bool Driver::OwReadByte(quint8 &data)
{
    I2cStart();
    bool ok = I2cWriteByte(DS2482_ADDR_W) && I2cWriteByte(CMD_1WRB);
    I2cStop();
    if (!ok) {
        SetError(QString::fromUtf8("DS2482 1-Wire 读字节命令无应答"));
        return false;
    }

    quint8 status = 0;
    if (!Ds2482WaitNotBusy(status))
        return false;

    // 读取结果保存在读数据寄存器中，需要先把读指针指过去
    if (!Ds2482SetReadPointer(PTR_DATA))
        return false;
    if (!Ds2482ReadRegister(data))
        return false;

    Log(LogDebug, QString::fromUtf8("1-Wire 读字节 (0x96) <- ") + Hex(data));
    return true;
}

// ============================================================ DS2431

bool Driver::ReadDs2431Rom(quint8 rom[8])
{
    if (!m_bOpen) {
        SetError(QString::fromUtf8("设备尚未打开"));
        return false;
    }

    QElapsedTimer timer;
    timer.start();
    Log(LogInfo, QString::fromUtf8("开始读取 DS2431 ROM ..."));

    // 每次读取都从干净状态开始，避免上一次操作的残留影响
    if (!InitDs2482()) {
        FlushLog();
        return false;
    }

    bool bPresence = false;
    if (!OwReset(bPresence)) {
        FlushLog();
        return false;
    }
    if (!bPresence) {
        SetError(QString::fromUtf8("未检测到 1-Wire 应答脉冲(PPD = 0)，DS2431 可能未接入或 IO 线断开"));
        FlushLog();
        return false;
    }
    Log(LogDebug, QString::fromUtf8("  检测到应答脉冲(PPD = 1)，总线上有 1-Wire 器件"));

    if (!OwWriteByte(OW_CMD_READ_ROM)) {
        FlushLog();
        return false;
    }

    for (int i = 0; i < 8; ++i) {
        if (!OwReadByte(rom[i])) {
            SetError(QString::fromUtf8("读取 ROM 第 %1 字节失败: %2").arg(i).arg(m_strError));
            FlushLog();
            return false;
        }
    }

    QString strRaw;
    for (int i = 0; i < 8; ++i)
        strRaw += QString("%1 ").arg(rom[i], 2, 16, QChar('0')).toUpper();
    Log(LogInfo, QString::fromUtf8("ROM 原始字节: ") + strRaw.trimmed());

    if (rom[0] != DS2431_FAMILY_CODE) {
        SetError(QString::fromUtf8("家族码错误: 期望 0x2D(DS2431)，实际 %1").arg(Hex(rom[0])));
        FlushLog();
        return false;
    }

    quint8 crc = Crc8(rom, 7);
    if (crc != rom[7]) {
        SetError(QString::fromUtf8("ROM CRC 校验失败: 计算值 %1，读出值 %2")
                 .arg(Hex(crc)).arg(Hex(rom[7])));
        FlushLog();
        return false;
    }

    m_strError.clear();
    Log(LogInfo, QString::fromUtf8("读取成功: %1，家族码与 CRC 校验通过，耗时 %2 ms")
        .arg(RomToString(rom)).arg(timer.elapsed()));
    FlushLog();
    return true;
}

// Dallas/Maxim CRC-8, 多项式 X^8 + X^5 + X^4 + 1 (反向 0x8C)
quint8 Driver::Crc8(const quint8 *data, int len)
{
    quint8 crc = 0;
    for (int i = 0; i < len; ++i) {
        quint8 inbyte = data[i];
        for (int j = 0; j < 8; ++j) {
            quint8 mix = (quint8)((crc ^ inbyte) & 0x01);
            crc >>= 1;
            if (mix)
                crc ^= 0x8C;
            inbyte >>= 1;
        }
    }
    return crc;
}

// 按 1-Wire 习惯显示: 家族码 - 48 位序列号(高位在前) - CRC
QString Driver::RomToString(const quint8 rom[8])
{
    QString sn;
    for (int i = 6; i >= 1; --i)
        sn += QString("%1").arg(rom[i], 2, 16, QChar('0'));

    return QString("%1-%2-%3")
            .arg(rom[0], 2, 16, QChar('0'))
            .arg(sn)
            .arg(rom[7], 2, 16, QChar('0'))
            .toUpper();
}

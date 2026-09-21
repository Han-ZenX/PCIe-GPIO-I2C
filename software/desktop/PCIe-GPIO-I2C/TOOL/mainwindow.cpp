#include "mainwindow.h"
#include "ui_mainwindow.h"
#include "driver.h"

#include <QDateTime>
#include <QDesktopServices>
#include <QDir>
#include <QUrl>
#include <QThread>

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
    , ui(new Ui::MainWindow)
    , m_driver(NULL)
{
    ui->setupUi(this);

    connect(ui->btnOpen,       SIGNAL(clicked()), this, SLOT(OnOpenDevice()));
    connect(ui->btnClose,      SIGNAL(clicked()), this, SLOT(OnCloseDevice()));
    connect(ui->btnReadId,     SIGNAL(clicked()), this, SLOT(OnReadId()));
    connect(ui->btnClearLog,   SIGNAL(clicked()), ui->editLog, SLOT(clear()));
    connect(ui->btnOpenLogDir, SIGNAL(clicked()), this, SLOT(OnOpenLogDir()));
    connect(ui->comboLevel,    SIGNAL(currentIndexChanged(int)), this, SLOT(OnLogLevelChanged(int)));
    connect(ui->spinDelay,     SIGNAL(valueChanged(int)), this, SLOT(OnBitDelayChanged(int)));
    connect(ui->btnScan,       SIGNAL(clicked()), this, SLOT(OnScanBus()));
    connect(ui->btnTestI2c,    SIGNAL(clicked()), this, SLOT(OnTestI2c()));
    connect(ui->btnSdaTest,    SIGNAL(clicked()), this, SLOT(OnSdaSelfTest()));
    connect(ui->btnSclWave,    SIGNAL(clicked()), this, SLOT(OnSclWave()));
    connect(ui->btnSdaWave,    SIGNAL(clicked()), this, SLOT(OnSdaWave()));
    connect(ui->btnToggleScl,  SIGNAL(clicked()), this, SLOT(OnToggleScl()));
    connect(ui->btnPullLow,    SIGNAL(clicked()), this, SLOT(OnPullLowTest()));

    AppendLog(Driver::LogInfo,
              QString::fromUtf8("就绪。引脚映射：SCL=P2_6(pin25)，SDA_OUT=P2_7(pin26)，SDA_IN=P0_2(pin3)。"));
    AppendLog(Driver::LogInfo,
              QString::fromUtf8("提示：日志级别选 Debug 可看到 DS2482 命令与状态寄存器，选 Trace 可看到每个 I2C 字节。"));
}

MainWindow::~MainWindow()
{
    if (m_driver != NULL) {
        delete m_driver;
        m_driver = NULL;
    }
    delete ui;
}

// 界面日志。Debug/Trace 条目很多，默认不上屏，只写入日志文件。
void MainWindow::AppendLog(int level, const QString &text)
{
    if (level >= Driver::LogDebug && !ui->checkShowDetail->isChecked())
        return;

    static const char *tags[] = { "ERROR", "INFO ", "DEBUG", "TRACE" };
    if (level < 0 || level > Driver::LogTrace)
        level = Driver::LogInfo;

    ui->editLog->appendPlainText(
        QString("[%1][%2] %3")
        .arg(QDateTime::currentDateTime().toString("HH:mm:ss.zzz"))
        .arg(tags[level])
        .arg(text));
}

void MainWindow::OnDriverLog(int level, const QString &text)
{
    AppendLog(level, text);
}

void MainWindow::UpdateUiState()
{
    bool bOpen = (m_driver != NULL && m_driver->IsOpen());
    ui->btnOpen->setEnabled(!bOpen);
    ui->btnClose->setEnabled(bOpen);
    ui->btnReadId->setEnabled(bOpen);
    ui->btnScan->setEnabled(bOpen);
    ui->btnTestI2c->setEnabled(bOpen);
    ui->btnSdaTest->setEnabled(bOpen);
    ui->btnSclWave->setEnabled(bOpen);
    ui->btnSdaWave->setEnabled(bOpen);
    ui->btnToggleScl->setEnabled(bOpen);
    ui->btnPullLow->setEnabled(bOpen);
    ui->editBID->setEnabled(!bOpen);
}

void MainWindow::OnOpenDevice()
{
    if (m_driver != NULL) {
        delete m_driver;
        m_driver = NULL;
    }

    QString strBID = ui->editBID->text().trimmed();
    if (strBID.isEmpty())
        strBID = "0";

    m_driver = new Driver(strBID);
    connect(m_driver, SIGNAL(LogMessage(int,QString)), this, SLOT(OnDriverLog(int,QString)));
    m_driver->SetLogLevel((Driver::LogLevel)ui->comboLevel->currentIndex());
    m_driver->SetBitDelayUs(ui->spinDelay->value());

    if (!m_driver->LogFilePath().isEmpty())
        AppendLog(Driver::LogInfo, QString::fromUtf8("日志文件：") + m_driver->LogFilePath());

    if (!m_driver->Open()) {
        AppendLog(Driver::LogError, QString::fromUtf8("打开失败：") + m_driver->LastError());
        delete m_driver;
        m_driver = NULL;
        UpdateUiState();
        return;
    }

    UpdateUiState();
}

void MainWindow::OnCloseDevice()
{
    if (m_driver != NULL) {
        delete m_driver;
        m_driver = NULL;
    }
    ui->editId->clear();
    UpdateUiState();
}

void MainWindow::OnReadId()
{
    if (m_driver == NULL)
        return;

    quint8 rom[8] = {0};
    if (!m_driver->ReadDs2431Rom(rom)) {
        ui->editId->clear();
        AppendLog(Driver::LogError, QString::fromUtf8("读取失败：") + m_driver->LastError());
        return;
    }

    ui->editId->setText(Driver::RomToString(rom));
}

void MainWindow::OnLogLevelChanged(int index)
{
    if (m_driver != NULL)
        m_driver->SetLogLevel((Driver::LogLevel)index);
}

void MainWindow::OnBitDelayChanged(int value)
{
    if (m_driver != NULL)
        m_driver->SetBitDelayUs(value);
}

void MainWindow::OnOpenLogDir()
{
    QString dir = (m_driver != NULL)
                  ? m_driver->LogDirPath()
                  : QCoreApplication::applicationDirPath() + "/Log";

    QDir d;
    if (!d.exists(dir))
        d.mkpath(dir);

    QDesktopServices::openUrl(QUrl::fromLocalFile(dir));
}

// SDA 回环自检: 软件即可判定 P2_7 -> 74HCT07 -> SDA -> P0_2 这条链路是否通
void MainWindow::OnSdaSelfTest()
{
    if (m_driver == NULL)
        return;

    QString report;
    bool bPass = m_driver->TestSdaLoopback(report);
    AppendLog(bPass ? Driver::LogInfo : Driver::LogError, report);
}

// SCL 没有回读通路，只能输出方波由万用表/示波器实测
void MainWindow::OnSclWave()
{
    if (m_driver == NULL)
        return;

    AppendLog(Driver::LogInfo,
              QString::fromUtf8("SCL 开始输出 1Hz 方波，持续 5 秒。请用万用表直流档测量验证板上 "
                                "74HCT07 的 1Y(pin2) 或 DS2482 的 SCL(pin4)，应在 0V 与 5V 之间跳变。"));

    ui->btnSclWave->setEnabled(false);
    for (int i = 0; i < 10; ++i) {
        m_driver->SetSclLevel((i % 2) != 0);
        QCoreApplication::processEvents();
        QThread::msleep(500);
    }
    m_driver->SetSclLevel(true);        // 结束后回到总线空闲态
    ui->btnSclWave->setEnabled(true);

    AppendLog(Driver::LogInfo,
              QString::fromUtf8("SCL 方波输出结束，已恢复为高电平(总线空闲态)。"
                                "若测量到电平始终不变，问题在 P2_6 -> 74HCT07 CH1 -> SCL 这条链路。"));
}

// 只验证 I2C 链路(复位 DS2482 + 写配置)，不涉及 1-Wire
void MainWindow::OnTestI2c()
{
    if (m_driver == NULL)
        return;

    if (!m_driver->InitDs2482())
        AppendLog(Driver::LogError, QString::fromUtf8("DS2482 测试失败：") + m_driver->LastError());
}

// 扫描全部 7 位地址，区分"芯片没工作"与"地址不是 0x18"
void MainWindow::OnScanBus()
{
    if (m_driver == NULL)
        return;

    QString report;
    bool bFound = m_driver->ScanI2cBus(report);
    AppendLog(bFound ? Driver::LogInfo : Driver::LogError, report);
}

// SDA 方波。回环自检的回路不经过 DS2482 的 pin5，只有在该引脚实测才能确认是否焊通。
void MainWindow::OnSdaWave()
{
    if (m_driver == NULL)
        return;

    AppendLog(Driver::LogInfo,
              QString::fromUtf8("SDA 开始输出 1Hz 方波，持续 5 秒。请把表笔直接压在 "
                                "DS2482 的 SDA(pin5) 上，应在 0V 与 5V 之间跳变。"));

    ui->btnSdaWave->setEnabled(false);
    for (int i = 0; i < 10; ++i) {
        m_driver->SetSdaLevel((i % 2) != 0);
        QCoreApplication::processEvents();
        QThread::msleep(500);
    }
    m_driver->SetSdaLevel(true);        // 结束后释放总线
    ui->btnSdaWave->setEnabled(true);

    AppendLog(Driver::LogInfo,
              QString::fromUtf8("SDA 方波输出结束，已释放为高电平。"
                                "若 pin5 上电平始终不变，说明该引脚虚焊 —— "
                                "这正是能骗过回环自检的那种故障。"));
}

// 用通信时真正使用的 SclHigh/SclLow 连续翻转，验证 I2C 速度下 SCL 是否真的在动
void MainWindow::OnToggleScl()
{
    if (m_driver == NULL)
        return;

    AppendLog(Driver::LogInfo,
              QString::fromUtf8("SCL 即将高速翻转 5 秒，请把万用表直流档压在 U2 的 pin4 上。"));

    ui->btnToggleScl->setEnabled(false);
    QCoreApplication::processEvents();

    QString report;
    m_driver->TestBusToggle(5, true, report);

    ui->btnToggleScl->setEnabled(true);
    AppendLog(Driver::LogInfo, report);
}

// 验证"外部器件拉低 SDA -> 主机可感知"这条路径，即 ACK 检测所依赖的通道
void MainWindow::OnPullLowTest()
{
    if (m_driver == NULL)
        return;

    AppendLog(Driver::LogInfo,
              QString::fromUtf8("即将释放 SDA 并监视 10 秒。请在此期间用导线把 U2 的 pin5 短接到 GND，"
                                "短接几秒后再松开。"));

    ui->btnPullLow->setEnabled(false);
    QCoreApplication::processEvents();

    QString report;
    m_driver->TestExternalPullLow(10, report);

    ui->btnPullLow->setEnabled(true);
    AppendLog(Driver::LogInfo, report);
}

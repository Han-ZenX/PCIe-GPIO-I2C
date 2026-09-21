#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>

QT_BEGIN_NAMESPACE
namespace Ui { class MainWindow; }
QT_END_NAMESPACE

class Driver;

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    MainWindow(QWidget *parent = nullptr);
    ~MainWindow();

private slots:
    void OnOpenDevice();
    void OnCloseDevice();
    void OnReadId();
    void OnDriverLog(int level, const QString &text);
    void OnLogLevelChanged(int index);
    void OnBitDelayChanged(int value);
    void OnOpenLogDir();
    void OnScanBus();
    void OnTestI2c();
    void OnSdaSelfTest();
    void OnSclWave();
    void OnSdaWave();
    void OnToggleScl();
    void OnPullLowTest();

private:
    void AppendLog(int level, const QString &text);
    void UpdateUiState();

    Ui::MainWindow *ui;
    Driver *m_driver;
};
#endif // MAINWINDOW_H

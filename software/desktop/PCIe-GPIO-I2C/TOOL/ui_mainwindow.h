/********************************************************************************
** Form generated from reading UI file 'mainwindow.ui'
**
** Created by: Qt User Interface Compiler version 5.14.1
**
** WARNING! All changes made in this file will be lost when recompiling UI file!
********************************************************************************/

#ifndef UI_MAINWINDOW_H
#define UI_MAINWINDOW_H

#include <QtCore/QVariant>
#include <QtWidgets/QApplication>
#include <QtWidgets/QCheckBox>
#include <QtWidgets/QComboBox>
#include <QtWidgets/QHBoxLayout>
#include <QtWidgets/QLabel>
#include <QtWidgets/QLineEdit>
#include <QtWidgets/QMainWindow>
#include <QtWidgets/QPlainTextEdit>
#include <QtWidgets/QPushButton>
#include <QtWidgets/QSpacerItem>
#include <QtWidgets/QSpinBox>
#include <QtWidgets/QStatusBar>
#include <QtWidgets/QVBoxLayout>
#include <QtWidgets/QWidget>

QT_BEGIN_NAMESPACE

class Ui_MainWindow
{
public:
    QWidget *centralwidget;
    QVBoxLayout *verticalLayout;
    QHBoxLayout *layoutDevice;
    QLabel *labelBID;
    QLineEdit *editBID;
    QPushButton *btnOpen;
    QPushButton *btnClose;
    QLabel *labelDelay;
    QSpinBox *spinDelay;
    QSpacerItem *spacerDevice;
    QHBoxLayout *layoutRead;
    QPushButton *btnReadId;
    QPushButton *btnScan;
    QPushButton *btnTestI2c;
    QPushButton *btnSdaTest;
    QPushButton *btnSclWave;
    QPushButton *btnSdaWave;
    QPushButton *btnToggleScl;
    QPushButton *btnPullLow;
    QLabel *labelId;
    QLineEdit *editId;
    QHBoxLayout *layoutLog;
    QLabel *labelLevel;
    QComboBox *comboLevel;
    QCheckBox *checkShowDetail;
    QPushButton *btnClearLog;
    QPushButton *btnOpenLogDir;
    QSpacerItem *spacerLog;
    QPlainTextEdit *editLog;
    QStatusBar *statusbar;

    void setupUi(QMainWindow *MainWindow)
    {
        if (MainWindow->objectName().isEmpty())
            MainWindow->setObjectName(QString::fromUtf8("MainWindow"));
        MainWindow->resize(760, 560);
        centralwidget = new QWidget(MainWindow);
        centralwidget->setObjectName(QString::fromUtf8("centralwidget"));
        verticalLayout = new QVBoxLayout(centralwidget);
        verticalLayout->setObjectName(QString::fromUtf8("verticalLayout"));
        layoutDevice = new QHBoxLayout();
        layoutDevice->setObjectName(QString::fromUtf8("layoutDevice"));
        labelBID = new QLabel(centralwidget);
        labelBID->setObjectName(QString::fromUtf8("labelBID"));

        layoutDevice->addWidget(labelBID);

        editBID = new QLineEdit(centralwidget);
        editBID->setObjectName(QString::fromUtf8("editBID"));
        editBID->setMaximumSize(QSize(60, 16777215));

        layoutDevice->addWidget(editBID);

        btnOpen = new QPushButton(centralwidget);
        btnOpen->setObjectName(QString::fromUtf8("btnOpen"));

        layoutDevice->addWidget(btnOpen);

        btnClose = new QPushButton(centralwidget);
        btnClose->setObjectName(QString::fromUtf8("btnClose"));
        btnClose->setEnabled(false);

        layoutDevice->addWidget(btnClose);

        labelDelay = new QLabel(centralwidget);
        labelDelay->setObjectName(QString::fromUtf8("labelDelay"));

        layoutDevice->addWidget(labelDelay);

        spinDelay = new QSpinBox(centralwidget);
        spinDelay->setObjectName(QString::fromUtf8("spinDelay"));
        spinDelay->setMinimum(1);
        spinDelay->setMaximum(1000);
        spinDelay->setValue(5);

        layoutDevice->addWidget(spinDelay);

        spacerDevice = new QSpacerItem(40, 20, QSizePolicy::Expanding, QSizePolicy::Minimum);

        layoutDevice->addItem(spacerDevice);


        verticalLayout->addLayout(layoutDevice);

        layoutRead = new QHBoxLayout();
        layoutRead->setObjectName(QString::fromUtf8("layoutRead"));
        btnReadId = new QPushButton(centralwidget);
        btnReadId->setObjectName(QString::fromUtf8("btnReadId"));
        btnReadId->setEnabled(false);

        layoutRead->addWidget(btnReadId);

        btnScan = new QPushButton(centralwidget);
        btnScan->setObjectName(QString::fromUtf8("btnScan"));
        btnScan->setEnabled(false);

        layoutRead->addWidget(btnScan);

        btnTestI2c = new QPushButton(centralwidget);
        btnTestI2c->setObjectName(QString::fromUtf8("btnTestI2c"));
        btnTestI2c->setEnabled(false);

        layoutRead->addWidget(btnTestI2c);

        btnSdaTest = new QPushButton(centralwidget);
        btnSdaTest->setObjectName(QString::fromUtf8("btnSdaTest"));
        btnSdaTest->setEnabled(false);

        layoutRead->addWidget(btnSdaTest);

        btnSclWave = new QPushButton(centralwidget);
        btnSclWave->setObjectName(QString::fromUtf8("btnSclWave"));
        btnSclWave->setEnabled(false);

        layoutRead->addWidget(btnSclWave);

        btnSdaWave = new QPushButton(centralwidget);
        btnSdaWave->setObjectName(QString::fromUtf8("btnSdaWave"));
        btnSdaWave->setEnabled(false);

        layoutRead->addWidget(btnSdaWave);

        btnToggleScl = new QPushButton(centralwidget);
        btnToggleScl->setObjectName(QString::fromUtf8("btnToggleScl"));
        btnToggleScl->setEnabled(false);

        layoutRead->addWidget(btnToggleScl);

        btnPullLow = new QPushButton(centralwidget);
        btnPullLow->setObjectName(QString::fromUtf8("btnPullLow"));
        btnPullLow->setEnabled(false);

        layoutRead->addWidget(btnPullLow);

        labelId = new QLabel(centralwidget);
        labelId->setObjectName(QString::fromUtf8("labelId"));

        layoutRead->addWidget(labelId);

        editId = new QLineEdit(centralwidget);
        editId->setObjectName(QString::fromUtf8("editId"));
        editId->setReadOnly(true);

        layoutRead->addWidget(editId);


        verticalLayout->addLayout(layoutRead);

        layoutLog = new QHBoxLayout();
        layoutLog->setObjectName(QString::fromUtf8("layoutLog"));
        labelLevel = new QLabel(centralwidget);
        labelLevel->setObjectName(QString::fromUtf8("labelLevel"));

        layoutLog->addWidget(labelLevel);

        comboLevel = new QComboBox(centralwidget);
        comboLevel->addItem(QString());
        comboLevel->addItem(QString());
        comboLevel->addItem(QString());
        comboLevel->addItem(QString());
        comboLevel->setObjectName(QString::fromUtf8("comboLevel"));

        layoutLog->addWidget(comboLevel);

        checkShowDetail = new QCheckBox(centralwidget);
        checkShowDetail->setObjectName(QString::fromUtf8("checkShowDetail"));

        layoutLog->addWidget(checkShowDetail);

        btnClearLog = new QPushButton(centralwidget);
        btnClearLog->setObjectName(QString::fromUtf8("btnClearLog"));

        layoutLog->addWidget(btnClearLog);

        btnOpenLogDir = new QPushButton(centralwidget);
        btnOpenLogDir->setObjectName(QString::fromUtf8("btnOpenLogDir"));

        layoutLog->addWidget(btnOpenLogDir);

        spacerLog = new QSpacerItem(40, 20, QSizePolicy::Expanding, QSizePolicy::Minimum);

        layoutLog->addItem(spacerLog);


        verticalLayout->addLayout(layoutLog);

        editLog = new QPlainTextEdit(centralwidget);
        editLog->setObjectName(QString::fromUtf8("editLog"));
        editLog->setReadOnly(true);
        editLog->setMaximumBlockCount(5000);

        verticalLayout->addWidget(editLog);

        MainWindow->setCentralWidget(centralwidget);
        statusbar = new QStatusBar(MainWindow);
        statusbar->setObjectName(QString::fromUtf8("statusbar"));
        MainWindow->setStatusBar(statusbar);

        retranslateUi(MainWindow);

        comboLevel->setCurrentIndex(1);


        QMetaObject::connectSlotsByName(MainWindow);
    } // setupUi

    void retranslateUi(QMainWindow *MainWindow)
    {
        MainWindow->setWindowTitle(QCoreApplication::translate("MainWindow", "PCIE-1751 \350\257\273\345\217\226 DS2431 ID", nullptr));
        labelBID->setText(QCoreApplication::translate("MainWindow", "\346\235\277\345\215\241 BID\357\274\232", nullptr));
        editBID->setText(QCoreApplication::translate("MainWindow", "0", nullptr));
        btnOpen->setText(QCoreApplication::translate("MainWindow", "\346\211\223\345\274\200\350\256\276\345\244\207", nullptr));
        btnClose->setText(QCoreApplication::translate("MainWindow", "\345\205\263\351\227\255\350\256\276\345\244\207", nullptr));
        labelDelay->setText(QCoreApplication::translate("MainWindow", "\344\275\215\345\273\266\346\227\266(us)\357\274\232", nullptr));
        btnReadId->setText(QCoreApplication::translate("MainWindow", "\350\257\273\345\217\226 DS2431 ID", nullptr));
        btnScan->setText(QCoreApplication::translate("MainWindow", "\346\211\253\346\217\217 I2C \345\234\260\345\235\200", nullptr));
        btnTestI2c->setText(QCoreApplication::translate("MainWindow", "\346\265\213\350\257\225 DS2482", nullptr));
        btnSdaTest->setText(QCoreApplication::translate("MainWindow", "SDA \345\233\236\347\216\257\350\207\252\346\243\200", nullptr));
        btnSclWave->setText(QCoreApplication::translate("MainWindow", "SCL \346\226\271\346\263\242(5\347\247\222)", nullptr));
        btnSdaWave->setText(QCoreApplication::translate("MainWindow", "SDA \346\226\271\346\263\242(5\347\247\222)", nullptr));
        btnToggleScl->setText(QCoreApplication::translate("MainWindow", "SCL \351\253\230\351\200\237\347\277\273\350\275\254", nullptr));
        btnPullLow->setText(QCoreApplication::translate("MainWindow", "SDA \345\244\226\351\203\250\346\213\211\344\275\216\346\265\213\350\257\225", nullptr));
        labelId->setText(QCoreApplication::translate("MainWindow", "ROM ID\357\274\232", nullptr));
        labelLevel->setText(QCoreApplication::translate("MainWindow", "\346\227\245\345\277\227\347\272\247\345\210\253\357\274\232", nullptr));
        comboLevel->setItemText(0, QCoreApplication::translate("MainWindow", "Error - \344\273\205\351\224\231\350\257\257", nullptr));
        comboLevel->setItemText(1, QCoreApplication::translate("MainWindow", "Info - \344\272\213\345\212\241\347\272\247", nullptr));
        comboLevel->setItemText(2, QCoreApplication::translate("MainWindow", "Debug - DS2482 \345\221\275\344\273\244\347\272\247", nullptr));
        comboLevel->setItemText(3, QCoreApplication::translate("MainWindow", "Trace - I2C \345\255\227\350\212\202\347\272\247", nullptr));

        checkShowDetail->setText(QCoreApplication::translate("MainWindow", "\347\225\214\351\235\242\346\230\276\347\244\272 Debug/Trace", nullptr));
        btnClearLog->setText(QCoreApplication::translate("MainWindow", "\346\270\205\347\251\272", nullptr));
        btnOpenLogDir->setText(QCoreApplication::translate("MainWindow", "\346\211\223\345\274\200\346\227\245\345\277\227\347\233\256\345\275\225", nullptr));
    } // retranslateUi

};

namespace Ui {
    class MainWindow: public Ui_MainWindow {};
} // namespace Ui

QT_END_NAMESPACE

#endif // UI_MAINWINDOW_H

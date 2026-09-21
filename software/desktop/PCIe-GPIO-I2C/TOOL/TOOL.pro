QT       += core gui

greaterThan(QT_MAJOR_VERSION, 4): QT += widgets

CONFIG += c++11

#源码为 UTF-8。MSVC 默认按本地代码页(GBK)存放窄字符串字面量，
#会让 QString::fromUtf8() 解码出乱码，因此强制源字符集与执行字符集均为 UTF-8。
win32-msvc*: QMAKE_CXXFLAGS += /utf-8

# The following define makes your compiler emit warnings if you use
# any Qt feature that has been marked deprecated (the exact warnings
# depend on your compiler). Please consult the documentation of the
# deprecated API in order to know how to port your code away from it.
DEFINES += QT_DEPRECATED_WARNINGS

# You can also make your code fail to compile if it uses deprecated APIs.
# In order to do so, uncomment the following line.
# You can also select to disable deprecated APIs only up to a certain version of Qt.
#DEFINES += QT_DISABLE_DEPRECATED_BEFORE=0x060000    # disables all the APIs deprecated before Qt 6.0.0

DESTDIR = ../bin #定义项目编译之后生成的结果文件的存放路径

#链接 Driver 库
INCLUDEPATH += $$PWD/../Driver
DEPENDPATH  += $$PWD/../Driver
LIBS        += -L$$PWD/../bin -lDriver

SOURCES += \
    main.cpp \
    mainwindow.cpp

HEADERS += \
    mainwindow.h

FORMS += \
    mainwindow.ui

# Default rules for deployment.
qnx: target.path = /tmp/$${TARGET}/bin
else: unix:!android: target.path = /opt/$${TARGET}/bin
!isEmpty(target.path): INSTALLS += target

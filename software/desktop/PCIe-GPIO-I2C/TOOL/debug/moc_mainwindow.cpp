/****************************************************************************
** Meta object code from reading C++ file 'mainwindow.h'
**
** Created by: The Qt Meta Object Compiler version 67 (Qt 5.14.1)
**
** WARNING! All changes made in this file will be lost!
*****************************************************************************/

#include <memory>
#include "../mainwindow.h"
#include <QtCore/qbytearray.h>
#include <QtCore/qmetatype.h>
#if !defined(Q_MOC_OUTPUT_REVISION)
#error "The header file 'mainwindow.h' doesn't include <QObject>."
#elif Q_MOC_OUTPUT_REVISION != 67
#error "This file was generated using the moc from 5.14.1. It"
#error "cannot be used with the include files from this version of Qt."
#error "(The moc has changed too much.)"
#endif

QT_BEGIN_MOC_NAMESPACE
QT_WARNING_PUSH
QT_WARNING_DISABLE_DEPRECATED
struct qt_meta_stringdata_MainWindow_t {
    QByteArrayData data[20];
    char stringdata0[212];
};
#define QT_MOC_LITERAL(idx, ofs, len) \
    Q_STATIC_BYTE_ARRAY_DATA_HEADER_INITIALIZER_WITH_OFFSET(len, \
    qptrdiff(offsetof(qt_meta_stringdata_MainWindow_t, stringdata0) + ofs \
        - idx * sizeof(QByteArrayData)) \
    )
static const qt_meta_stringdata_MainWindow_t qt_meta_stringdata_MainWindow = {
    {
QT_MOC_LITERAL(0, 0, 10), // "MainWindow"
QT_MOC_LITERAL(1, 11, 12), // "OnOpenDevice"
QT_MOC_LITERAL(2, 24, 0), // ""
QT_MOC_LITERAL(3, 25, 13), // "OnCloseDevice"
QT_MOC_LITERAL(4, 39, 8), // "OnReadId"
QT_MOC_LITERAL(5, 48, 11), // "OnDriverLog"
QT_MOC_LITERAL(6, 60, 5), // "level"
QT_MOC_LITERAL(7, 66, 4), // "text"
QT_MOC_LITERAL(8, 71, 17), // "OnLogLevelChanged"
QT_MOC_LITERAL(9, 89, 5), // "index"
QT_MOC_LITERAL(10, 95, 17), // "OnBitDelayChanged"
QT_MOC_LITERAL(11, 113, 5), // "value"
QT_MOC_LITERAL(12, 119, 12), // "OnOpenLogDir"
QT_MOC_LITERAL(13, 132, 9), // "OnScanBus"
QT_MOC_LITERAL(14, 142, 9), // "OnTestI2c"
QT_MOC_LITERAL(15, 152, 13), // "OnSdaSelfTest"
QT_MOC_LITERAL(16, 166, 9), // "OnSclWave"
QT_MOC_LITERAL(17, 176, 9), // "OnSdaWave"
QT_MOC_LITERAL(18, 186, 11), // "OnToggleScl"
QT_MOC_LITERAL(19, 198, 13) // "OnPullLowTest"

    },
    "MainWindow\0OnOpenDevice\0\0OnCloseDevice\0"
    "OnReadId\0OnDriverLog\0level\0text\0"
    "OnLogLevelChanged\0index\0OnBitDelayChanged\0"
    "value\0OnOpenLogDir\0OnScanBus\0OnTestI2c\0"
    "OnSdaSelfTest\0OnSclWave\0OnSdaWave\0"
    "OnToggleScl\0OnPullLowTest"
};
#undef QT_MOC_LITERAL

static const uint qt_meta_data_MainWindow[] = {

 // content:
       8,       // revision
       0,       // classname
       0,    0, // classinfo
      14,   14, // methods
       0,    0, // properties
       0,    0, // enums/sets
       0,    0, // constructors
       0,       // flags
       0,       // signalCount

 // slots: name, argc, parameters, tag, flags
       1,    0,   84,    2, 0x08 /* Private */,
       3,    0,   85,    2, 0x08 /* Private */,
       4,    0,   86,    2, 0x08 /* Private */,
       5,    2,   87,    2, 0x08 /* Private */,
       8,    1,   92,    2, 0x08 /* Private */,
      10,    1,   95,    2, 0x08 /* Private */,
      12,    0,   98,    2, 0x08 /* Private */,
      13,    0,   99,    2, 0x08 /* Private */,
      14,    0,  100,    2, 0x08 /* Private */,
      15,    0,  101,    2, 0x08 /* Private */,
      16,    0,  102,    2, 0x08 /* Private */,
      17,    0,  103,    2, 0x08 /* Private */,
      18,    0,  104,    2, 0x08 /* Private */,
      19,    0,  105,    2, 0x08 /* Private */,

 // slots: parameters
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void, QMetaType::Int, QMetaType::QString,    6,    7,
    QMetaType::Void, QMetaType::Int,    9,
    QMetaType::Void, QMetaType::Int,   11,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void,

       0        // eod
};

void MainWindow::qt_static_metacall(QObject *_o, QMetaObject::Call _c, int _id, void **_a)
{
    if (_c == QMetaObject::InvokeMetaMethod) {
        auto *_t = static_cast<MainWindow *>(_o);
        Q_UNUSED(_t)
        switch (_id) {
        case 0: _t->OnOpenDevice(); break;
        case 1: _t->OnCloseDevice(); break;
        case 2: _t->OnReadId(); break;
        case 3: _t->OnDriverLog((*reinterpret_cast< int(*)>(_a[1])),(*reinterpret_cast< const QString(*)>(_a[2]))); break;
        case 4: _t->OnLogLevelChanged((*reinterpret_cast< int(*)>(_a[1]))); break;
        case 5: _t->OnBitDelayChanged((*reinterpret_cast< int(*)>(_a[1]))); break;
        case 6: _t->OnOpenLogDir(); break;
        case 7: _t->OnScanBus(); break;
        case 8: _t->OnTestI2c(); break;
        case 9: _t->OnSdaSelfTest(); break;
        case 10: _t->OnSclWave(); break;
        case 11: _t->OnSdaWave(); break;
        case 12: _t->OnToggleScl(); break;
        case 13: _t->OnPullLowTest(); break;
        default: ;
        }
    }
}

QT_INIT_METAOBJECT const QMetaObject MainWindow::staticMetaObject = { {
    QMetaObject::SuperData::link<QMainWindow::staticMetaObject>(),
    qt_meta_stringdata_MainWindow.data,
    qt_meta_data_MainWindow,
    qt_static_metacall,
    nullptr,
    nullptr
} };


const QMetaObject *MainWindow::metaObject() const
{
    return QObject::d_ptr->metaObject ? QObject::d_ptr->dynamicMetaObject() : &staticMetaObject;
}

void *MainWindow::qt_metacast(const char *_clname)
{
    if (!_clname) return nullptr;
    if (!strcmp(_clname, qt_meta_stringdata_MainWindow.stringdata0))
        return static_cast<void*>(this);
    return QMainWindow::qt_metacast(_clname);
}

int MainWindow::qt_metacall(QMetaObject::Call _c, int _id, void **_a)
{
    _id = QMainWindow::qt_metacall(_c, _id, _a);
    if (_id < 0)
        return _id;
    if (_c == QMetaObject::InvokeMetaMethod) {
        if (_id < 14)
            qt_static_metacall(this, _c, _id, _a);
        _id -= 14;
    } else if (_c == QMetaObject::RegisterMethodArgumentMetaType) {
        if (_id < 14)
            *reinterpret_cast<int*>(_a[0]) = -1;
        _id -= 14;
    }
    return _id;
}
QT_WARNING_POP
QT_END_MOC_NAMESPACE

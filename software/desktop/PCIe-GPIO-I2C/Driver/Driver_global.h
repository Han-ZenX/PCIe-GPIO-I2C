#ifndef DRIVER_GLOBAL_H
#define DRIVER_GLOBAL_H

#include <QtCore/qglobal.h>

#if defined(DRIVER_LIBRARY)
#  define DRIVER_EXPORT Q_DECL_EXPORT
#else
#  define DRIVER_EXPORT Q_DECL_IMPORT
#endif

#endif // DRIVER_GLOBAL_H

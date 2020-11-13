#include "src/gmic/src/gmic.h"

// Set T be a float if not platform-overridden
#ifndef T
#define T gmic_pixel_type
#endif

#define xstr(s) str(s)
#define str(s) #s

#ifdef cimg_use_zlib
#define zlib_enabled 1
#else
#define zlib_enabled 0
#endif

#ifdef cimg_use_png
#define libpng_enabled 1
#else
#define lipng_enabled 0
#endif

#ifdef cimg_display
#define display_enabled 1
#else
#define display_enabled 0
#endif

#ifdef cimg_use_fftw3
#define fftw3_enabled 1
#else
#define fftw3_enabled 0
#endif

#ifdef cimg_use_curl
#define libcurl_enabled 1
#else
#define libcurl_enabled 0
#endif

#ifdef gmic_py_numpy
#define numpy_enabled 1
#else
#define numpy_enabled 0
#endif

#if cimg_OS == 0
#define OS_type "unknown"
#elif cimg_OS == 1
#define OS_type "unix"
#elif cimg_OS == 2
#define OS_type "windows"
#endif

#define gmicpy_build_info                                                   \
    PyUnicode_FromFormat(                                                   \
        "zlib_enabled:%d libpng_enabled:%d display_enabled:%d "             \
        "fftw3_enabled:%d libcurl_enabled:%d openmp_enabled:%d cimg_OS:%d " \
        "numpy_enabled:%d "                                                 \
        "OS_type:%s",                                                       \
        zlib_enabled, libpng_enabled, display_enabled, fftw3_enabled,       \
        libcurl_enabled, cimg_use_openmp, cimg_OS, numpy_enabled, OS_type)

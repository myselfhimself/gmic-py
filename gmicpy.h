#include "gmic.h"

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

#if cimg_OS==0
#define OS_type "unknown"
#elif cimg_OS==1
#define OS_type "windows"
#elif cimg_OS==2
#define OS_type "unix"
#endif

#ifdef gmicpy_debug
#define gmicpy_debug_enabled 1
#define gmicpy_optimize_enabled 0
#else
#define gmicpy_debug_enabled 0
#define gmicpy_optimize_enabled 1
#endif

#ifdef gmicpy_sanitizer
#define gmicpy_sanitizer_enabled 1
#else
#define gmicpy_sanitizer_enabled 0
#endif

#define gmicpy_build_info PyUnicode_FromFormat("zlib_enabled:%d libpng_enabled:%d display_enabled:%d fftw3_enabled:%d libcurl_enabled:%d openmp_enabled:%d cimg_OS:%d OS_type:%s debug_symbols:%d optimized:%d sanitizer_enabled:%d", zlib_enabled, libpng_enabled, display_enabled, fftw3_enabled, libcurl_enabled, cimg_use_openmp, cimg_OS, OS_type, gmicpy_debug_enabled, gmicpy_optimize_enabled, gmicpy_sanitizer_enabled)

#define gmicpy_version_info PyUnicode_Join(PyUnicode_FromString("."), PyUnicode_FromString(xstr(gmic_version)))

INCLUDE(FindPkgConfig)
PKG_CHECK_MODULES(PC_BINARY_DECODER binary_decoder)

FIND_PATH(
    BINARY_DECODER_INCLUDE_DIRS
    NAMES binary_decoder/api.h
    HINTS $ENV{BINARY_DECODER_DIR}/include
        ${PC_BINARY_DECODER_INCLUDEDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/include
          /usr/local/include
          /usr/include
)

FIND_LIBRARY(
    BINARY_DECODER_LIBRARIES
    NAMES gnuradio-binary_decoder
    HINTS $ENV{BINARY_DECODER_DIR}/lib
        ${PC_BINARY_DECODER_LIBDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/lib
          ${CMAKE_INSTALL_PREFIX}/lib64
          /usr/local/lib
          /usr/local/lib64
          /usr/lib
          /usr/lib64
          )

include("${CMAKE_CURRENT_LIST_DIR}/binary_decoderTarget.cmake")

INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(BINARY_DECODER DEFAULT_MSG BINARY_DECODER_LIBRARIES BINARY_DECODER_INCLUDE_DIRS)
MARK_AS_ADVANCED(BINARY_DECODER_LIBRARIES BINARY_DECODER_INCLUDE_DIRS)

file(GLOB GENERAL_OPS RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}" "*_op.cc")
string(REPLACE ".cc" "" GENERAL_OPS "${GENERAL_OPS}")
set(pybind_file ${PADDLE_SOURCE_DIR}/paddle/pybind/pybind.h)
file(WRITE ${pybind_file} "// Generated by the paddle/operator/CMakeLists.txt.  DO NOT EDIT!\n\n")
function(op_library TARGET)
    # op_library is a function to create op library. The interface is same as
    # cc_library. But it handle split GPU/CPU code and link some common library
    # for ops.
    set(OP_LIBRARY ${TARGET} ${OP_LIBRARY} PARENT_SCOPE)
    set(cc_srcs)
    set(cu_srcs)
    set(op_common_deps operator op_registry math_function)
    set(options "")
    set(oneValueArgs "")
    set(multiValueArgs SRCS DEPS)
    set(pybind_flag 0)
    cmake_parse_arguments(op_library "${options}" "${oneValueArgs}"
            "${multiValueArgs}" ${ARGN})

    list(LENGTH op_library_SRCS op_library_SRCS_len)
    if (${op_library_SRCS_len} EQUAL 0)
        if (EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/${TARGET}.cc)
            list(APPEND cc_srcs ${TARGET}.cc)
        endif()
        if (EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/${TARGET}.cu)
            list(APPEND cu_srcs ${TARGET}.cu)
        endif()
    else()
        foreach(src ${op_library_SRCS})
            if (${src} MATCHES ".*\\.cu$")
                list(APPEND cu_srcs ${src})
            elseif(${src} MATCHES ".*\\.cc$")
                list(APPEND cc_srcs ${src})
            else()
                message(FATAL_ERROR "${TARGET} Source file ${src} should only be .cc or .cu")
            endif()
        endforeach()
    endif()

    list(LENGTH cc_srcs cc_srcs_len)
    if (${cc_srcs_len} EQUAL 0)
        message(FATAL_ERROR "The op library ${TARGET} should contains at least one .cc file")
    endif()

    if (WITH_GPU)
        nv_library(${TARGET} SRCS ${cc_srcs} ${cu_srcs} DEPS ${op_library_DEPS}
                ${op_common_deps})
    else()
        cc_library(${TARGET} SRCS ${cc_srcs} DEPS ${op_library_DEPS}
                ${op_common_deps})
    endif()

    # net_op doesn't need pybind
    if ("${TARGET}" STREQUAL "net_op")
        set(pybind_flag 1)
    endif()

    # pool_op contains several operators
    if ("${TARGET}" STREQUAL "pool_op")
        set(pybind_flag 1)
        # It's enough to just adding one operator to pybind
        file(APPEND ${pybind_file} "USE_OP(pool2d);\n")
    endif()

    # pool_with_index_op contains several operators
    if ("${TARGET}" STREQUAL "pool_with_index_op")
        set(pybind_flag 1)
        # It's enough to just adding one operator to pybind
        file(APPEND ${pybind_file} "USE_OP(max_pool2d_with_index);\n")
    endif()

    # pool_cudnn_op contains several operators
    if ("${TARGET}" STREQUAL "pool_cudnn_op")
        set(pybind_flag 1)
        # It's enough to just adding one operator to pybind
        file(APPEND ${pybind_file} "USE_OP(pool2d_cudnn);\n")
    endif()

    # save_restore_op contains several operators
    if ("${TARGET}" STREQUAL "save_restore_op")
        set(pybind_flag 1)
        # It's enough to just adding one operator to pybind
        file(APPEND ${pybind_file} "USE_NO_KERNEL_OP(save);\n")
    endif()

    # activation_op contains several operators
    if ("${TARGET}" STREQUAL "activation_op")
        set(pybind_flag 1)
        # It's enough to just adding one operator to pybind
        file(APPEND ${pybind_file} "USE_OP(sigmoid);\n")
    endif()

    # nccl_op contains several operators
    if ("${TARGET}" STREQUAL "nccl_op")
        set(pybind_flag 1)
        # It's enough to just adding one operator to pybind
        file(APPEND ${pybind_file} "USE_GPU_ONLY_OP(ncclAllReduce);\n")
    endif()
    
    # reduce_op contains several operators
    if ("${TARGET}" STREQUAL "reduce_op")
        set(pybind_flag 1)
        # It's enough to just adding one operator to pybind
        file(APPEND ${pybind_file} "USE_OP(reduce_sum);\n")
    endif()

    # pybind USE_NO_KERNEL_OP
    # HACK: if REGISTER_OP_CPU_KERNEL presents the operator must have kernel
    file(READ ${TARGET}.cc TARGET_CONTENT)
    string(REGEX MATCH "REGISTER_OP_CPU_KERNEL" regex_result "${TARGET_CONTENT}")
    string(REPLACE "_op" "" TARGET "${TARGET}")
    if (${pybind_flag} EQUAL 0 AND regex_result STREQUAL "")
        file(APPEND ${pybind_file} "USE_NO_KERNEL_OP(${TARGET});\n")
        set(pybind_flag 1)
    endif()

    # pybind USE_CPU_ONLY_OP
    list(LENGTH cu_srcs cu_srcs_len)
    if (${pybind_flag} EQUAL 0 AND ${cu_srcs_len} EQUAL 0)
        file(APPEND ${pybind_file} "USE_CPU_ONLY_OP(${TARGET});\n")
        set(pybind_flag 1)
    endif()

    # pybind USE_OP
    if (${pybind_flag} EQUAL 0)
        file(APPEND ${pybind_file} "USE_OP(${TARGET});\n")
    endif()
endfunction()

add_subdirectory(math)
add_subdirectory(nccl)

set(DEPS_OPS
    cond_op
    cross_entropy_op
    recurrent_op
    dynamic_recurrent_op
    softmax_with_cross_entropy_op
    sum_op
    pool_op
    pool_with_index_op
    nccl_op
    sequence_conv_op
    lstm_op)

op_library(cond_op SRCS cond_op.cc DEPS framework_proto tensor operator net_op)
op_library(cross_entropy_op DEPS cross_entropy)
op_library(softmax_with_cross_entropy_op DEPS cross_entropy softmax)
op_library(sum_op DEPS net_op selected_rows_functor)
op_library(pool_op DEPS pooling)
op_library(pool_with_index_op DEPS pooling)
if(WITH_GPU)
op_library(nccl_op DEPS nccl_common)
endif()
op_library(sequence_conv_op DEPS context_project)
op_library(lstm_op DEPS sequence2batch lstm_compute)
op_library(dynamic_recurrent_op SRCS dynamic_recurrent_op.cc rnn/recurrent_op_utils.cc
        DEPS net_op tensor_array)
op_library(recurrent_op SRCS recurrent_op.cc DEPS executor)
list(REMOVE_ITEM GENERAL_OPS ${DEPS_OPS})
foreach(src ${GENERAL_OPS})
    op_library(${src})
endforeach()

set(GLOB_OP_LIB ${OP_LIBRARY} CACHE INTERNAL "Global OP library")

cc_test(gather_test SRCS gather_test.cc DEPS tensor)
cc_test(net_op_test SRCS net_op_test.cc DEPS net_op)
cc_test(scatter_test SRCS scatter_test.cc DEPS tensor)
cc_test(strided_memcpy_test SRCS strided_memcpy_test.cc DEPS tensor paddle_memory)
cc_test(dynamic_recurrent_op_test SRCS dynamic_recurrent_op_test.cc
        rnn/recurrent_op_utils.cc
        DEPS dynamic_recurrent_op)
if(WITH_GPU)
  nv_test(nccl_op_test SRCS nccl_op_test.cu DEPS nccl_op gpu_info device_context)
endif()
cc_test(save_load_op_test SRCS save_load_op_test.cc DEPS save_op load_op)

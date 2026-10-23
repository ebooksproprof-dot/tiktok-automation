"""Run cached CPU inference with kernel-enforced denial of all socket calls.

Linux/libseccomp only, fails closed. Install/download dependencies before this
wrapper; subprocesses inherit the filter. No remote telemetry can be emitted.
"""
import ctypes
import ctypes.util
import errno
import os
import sys


def deny_network():
    name = ctypes.util.find_library('seccomp')
    if not name:
        raise RuntimeError('libseccomp required for offline inference')
    lib = ctypes.CDLL(name, use_errno=True)
    lib.seccomp_init.argtypes = [ctypes.c_uint32]
    lib.seccomp_init.restype = ctypes.c_void_p
    lib.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
    lib.seccomp_syscall_resolve_name.restype = ctypes.c_int
    lib.seccomp_rule_add.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_uint]
    lib.seccomp_rule_add.restype = ctypes.c_int
    lib.seccomp_load.argtypes = [ctypes.c_void_p]
    lib.seccomp_load.restype = ctypes.c_int
    lib.seccomp_release.argtypes = [ctypes.c_void_p]
    ctx = lib.seccomp_init(0x7fff0000)  # ALLOW all except listed network syscalls.
    if not ctx:
        raise RuntimeError('Cannot allocate network deny filter')
    try:
        for name in (b'socket', b'connect', b'sendto', b'sendmsg', b'sendmmsg', b'socketcall'):
            number = lib.seccomp_syscall_resolve_name(name)
            if number >= 0 and lib.seccomp_rule_add(ctx, 0x50000 | errno.EPERM, number, 0) != 0:
                raise RuntimeError('Cannot install network deny rule')
        if lib.seccomp_load(ctx) != 0:
            raise RuntimeError('Cannot enforce offline inference')
    finally:
        lib.seccomp_release(ctx)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise SystemExit('Usage: offline_exec.py PROGRAM [ARG...]')
    deny_network()
    os.execvp(sys.argv[1], sys.argv[1:])

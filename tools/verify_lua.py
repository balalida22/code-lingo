"""Run an authored fixture using an installed Lua 5.4 shared library.

Developer-only fallback when the Lua CLI is absent. Never used by the tutor.
Usage: python tools/verify_lua.py /path/to/authored-fixture.lua
"""
import ctypes
import ctypes.util
import sys

def main():
    path=ctypes.util.find_library('lua5.4')
    if not path:
        print('Lua 5.4 shared library is unavailable',file=sys.stderr)
        return 2
    lib=ctypes.CDLL(path)
    lib.luaL_newstate.restype=ctypes.c_void_p
    lib.luaL_openlibs.argtypes=[ctypes.c_void_p]
    lib.luaL_loadfilex.argtypes=[ctypes.c_void_p,ctypes.c_char_p,ctypes.c_char_p]
    lib.luaL_loadfilex.restype=ctypes.c_int
    lib.lua_pcallk.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_ssize_t,ctypes.c_void_p]
    lib.lua_pcallk.restype=ctypes.c_int
    lib.lua_tolstring.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p]
    lib.lua_tolstring.restype=ctypes.c_char_p
    lib.lua_close.argtypes=[ctypes.c_void_p]
    state=lib.luaL_newstate()
    if not state: raise MemoryError('Cannot create Lua state')
    try:
        lib.luaL_openlibs(state)
        status=lib.luaL_loadfilex(state,sys.argv[1].encode(),None)
        if not status: status=lib.lua_pcallk(state,0,-1,0,0,None)
        if status:
            print(lib.lua_tolstring(state,-1,None).decode('utf-8','replace'),file=sys.stderr)
        return int(bool(status))
    finally:lib.lua_close(state)

if __name__=='__main__':raise SystemExit(main())

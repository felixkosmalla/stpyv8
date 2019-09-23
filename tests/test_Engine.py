#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import unittest
import logging

from datetime import *
from SoirV8 import *

is_py3k = sys.version_info[0] > 2


class TestContext(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.platform = JSPlatform()
        self.platform.init()

        self.isolate = JSIsolate()
        self.isolate.enter()  #TODO remove?

class TestEngine(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.platform = JSPlatform()
        self.platform.init()

        self.isolate = JSIsolate()
        self.isolate.enter()  #TODO remove?

    def testClassProperties(self):
        with JSContext() as ctxt:
            self.assertTrue(str(JSEngine.version).startswith("7."))
            # self.assertFalse(JSEngine.dead)

    def testCompile(self):
        with JSContext() as ctxt:
            with JSEngine() as engine:
                s = engine.compile("1+2")

                self.assertTrue(isinstance(s, JSScript))

                self.assertEqual("1+2", s.source)
                self.assertEqual(3, int(s.run()))

                self.assertRaises(SyntaxError, engine.compile, "1+")

    def _testPrecompile(self):
        with JSContext() as ctxt:
            with JSEngine() as engine:
                data = engine.precompile("1+2")

                self.assertTrue(data)
                self.assertEqual(28, len(data))

                s = engine.compile("1+2", precompiled=data)

                self.assertTrue(isinstance(s, _PyV8.JSScript))

                self.assertEqual("1+2", s.source)
                self.assertEqual(3, int(s.run()))

                self.assertRaises(SyntaxError, engine.precompile, "1+")

    def testUnicodeSource(self):
        class Global(JSClass):
            var = u'测试'

            def __getattr__(self, name):
                if (name if is_py3k else name.decode('utf-8')) == u'变量':
                    return self.var

                return JSClass.__getattr__(self, name)

        g = Global()

    def _testUnicodeSource(self):
        class Global(JSClass):
            var = u'测试'

            def __getattr__(self, name):
                if (name if is_py3k else name.decode('utf-8')) == u'变量':
                    return self.var

                return JSClass.__getattr__(self, name)

        g = Global()

        with JSContext(g) as ctxt:
            with JSEngine() as engine:
                src = u"""
                function 函数() { return 变量.length; }

                函数();

                var func = function () {};
                """

                data = engine.precompile(src)

                self.assertTrue(data)
                self.assertEqual(68, len(data))

                s = engine.compile(src, precompiled=data)

                self.assertTrue(isinstance(s, _PyV8.JSScript))

                self.assertEqual(toNativeString(src), s.source)
                self.assertEqual(2, s.run())

                func_name = toNativeString(u'函数')

                self.assertTrue(hasattr(ctxt.locals, func_name))

                func = getattr(ctxt.locals, func_name)

                self.assertTrue(isinstance(func, _PyV8.JSFunction))

                self.assertEqual(func_name, func.name)
                self.assertEqual("", func.resname)
                self.assertEqual(1, func.linenum)
                self.assertEqual(0, func.lineoff)
                self.assertEqual(0, func.coloff)

                var_name = toNativeString(u'变量')

                setattr(ctxt.locals, var_name, u'测试长字符串')

                self.assertEqual(6, func())

                self.assertEqual("func", ctxt.locals.func.inferredname)

    def _testExtension(self):
        extSrc = """function hello(name) { return "hello " + name + " from javascript"; }"""
        extJs = JSExtension("hello/javascript", extSrc)

        self.assertTrue(extJs)
        self.assertEqual("hello/javascript", extJs.name)
        self.assertEqual(extSrc, extJs.source)
        self.assertFalse(extJs.autoEnable)
        self.assertTrue(extJs.registered)

        TestEngine.extJs = extJs

        with JSContext(extensions=['hello/javascript']) as ctxt:
            self.assertEqual("hello flier from javascript", ctxt.eval("hello('flier')"))

        # test the auto enable property

        with JSContext() as ctxt:
            self.assertRaises(ReferenceError, ctxt.eval, "hello('flier')")

        extJs.autoEnable = True
        self.assertTrue(extJs.autoEnable)

        with JSContext() as ctxt:
            self.assertEqual("hello flier from javascript", ctxt.eval("hello('flier')"))

        extJs.autoEnable = False
        self.assertFalse(extJs.autoEnable)

        with JSContext() as ctxt:
            self.assertRaises(ReferenceError, ctxt.eval, "hello('flier')")

        extUnicodeSrc = u"""function helloW(name) { return "hello " + name + " from javascript"; }"""
        extUnicodeJs = JSExtension(u"helloW/javascript", extUnicodeSrc)

        self.assertTrue(extUnicodeJs)
        self.assertEqual("helloW/javascript", extUnicodeJs.name)
        self.assertEqual(toNativeString(extUnicodeSrc), extUnicodeJs.source)
        self.assertFalse(extUnicodeJs.autoEnable)
        self.assertTrue(extUnicodeJs.registered)

        TestEngine.extUnicodeJs = extUnicodeJs

        with JSContext(extensions=['helloW/javascript']) as ctxt:
            self.assertEqual("hello flier from javascript", ctxt.eval("helloW('flier')"))

            ret = ctxt.eval(u"helloW('世界')")

            self.assertEqual(u"hello 世界 from javascript", ret if is_py3k else ret.decode('UTF-8'))

    def _testNativeExtension(self):
        extSrc = "native function hello();"
        extPy = JSExtension("hello/python", extSrc, lambda func: lambda name: "hello " + name + " from python", register=False)
        self.assertTrue(extPy)
        self.assertEqual("hello/python", extPy.name)
        self.assertEqual(extSrc, extPy.source)
        self.assertFalse(extPy.autoEnable)
        self.assertFalse(extPy.registered)
        extPy.register()
        self.assertTrue(extPy.registered)

        TestEngine.extPy = extPy

        with JSContext(extensions=['hello/python']) as ctxt:
            self.assertEqual("hello flier from python", ctxt.eval("hello('flier')"))

    def _testSerialize(self):
        data = None

        self.assertFalse(JSContext.entered)

        with JSContext() as ctxt:
            self.assertTrue(JSContext.entered)

            #ctxt.eval("function hello(name) { return 'hello ' + name; }")

            data = JSEngine.serialize()

        self.assertTrue(data)
        self.assertTrue(len(data) > 0)

        self.assertFalse(JSContext.entered)

        #JSEngine.deserialize()

        self.assertTrue(JSContext.entered)

        self.assertEqual('hello flier', JSContext.current.eval("hello('flier');"))

    def testEval(self):
        with JSContext() as ctxt:
            self.assertEqual(3, int(ctxt.eval("1+2")))

    def testGlobal(self):
        class Global(JSClass):
            version = "1.0"

        with JSContext(Global()) as ctxt:
            vars = ctxt.locals

            # getter
            self.assertEqual(Global.version, str(vars.version))
            self.assertEqual(Global.version, str(ctxt.eval("version")))

            self.assertRaises(ReferenceError, ctxt.eval, "nonexists")

            # setter
            self.assertEqual(2.0, float(ctxt.eval("version = 2.0")))

            self.assertEqual(2.0, float(vars.version))

    def _testThis(self):
        class Global(JSClass):
            version = 1.0

        with JSContext(Global()) as ctxt:
            self.assertEqual("[object Global]", str(ctxt.eval("this")))

            self.assertEqual(1.0, float(ctxt.eval("this.version")))

    def testObjectBuildInMethods(self):
        class Global(JSClass):
            version = 1.0

        with JSContext(Global()) as ctxt:
            self.assertEqual("[object Global]", str(ctxt.eval("this.toString()")))
            self.assertEqual("[object Global]", str(ctxt.eval("this.toLocaleString()")))
            self.assertEqual(Global.version, float(ctxt.eval("this.valueOf()").version))

            self.assertTrue(bool(ctxt.eval("this.hasOwnProperty(\"version\")")))

            self.assertFalse(ctxt.eval("this.hasOwnProperty(\"nonexistent\")"))

    def testPythonWrapper(self):
        class Global(JSClass):
            s = [1, 2, 3]
            d = {'a': {'b': 'c'}, 'd': ['e', 'f']}

        g = Global()

        with JSContext(g) as ctxt:
            ctxt.eval("""
                s[2] = s[1] + 2;
                s[0] = s[1];
                delete s[1];
            """)
            self.assertEqual([2, 4], g.s)
            self.assertEqual('c', ctxt.eval("d.a.b"))
            self.assertEqual(['e', 'f'], ctxt.eval("d.d"))
            ctxt.eval("""
                d.a.q = 4
                delete d.d
            """)
            self.assertEqual(4, g.d['a']['q'])
            self.assertEqual(None, ctxt.eval("d.d"))

    def _testMemoryAllocationCallback(self):
        alloc = {}

        def callback(space, action, size):
            alloc[(space, action)] = alloc.setdefault((space, action), 0) + size

        JSEngine.setMemoryAllocationCallback(callback)

        with JSContext() as ctxt:
            self.assertFalse((JSObjectSpace.Code, JSAllocationAction.alloc) in alloc)

            ctxt.eval("var o = new Array(1000);")

            self.assertTrue((JSObjectSpace.Code, JSAllocationAction.alloc) in alloc)

        JSEngine.setMemoryAllocationCallback(None)

    def _testOutOfMemory(self):
        with JSIsolate():
            JSEngine.setMemoryLimit(max_young_space_size=16 * 1024, max_old_space_size=4 * 1024 * 1024)

            with JSContext() as ctxt:
                JSEngine.ignoreOutOfMemoryException()

                ctxt.eval("var a = new Array(); while(true) a.push(a);")

                self.assertTrue(ctxt.hasOutOfMemoryException)

                JSEngine.setMemoryLimit()

                JSEngine.collect()

    def _testStackLimit(self):
        with JSIsolate():
            JSEngine.setStackLimit(256 * 1024)

            with JSContext() as ctxt:
                oldStackSize = ctxt.eval("var maxStackSize = function(i){try{(function m(){++i&&m()}())}catch(e){return i}}(0); maxStackSize")

        with JSIsolate():
            JSEngine.setStackLimit(512 * 1024)

            with JSContext() as ctxt:
                newStackSize = ctxt.eval("var maxStackSize = function(i){try{(function m(){++i&&m()}())}catch(e){return i}}(0); maxStackSize")

        self.assertTrue(newStackSize > oldStackSize * 2)



if __name__ == '__main__':
    level = logging.DEBUG if "-v" in sys.argv else logging.WARN
    logging.basicConfig(level = level, format = '%(asctime)s %(levelname)s %(message)s')
    unittest.main()
.. py:module:: STPyV8
    :noindex:

.. testsetup:: *

   from STPyV8 import *

.. _context:

Javascript Context
==================

.. sidebar:: Execution context

    When control is transferred to ECMAScript executable code [#f2]_, control is entering an execution context.

        -- ECMA-262 3rd Chapter 10

According to the ECMAScript standard [#f1]_, an execution context has to be entered before executing any script code.

:py:class:`JSContext` is a sandboxed execution context with its own set of built-in objects and functions.

You could create a :py:class:`JSContext` instance, enter it with the :py:meth:`JSContext.enter` method, and use it to
execute Javascript code with the :py:meth:`JSContext.eval` method. The best practice is to leave the context with the 
:py:meth:`JSContext.leave` when you do not need it anymore.

.. doctest::

   >>> ctxt = JSContext()               # create a context with an implicit global object
   >>> ctxt.enter()                     # enter the context (also support with statement)
   >>> ctxt.eval("1+2")                 # evalute the javascript expression and return a native python int
   3
   >>> ctxt.leave()                     # leave the context and release the related resources

.. note::

   To ensure the context is entered/left correctly, use the **with** statement

    .. testcode::

        with JSContext() as ctxt:
            print(ctxt.eval("1+2")) # 3

    .. testoutput::
       :hide:

       3

You could also check the current context using the :py:class:`JSContext` static properties.

==============================  =============================================
Property                        Description
==============================  =============================================
:py:attr:`JSContext.current`    The context that is on the top of the stack.
:py:attr:`JSContext.entered`    The last entered context.
:py:attr:`JSContext.calling`    The context of the calling JavaScript code.
:py:attr:`JSContext.inContext`  Returns true if V8 has a current context.
==============================  =============================================

.. _gobj:

Global Object
-------------

.. sidebar:: Global object

    There is a unique *global object* (15.1), which is created before control enters any execution context. Initially the global object has the following properties:

    * Built-in objects such as Math, String, Date, parseInt, etc.
    * Additional host defined properties.

    As control enters execution contexts, and as ECMAScript code is executed, additional properties may be added to the global object and the initial properties may be changed.

        -- ECMA-262 3rd Chapter 10.1.5

The execution context has a global object which could be accessed both from the Python side with the :py:attr:`JSContext.locals`
attribute and from the Javascript side using the global namespace. The Python and Javascript code could use such object to 
perform seamless interoperable logic while STPyV8 takes care of :ref:`typeconv`, :ref:`funcall` and :ref:`exctrans`.

.. testcode::

    with JSContext() as ctxt:
        ctxt.eval("a = 1")
        print(ctxt.locals.a)     # 1

        ctxt.locals.a = 2
        print(ctxt.eval("a"))    # 2

.. testoutput::
   :hide:

   1
   2

Providing more complicated properties and methods to the Javascript code can be easily done by passing a customized global object
instance when the :py:class:`JSContext` instance is created.

.. testcode::

    class Global(JSClass):
        version = "1.0"

        def hello(self, name):
            return "Hello " + name

    with JSContext(Global()) as ctxt:
        print(ctxt.eval("version")))          # 1.0
        print(ctxt.eval("hello('World')"))   # Hello World
        print(ctxt.eval("hello.toString()")) # function () { [native code] }

.. testoutput::
   :hide:

   1.0
   Hello World
   function () { [native code] }

.. note::

    If you want your global object to behave like a real Javascript object, you should inherit from the :py:class:`JSClass` class
    which provides a lot of helper methods such as :py:meth:`JSClass.toString`, :py:meth:`JSClass.watch` etc.

.. _jsext:

JSContext - the execution context.
----------------------------------

.. autoclass:: JSContext
   :members:
   :inherited-members:
   :exclude-members: eval

   JSContext is an execution context.

   .. automethod:: __init__(global = None) -> JSContext object

      :param object global: the global object
      :rtype: :py:class:`JSContext` instance

   .. automethod:: __init__(ctxt) -> JSContext object

      :param JSContext ctxt: an existing :py:class:`JSContext` instance
      :rtype: a cloned :py:class:`JSContext` instance

   .. automethod:: eval(source, name = '', line = -1, col = -1) -> object:

      Execute the Javascript code and return the result

      :param source: the Javascript code to be executed
      :type source: str or unicode
      :param str name: the name of the Javascript code
      :param integer line: the start line number of the Javascript code
      :param integer col: the start column number of the Javascript code
      :rtype: the result

   .. automethod:: __enter__() -> JSContext object

   .. automethod:: __exit__(exc_type, exc_value, traceback) -> None

   .. py:attribute:: current

       The context that is on the top of the stack.

   .. py:attribute:: entered

       The last entered context.

   .. py:attribute:: calling

       The context of the calling JavaScript code.

   .. py:attribute:: inContext

       Returns true if V8 has a current context.

.. toctree::
   :maxdepth: 2

.. rubric:: Footnotes

.. [#f1] `ECMAScript <http://en.wikipedia.org/wiki/ECMAScript>`_ is the scripting language standardized by Ecma International in the ECMA-262 specification and ISO/IEC 16262. The language is widely used for client-side scripting on the web, in the form of several well-known dialects such as JavaScript, JScript, and ActionScript.

.. [#f2] There are three types of ECMAScript executable code:

         * *Global code* is source text that is treated as an ECMAScript *Program*.
         * *Eval code* is the source text supplied to the built-in **eval** function.
         * *Function code* is source text that is parsed as part of a *FunctionBody*.

#include <Python.h>
#include <iostream>
#include "gmic.h"
using namespace std;

PyObject* run_impl(PyObject*, PyObject* commands_line) 
{
  const char* c_commands_line = PyUnicode_AsUTF8(commands_line);
  gmic(c_commands_line, 0, true);
  return Py_True;
}

static PyMethodDef gmic_methods[] = {
  {"run", (PyCFunction)run_impl, METH_O, nullptr },
  {nullptr, nullptr, 0, nullptr }
};

PyModuleDef gmic_module = {
  PyModuleDef_HEAD_INIT,
  "gmic",
  "Gmic Python binding",
  0,
  gmic_methods
};

PyMODINIT_FUNC PyInit_gmic() {
  return PyModule_Create(&gmic_module);
}

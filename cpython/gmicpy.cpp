#include <Python.h>
#include <iostream>
#include "gmic.h"
using namespace std;

PyObject* run_impl(PyObject*, PyObject* commands_line) 
{
  const char* c_commands_line = PyUnicode_AsUTF8(commands_line);
  //gmic::run(c_commands_line, NULL, NULL, NULL, NULL);
// template gmic& gmic::run(const char *const commands_line, \
                         gmic_list<pt> &images, gmic_list<char> &images_names, \
                         float *const p_progress, bool *const p_is_abort); \
t
	cout << "about to pipe this string into gmic from a python module:" << c_commands_line << endl;
        gmic(c_commands_line, NULL, NULL);
  return Py_True;
}

static PyMethodDef gmicpy_methods[] = {
  {"run", (PyCFunction)run_impl, METH_O, nullptr },
  {nullptr, nullptr, 0, nullptr }
};

PyModuleDef gmicpy_module = {
  PyModuleDef_HEAD_INIT,
  "gmic",
  "WIP Gmic Python binding",
  0,
  gmicpy_methods
};

PyMODINIT_FUNC PyInit_gmicpy() {
  return PyModule_Create(&gmicpy_module);
}

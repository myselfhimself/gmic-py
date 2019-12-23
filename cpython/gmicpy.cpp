#include <Python.h>
#include <iostream>
#include "gmic.h"
using namespace std;

// Set T be a float if not platform-overridden
#ifndef T
#define T gmic_pixel_type
#endif


typedef struct {
    PyObject_HEAD
    gmic_image<T> * ptrObj;
} PyGmicImage;

static int PyGmicImage_init(PyGmicImage *self, PyObject *args, PyObject *kwds)
// initialize PyGmicImage Object
{
    unsigned int _width;       // Number of image columns (dimension along the X-axis)
    unsigned int _height;      // Number of image lines (dimension along the Y-axis)
    unsigned int _depth;       // Number of image slices (dimension along the Z-axis)
    unsigned int _spectrum;    // Number of image channels (dimension along the C-axis)
  
    // SKIPPED FOR NOW
    bool _is_shared = false;           // Tells if the data buffer is shared by another structure
    T *_data;                  // Pointer to the first pixel value


    if (! PyArg_ParseTuple(args, "IIII", &_width, &_height, &_depth, &_spectrum))
        return -1;

    self->ptrObj=new gmic_image<T>();
    self->ptrObj->_is_shared = _is_shared;
    self->ptrObj->_data = NULL;
    self->ptrObj->assign(_width, _height, _depth, _spectrum);

    return 0;
}


static PyObject* PyGmicImage_repr(PyGmicImage* self)
{
    return PyUnicode_FromFormat("<%s object at %p with _data address %p, w=%d h=%d d=%d s=%d>",
                                    Py_TYPE(self)->tp_name, self, self->ptrObj->_data, self->ptrObj->_width, self->ptrObj->_height, self->ptrObj->_depth, self->ptrObj->_spectrum);
}




static void PyGmicImage_dealloc(PyGmicImage * self)
// destruct the object
{
    free(self->ptrObj->_data);
    delete self->ptrObj;
    Py_TYPE(self)->tp_free(self);

}



static PyObject * PyGmicImage_from_numpy_array(PyGmicImage * self, PyObject* args)
{
int retval;

// todo array of floats instead from numpy array
    if (! PyArg_ParseTuple(args, "f", &self->ptrObj->_data))
        return Py_False;

    retval = (self->ptrObj)->_data != NULL;

    return Py_BuildValue("i",retval);
}



static PyTypeObject PyGmicImageType = { PyVarObject_HEAD_INIT(NULL, 0)
                                    "gmic.GmicImage"   /* tp_name */
                                };

static PyMethodDef PyGmicImage_methods[] = {
    { "from_numpy_array", (PyCFunction)PyGmicImage_from_numpy_array,    METH_VARARGS,       "get numpy array's data" },
    {NULL}  /* Sentinel */
};






PyObject* run_impl(PyObject*, PyObject* commands_line) 
{
  const char* c_commands_line = PyUnicode_AsUTF8(commands_line);
  try {
    gmic(c_commands_line, 0, true);
  } catch (gmic_exception& e) {
    PyErr_SetString(PyExc_Exception, e.what());
  } catch (std::exception& e) {
    PyErr_SetString(PyExc_Exception, e.what());
    return NULL;
  }
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
  
    
    PyObject* m;

    PyGmicImageType.tp_new = PyType_GenericNew;
    PyGmicImageType.tp_basicsize=sizeof(PyGmicImage);
    PyGmicImageType.tp_dealloc=(destructor) PyGmicImage_dealloc;
    PyGmicImageType.tp_doc="Gmic Image buffer";
    PyGmicImageType.tp_methods=PyGmicImage_methods;
    PyGmicImageType.tp_repr=PyGmicImage_repr;
    PyGmicImageType.tp_init=(initproc)PyGmicImage_init;

    if (PyType_Ready(&PyGmicImageType) < 0)
        return NULL;

    m = PyModule_Create(&gmic_module);
    if (m == NULL)
        return NULL;

    Py_INCREF(&PyGmicImageType);
    PyModule_AddObject(m, "GmicImage", (PyObject *)&PyGmicImageType); // Add GmicImage object to the module
    return m;
    
}

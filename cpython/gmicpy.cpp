#include <Python.h>
#include <iostream>
#include <stdio.h>
#include "gmic.h"
using namespace std;

// Set T be a float if not platform-overridden
#ifndef T
#define T gmic_pixel_type
#endif


typedef struct {
    PyObject_HEAD
    gmic_image<T> * ptrObj; // G'MIC library's Gmic Image
} PyGmicImage;

static int PyGmicImage_init(PyGmicImage *self, PyObject *args, PyObject *kwargs)
{
    unsigned int _width;       // Number of image columns (dimension along the X-axis)
    unsigned int _height;      // Number of image lines (dimension along the Y-axis)
    unsigned int _depth;       // Number of image slices (dimension along the Z-axis)
    unsigned int _spectrum;    // Number of image channels (dimension along the C-axis)
    int _is_shared = (int) false; // Whether image should be shared across gmic operations (if true, operations like resize will fail)
    PyObject* bytesObj;        // Incoming bytes buffer object pointer
    char const* keywords[] = {"data", "width", "height", "depth", "spectrum", "shared", NULL};
    _width=_height=_depth=_spectrum=1;

    if (! PyArg_ParseTupleAndKeywords(args, kwargs, "S|IIIIp", (char**) keywords, &bytesObj, &_width, &_height, &_depth, &_spectrum, &_is_shared))
        return -1;

    self->ptrObj=new gmic_image<T>();
    self->ptrObj->assign(_width,_height,_depth,_spectrum);
    self->ptrObj->_is_shared = _is_shared;

    memcpy(self->ptrObj->_data, PyBytes_AsString(bytesObj), PyBytes_Size(bytesObj));

    return 0;
}


static PyObject* PyGmicImage_repr(PyGmicImage* self)
{
    return PyUnicode_FromFormat("<%s object at %p with _data address at %p, w=%d h=%d d=%d s=%d shared=%d>",
        Py_TYPE(self)->tp_name,
       	self, self->ptrObj->_data,
       	self->ptrObj->_width,
       	self->ptrObj->_height,
	self->ptrObj->_depth,
        self->ptrObj->_spectrum,
        self->ptrObj->_is_shared
    );
}


static PyObject *PyGmicImage_call(PyObject *self, PyObject *args, PyObject *kwargs) {
    const char* keywords[] = {"x", "y", "z", "c", NULL};
    int x,y,z,c;
    x=y=z=c=0;
    
    if(!PyArg_ParseTupleAndKeywords(args, kwargs, "i|iii", (char**)keywords, &x, &y, &z, &c)) {
        return NULL;
    }
    
    return PyFloat_FromDouble((*((PyGmicImage*)self)->ptrObj)(x,y,z,c));
}



static void PyGmicImage_dealloc(PyGmicImage * self)
{
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
    { "from_numpy_array", (PyCFunction)PyGmicImage_from_numpy_array, METH_VARARGS|METH_KEYWORDS, "get numpy array's data" },
    {NULL}  /* Sentinel */
};


static PyObject* run_impl(PyObject*, PyObject* args, PyObject* kwargs) 
{

  char const* keywords[] = {"commands_line", "image_or_images", NULL};
  PyObject* input_gmic_image_or_list = NULL;
  char* commands_line = NULL;

  if(!PyArg_ParseTupleAndKeywords(args, kwargs, "s|O!", (char**)keywords, &commands_line, &PyGmicImageType, &input_gmic_image_or_list)) {
      return NULL;
  }


  try {
    if (input_gmic_image_or_list != NULL) {

        Py_INCREF(input_gmic_image_or_list);
        gmic_list<T> images;

        gmic_list<char> image_names; // Empty image names

        images.assign(1);
        images[0]._width = ((PyGmicImage*)input_gmic_image_or_list)->ptrObj->_width;
        images[0]._height = ((PyGmicImage*)input_gmic_image_or_list)->ptrObj->_height;
        images[0]._depth = ((PyGmicImage*)input_gmic_image_or_list)->ptrObj->_depth;
        images[0]._spectrum = ((PyGmicImage*)input_gmic_image_or_list)->ptrObj->_spectrum;
        images[0]._data = ((PyGmicImage*)input_gmic_image_or_list)->ptrObj->_data;
        images[0]._is_shared = ((PyGmicImage*)input_gmic_image_or_list)->ptrObj->_is_shared;

        gmic(commands_line, images, image_names);
        Py_DECREF(input_gmic_image_or_list);
    } else {
        gmic(commands_line, 0, true);
    }

  } catch (gmic_exception& e) {
    PyErr_SetString(PyExc_Exception, e.what());
  } catch (std::exception& e) {
    PyErr_SetString(PyExc_Exception, e.what());
    return NULL;
  }
  return Py_True;
}

static PyMethodDef gmic_methods[] = {
  {"run", (PyCFunction)run_impl, METH_VARARGS|METH_KEYWORDS, "Run the Gmic processor on one or more GmicImage(s), following a gmic command string"},
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
    PyGmicImageType.tp_methods=PyGmicImage_methods;
    PyGmicImageType.tp_repr=(reprfunc)PyGmicImage_repr;
    PyGmicImageType.tp_init=(initproc)PyGmicImage_init;
    PyGmicImageType.tp_call=(ternaryfunc)PyGmicImage_call;
    PyGmicImageType.tp_doc = "Simplified mapping of the c++ gmic_image type. Stores non-publicly a binary buffer of data, a height, width, depth, spectrum.";

    if (PyType_Ready(&PyGmicImageType) < 0)
        return NULL;

    m = PyModule_Create(&gmic_module);
    if (m == NULL)
        return NULL;

    Py_INCREF(&PyGmicImageType);
    PyModule_AddObject(m, "GmicImage", (PyObject *)&PyGmicImageType); // Add GmicImage object to the module
    return m;
}

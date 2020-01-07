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
    gmic_image<T> * ptrObj;
    PyObject* ptrBytesObj;
} PyGmicImage;

static int PyGmicImage_init(PyGmicImage *self, PyObject *args, PyObject *kwds)
// initialize PyGmicImage Object
{
    unsigned int _width;       // Number of image columns (dimension along the X-axis)
    unsigned int _height;      // Number of image lines (dimension along the Y-axis)
    unsigned int _depth;       // Number of image slices (dimension along the Z-axis)
    unsigned int _spectrum;    // Number of image channels (dimension along the C-axis)
    PyObject* bytesObj;
  
    // SKIPPED FOR NOW
    bool _is_shared = false;           // Tells if the data buffer is shared by another structure


    if (! PyArg_ParseTuple(args, "SIIII", &bytesObj, &_width, &_height, &_depth, &_spectrum))
        return -1;

    printf("parsed from binding: _data(bytes): %p, _width: %d, _height: %d, _depth: %d, _spectrum: %d\n", bytesObj, _width, _height, _depth, _spectrum);


    self->ptrObj=new gmic_image<T>();
    self->ptrBytesObj = NULL;
    self->ptrObj->_is_shared = true; //ensure that only Python frees the _data buffer, not the gmic_image destructor

    printf("incoming bytes _data refcount:%d\n", bytesObj->ob_refcnt);
    // prevent memory erasing, by increasing reference counting a little more
    // this turns useful in a case with non-variable-attached initialization: i = gmic.GmicImage(struct.pack('8f', 1, 3, 5, 7, 2, 6, 10, 14), 4,2,1,1)
    Py_INCREF(bytesObj);
    self->ptrBytesObj = bytesObj;
    printf("attached bytes _data refcount:%d\n", self->ptrBytesObj->ob_refcnt);
    // copying memory address of data only
    self->ptrObj->_data = (T*) PyBytes_AsString(self->ptrBytesObj);
    printf("bytes string is: %f%f%f%f\n", self->ptrObj->_data[0], self->ptrObj->_data[1], self->ptrObj->_data[2], self->ptrObj->_data[3]);
    //self->ptrObj->assign(_width, _height, _depth, _spectrum);
    self->ptrObj->_height = _height;
    self->ptrObj->_width = _width;
    self->ptrObj->_depth = _depth;
    self->ptrObj->_spectrum = _spectrum;

    for(int a=0; a<self->ptrObj->_width; a++) {
	    for(int b=0; b<self->ptrObj->_height; b++) {
	    printf("GmicImage(%d, %d): %f\n", a, b, (*self->ptrObj)(a,b));
	    }
    }

    return 0;
}


static PyObject* PyGmicImage_repr(PyGmicImage* self)
{
    cout << "bonsoir" << endl;
    printf("self:%d\n", self);
    printf("self->prtObj:%d\n", self->ptrObj);
    printf("prtObj->_data:%d\n", self->ptrObj->_data);
    for(int a=0; a<self->ptrObj->_width; a++) {

	    for(int b=0; b<self->ptrObj->_height; b++) {
	    printf("GmicImage(%d, %d): %f\n", a, b, (*self->ptrObj)(a,b));
	    }
    }

    printf("attached bytes _data refcount:%d\n", self->ptrBytesObj->ob_refcnt);
    return PyUnicode_FromFormat("<%s object at %p with _data address %p, w=%d h=%d d=%d s=%d>",
                                    Py_TYPE(self)->tp_name, self, self->ptrObj->_data, self->ptrObj->_width, self->ptrObj->_height, self->ptrObj->_depth, self->ptrObj->_spectrum
				    );
}


PyObject *PyGmicImage_call(PyObject *self, PyObject *args, PyObject *kwargs) {
	const char* keywords[] = {"x", "y", "z", "c", NULL};
	int x,y,z,c;
	x=y=z=c=0;

	if(!PyArg_ParseTupleAndKeywords(args, kwargs, "i|iii", (char**)keywords, &x, &y, &z, &c)) {
            return NULL;
	}
	
	return PyFloat_FromDouble((*((PyGmicImage*)self)->ptrObj)(x,y,z,c));

	//char pixel_value[9];
	// snprintf(pixel_value, 9, "%f", (*((PyGmicImage*)self)->ptrObj)(x,y,z,c));
	// printf("asked for pixel value at: x=%d, y=%d, z=%d, c=%d: %s\n", x, y, z, c, pixel_value);
	// Py_RETURN_NONE;
}



static void PyGmicImage_dealloc(PyGmicImage * self)
// destruct the object
{
    if(!self->ptrObj->_is_shared) {
        free(self->ptrObj->_data);
    }
    if(self->ptrBytesObj != NULL) {
        Py_DECREF(self->ptrBytesObj);
    }
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
    PyGmicImageType.tp_repr=(reprfunc)PyGmicImage_repr;
    PyGmicImageType.tp_init=(initproc)PyGmicImage_init;
    PyGmicImageType.tp_call=(ternaryfunc)PyGmicImage_call;

    if (PyType_Ready(&PyGmicImageType) < 0)
        return NULL;

    m = PyModule_Create(&gmic_module);
    if (m == NULL)
        return NULL;

    Py_INCREF(&PyGmicImageType);
    PyModule_AddObject(m, "GmicImage", (PyObject *)&PyGmicImageType); // Add GmicImage object to the module
    return m;
    
}

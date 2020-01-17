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

// Disallow all gmic_image attributes to be written
static int PyGmicImage_setattro(PyGmicImage* self, PyObject* attr, PyObject* value)
{
    char* name = PyUnicode_AsUTF8(attr);
    if (strcmp(name, "_data") == 0 || strcmp(name, "_width") == 0 || strcmp(name, "_height") == 0 || strcmp(name, "_depth") == 0 || strcmp(name, "_spectrum") == 0 || strcmp(name, "_is_shared") == 0)
    {
        PyErr_Format(PyExc_AttributeError,
                     "'%.50s' object attribute '%.400s' is read-only",
                     Py_TYPE(self)->tp_name, name);
    }
    else
    {
        PyErr_Format(PyExc_AttributeError,
                     "'%.50s' object has no attribute '%.400s'",
                     Py_TYPE(self)->tp_name, name);
    }

    return -1;
}

// Allow gmic_image attributes to be read only
static PyObject * PyGmicImage_getattro(PyGmicImage* self, PyObject *attr)
{
    char* name = PyUnicode_AsUTF8(attr);

    if (strcmp(name, "_data") == 0)
    {
        return PyBytes_FromStringAndSize((char*)self->ptrObj->_data, sizeof(T)*(self->ptrObj->_width)*(self->ptrObj->_height)*(self->ptrObj->_depth)*(self->ptrObj->_spectrum));
    }
    else if (strcmp(name, "_width") == 0)
    {
        return PyLong_FromLong((long)self->ptrObj->_width);
    }
    else if (strcmp(name, "_height") == 0)
    {
        return PyLong_FromLong((long)self->ptrObj->_height);
    }
    else if (strcmp(name, "_depth") == 0)
    {
        return PyLong_FromLong((long)self->ptrObj->_depth);
    }
    else if (strcmp(name, "_spectrum") == 0)
    {
        return PyLong_FromLong((long)self->ptrObj->_spectrum);
    }
    else if (strcmp(name, "_is_shared") == 0)
    {
        return PyBool_FromLong((long)self->ptrObj->_is_shared);
    }

    PyErr_Format(PyExc_AttributeError,
                 "'%.50s' object has no attribute '%.400s'",
                 Py_TYPE(self)->tp_name, name);
    return NULL;
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

  char const* keywords[] = {"commands_line", "images", "image_names", NULL};
  PyObject* input_gmic_images = NULL;
  PyObject* input_gmic_image_names = NULL;
  char* commands_line = NULL;
  int image_position;
  int image_name_position;
  int images_count;
  int image_names_count;
  gmic_list<T> images;
  gmic_list<char> image_names; // Empty image names
  PyObject* current_image = NULL;
  PyObject* current_image_name = NULL;
  PyObject* iter = NULL;

  if(!PyArg_ParseTupleAndKeywords(args, kwargs, "s|OO", (char**)keywords, &commands_line, &input_gmic_images, &input_gmic_image_names)) {
      return NULL;
  }

// TODO turn image names into a list of char*

  try {

    Py_XINCREF(input_gmic_image_names);

    if (input_gmic_images != NULL) {
        Py_INCREF(input_gmic_images);

        // A/ If a list of images was provided
	if(PyList_Check(input_gmic_images) || PyTuple_Check(input_gmic_images)) {
            image_position = 0;
            images_count = Py_SIZE(input_gmic_images);
            images.assign(images_count);

            // Grab images and check their typing
            iter = PyObject_GetIter(input_gmic_images);
            while ((current_image = PyIter_Next(iter))) {
                if (Py_TYPE(current_image) != (PyTypeObject*)&PyGmicImageType) {
                    PyErr_Format(PyExc_TypeError,
                                 "'%.50s' input object found at position %d in list/tuple is not a '%.400s'",
                                 Py_TYPE(current_image)->tp_name, image_position, PyGmicImageType.tp_name);
                    return NULL;
                }
                images[image_position]._width = ((PyGmicImage*)current_image)->ptrObj->_width;
                images[image_position]._height = ((PyGmicImage*)current_image)->ptrObj->_height;
                images[image_position]._depth = ((PyGmicImage*)current_image)->ptrObj->_depth;
                images[image_position]._spectrum = ((PyGmicImage*)current_image)->ptrObj->_spectrum;
                images[image_position]._data = ((PyGmicImage*)current_image)->ptrObj->_data;
                images[image_position]._is_shared = ((PyGmicImage*)current_image)->ptrObj->_is_shared;

                image_position++;
            }

            // Grab image names and check their typings
            if (input_gmic_image_names != NULL) {
                if(PyList_Check(input_gmic_image_names) || PyTuple_Check(input_gmic_image_names)) {
                    PyObject* iter = PyObject_GetIter(input_gmic_image_names);
                    image_names_count = Py_SIZE(input_gmic_image_names);
                    image_names.assign(image_names_count);
                    image_name_position = 0;

                    while ((current_image_name = PyIter_Next(iter))) {
                        if (!PyUnicode_Check(current_image_name)) {
                            PyErr_Format(PyExc_TypeError,
                                         "'%.50s' input element found at position %d in list/tuple is not a '%.400s'",
                                         Py_TYPE(current_image_name)->tp_name, image_name_position, PyUnicode_Type.tp_name);
                            return NULL;
                        }
                        image_names[image_name_position]._data = PyUnicode_AsUTF8(current_image_name);
                        image_name_position++;
                    }
                }
            }

            // Process images and names
            gmic(commands_line, images, image_names);

            // Prevent images auto-deallocation by G'MIC
            image_position = 0;
            iter = PyObject_GetIter(input_gmic_images);
            while ((current_image = PyIter_Next(iter))) {
                // Put back the possibly modified reallocated image buffer into the original external GmicImage
                // Back up the image data into the original external image before it gets freed
                swap(((PyGmicImage*)current_image)->ptrObj->_data, images[image_position]._data);
                ((PyGmicImage*)current_image)->ptrObj->_width = images[image_position]._width;
                ((PyGmicImage*)current_image)->ptrObj->_height = images[image_position]._height;
                ((PyGmicImage*)current_image)->ptrObj->_depth = images[image_position]._depth;
                ((PyGmicImage*)current_image)->ptrObj->_spectrum = images[image_position]._spectrum;
                ((PyGmicImage*)current_image)->ptrObj->_is_shared = images[image_position]._is_shared;
                // Prevent freeing the data buffer's pointer now copied into the external image
                images[image_position]._data = 0;

                image_position++;
            }

            // Prevent image names auto-deallocation by G'MIC
            if (input_gmic_image_names != NULL) {
                for(image_name_position = 0; image_name_position < image_names_count; image_name_position++) {
                    image_names[image_name_position]._data = 0;
                }
            }

        // B/ Else if a single GmicImage was provided
	} else if(Py_TYPE(input_gmic_images) == (PyTypeObject*)&PyGmicImageType) {
            images_count = 1;
            images.assign(1);
            image_position = 0;

            images[image_position]._width = ((PyGmicImage*)input_gmic_images)->ptrObj->_width;
            images[image_position]._height = ((PyGmicImage*)input_gmic_images)->ptrObj->_height;
            images[image_position]._depth = ((PyGmicImage*)input_gmic_images)->ptrObj->_depth;
            images[image_position]._spectrum = ((PyGmicImage*)input_gmic_images)->ptrObj->_spectrum;
            images[image_position]._data = ((PyGmicImage*)input_gmic_images)->ptrObj->_data;
            images[image_position]._is_shared = ((PyGmicImage*)input_gmic_images)->ptrObj->_is_shared;

            // Pipe the commands, our single image, and no image names
            gmic(commands_line, images, image_names);

            // Put back the possibly modified reallocated image buffer into the original external GmicImage
            // Back up the image data into the original external image before it gets freed
            swap(((PyGmicImage*)input_gmic_images)->ptrObj->_data, images[0]._data);
            ((PyGmicImage*)input_gmic_images)->ptrObj->_width = images[0]._width;
            ((PyGmicImage*)input_gmic_images)->ptrObj->_height = images[0]._height;
            ((PyGmicImage*)input_gmic_images)->ptrObj->_depth = images[0]._depth;
            ((PyGmicImage*)input_gmic_images)->ptrObj->_spectrum = images[0]._spectrum;
            ((PyGmicImage*)input_gmic_images)->ptrObj->_is_shared = images[0]._is_shared;
            // Prevent freeing the data buffer's pointer now copied into the external image
            images[0]._data = 0;
        }

        Py_XDECREF(input_gmic_images);
    } else {
        gmic(commands_line, 0, true);
    }

    Py_XDECREF(input_gmic_image_names);

  } catch (gmic_exception& e) {
    // TODO bind a new GmicException type?
    PyErr_SetString(PyExc_Exception, e.what());
    return NULL;
  } catch (std::exception& e) {
    PyErr_SetString(PyExc_Exception, e.what());
    return NULL;
  }
  return Py_True;
}

PyDoc_STRVAR(
run_impl_doc,
"run(command: str[, images: GmicImage|list|tuple]), image_names: list|tuple -> bool)\n\n\
Run G'MIC interpret following a G'MIC language command(s) string, on 0 or more GmicImage(s).\n\n\
Example:\n\
import gmic\n\
import struct\n\
import random\n\
gmic.run('echo_stdout \'hello world\'') # G'MIC command without images parameter\n\
a = gmic.GmicImage(struct.pack(*('256f',) + tuple([random.random() for a in range(256)])), 16, 16) # Build 16x16 greyscale image\n\
gmic.run('blur 12,0,1 resize 50%,50%', a) # Blur then resize the image\n\
a._width == a._height == 8 # The image is half smaller\n\
gmic.run('display', a) # If you have X11 enabled (linux only), show the image in a window");

static PyMethodDef gmic_methods[] = {
  {"run", (PyCFunction)run_impl, METH_VARARGS|METH_KEYWORDS, run_impl_doc},
  {nullptr, nullptr, 0, nullptr }
};

PyDoc_STRVAR(
gmic_module_doc,
"G'MIC Image Processing library Python binding\n\n\
Use gmic.run(...), gmic.GmicImage(...), gmic.GmicList(...).\n\
Make sure to visit https://github.com/myselfhimself/gmic-py for examples and documentation.");

PyModuleDef gmic_module = {
  PyModuleDef_HEAD_INIT,
  "gmic",
  gmic_module_doc,
  0,
  gmic_methods
};

PyDoc_STRVAR(
GmicImage_doc,
"GmicImage(data: bytes[, width: int = 1, height: int = 1, depth: int = 1, spectrum: int = 1, shared: bool = False]) -> bool\n\n\
Simplified mapping of the c++ gmic_image type. Stores non-publicly a binary buffer of data, a height, width, depth, spectrum.\n\n\
Example:\n\
import gmic\n\
import struct\n\
i = gmic.GmicImage(struct.pack('2f', 0.0, 1.5), 1, 1) # 2D 1x1 image\n\
gmic.run('add 1', i) # GmicImage injection into G'MIC's interpreter\n\
i # Using GmicImage's repr() string representation\n\
# Output: <gmic.GmicImage object at 0x7f09bfb504f8 with _data address at 0x22dd5b0, w=1 h=1 d=1 s=1 shared=0>\n\
i(0,0) == 1.0 # Using GmicImage(x,y,z) pixel reading operator after initialization\n\
gmic.run('resize 200%,200%', i) # Some G'MIC operations may reallocate the image buffer in place without risk\n\
i._width == i._height == 2 # Use the _width, _height, _depth, _spectrum, _data, _is_shared read-only attributes");

PyMODINIT_FUNC PyInit_gmic() {
    PyObject* m;

    PyGmicImageType.tp_new = PyType_GenericNew;
    PyGmicImageType.tp_basicsize=sizeof(PyGmicImage);
    PyGmicImageType.tp_dealloc=(destructor) PyGmicImage_dealloc;
    PyGmicImageType.tp_methods=PyGmicImage_methods;
    PyGmicImageType.tp_repr=(reprfunc)PyGmicImage_repr;
    PyGmicImageType.tp_init=(initproc)PyGmicImage_init;
    PyGmicImageType.tp_call=(ternaryfunc)PyGmicImage_call;
    PyGmicImageType.tp_getattro=(getattrofunc)PyGmicImage_getattro;
    PyGmicImageType.tp_setattro=(setattrofunc)PyGmicImage_setattro;
    PyGmicImageType.tp_doc=GmicImage_doc;

    if (PyType_Ready(&PyGmicImageType) < 0)
        return NULL;

    m = PyModule_Create(&gmic_module);
    if (m == NULL)
        return NULL;

    Py_INCREF(&PyGmicImageType);
    PyModule_AddObject(m, "GmicImage", (PyObject *)&PyGmicImageType); // Add GmicImage object to the module
    return m;
}

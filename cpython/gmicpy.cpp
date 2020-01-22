#include <Python.h>
#include "structmember.h"
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
    PyObject* dict;
    gmic_image<T> ptrObj; // G'MIC library's Gmic Image
} PyGmicImage;

static int PyGmicImage_init(PyGmicImage *self, PyObject *args, PyObject *kwargs)
{
    unsigned int _width;       // Number of image columns (dimension along the X-axis)
    unsigned int _height;      // Number of image lines (dimension along the Y-axis)
    unsigned int _depth;       // Number of image slices (dimension along the Z-axis)
    unsigned int _spectrum;    // Number of image channels (dimension along the C-axis)
    Py_ssize_t dimensions_product;    // All integer parameters multiplied together, will help for allocating (ie. assign()ing)
    Py_ssize_t _data_bytes_size;
    int _is_shared = (int) false; // Whether image should be shared across gmic operations (if true, operations like resize will fail)
    PyObject* bytesObj;        // Incoming bytes buffer object pointer
    char const* keywords[] = {"data", "width", "height", "depth", "spectrum", "shared", NULL};
    _width=_height=_depth=_spectrum=1;

    if (! PyArg_ParseTupleAndKeywords(args, kwargs, "S|IIIIp", (char**) keywords, &bytesObj, &_width, &_height, &_depth, &_spectrum, &_is_shared))
        return -1;

    dimensions_product = _width*_height*_depth*_spectrum;
    _data_bytes_size = PyBytes_Size(bytesObj);
    if((Py_ssize_t)(dimensions_product*sizeof(T)) != _data_bytes_size)
    {
        PyErr_Format(PyExc_ValueError, "GmicImage dimensions-induced buffer bytes size (%d*%dB=%d) cannot be strictly negative or different than the _data buffer size in bytes (%d)", dimensions_product, sizeof(T), dimensions_product*sizeof(T), _data_bytes_size);
	return -1;
    }

    try {
        self->ptrObj.assign(_width,_height,_depth,_spectrum);
    }
    // Ugly exception catching, probably to catch a cimg::GmicInstanceException()
    catch(...)
    {
        PyErr_Format(PyExc_MemoryError, "Allocation error in GmicImage::assign(_width=%d,_height=%d,_depth=%d,_spectrum=%d), are you requesting too much memory (%d bytes)?", _width, _height, _depth, _spectrum, _data_bytes_size);
        return -1;
    }

    self->ptrObj._is_shared = _is_shared;

    memcpy(self->ptrObj._data, PyBytes_AsString(bytesObj), PyBytes_Size(bytesObj));

    return 0;
}

static PyObject* PyGmicImage_repr(PyGmicImage* self)
{
    return PyUnicode_FromFormat("<%s object at %p with _data address at %p, w=%d h=%d d=%d s=%d shared=%d>",
        Py_TYPE(self)->tp_name,
        self, self->ptrObj._data,
        self->ptrObj._width,
        self->ptrObj._height,
        self->ptrObj._depth,
        self->ptrObj._spectrum,
        self->ptrObj._is_shared
    );
}


static PyObject *PyGmicImage_call(PyObject *self, PyObject *args, PyObject *kwargs) {
    const char* keywords[] = {"x", "y", "z", "c", NULL};
    int x,y,z,c;
    x=y=z=c=0;
    
    if(!PyArg_ParseTupleAndKeywords(args, kwargs, "i|iii", (char**)keywords, &x, &y, &z, &c)) {
        return NULL;
    }
    
    return PyFloat_FromDouble(((PyGmicImage*)self)->ptrObj(x,y,z,c));
}



static void PyGmicImage_dealloc(PyGmicImage * self)
{
    Py_TYPE(self)->tp_free(self);
}



static PyObject * PyGmicImage_from_numpy_array(PyGmicImage * self, PyObject* args)
{
int retval;

// todo array of floats instead from numpy array
    if (! PyArg_ParseTuple(args, "f", &self->ptrObj._data))
        return Py_False;

    retval = (self->ptrObj)._data != NULL;

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

  char const* keywords[] = {"command", "images", "image_names", NULL};
  PyObject* input_gmic_images = NULL;
  PyObject* input_gmic_image_names = NULL;
  char* commands_line = NULL;
  int image_position;
  int image_name_position;
  int images_count;
  int image_names_count;
  gmic_list<T> images;
  gmic_list<char> image_names; // Empty image names
  char* current_image_name_raw;
  PyObject* current_image = NULL;
  PyObject* current_image_name = NULL;
  PyObject* iter = NULL;

  if(!PyArg_ParseTupleAndKeywords(args, kwargs, "s|OO", (char**)keywords, &commands_line, &input_gmic_images, &input_gmic_image_names)) {
      return NULL;
  }

  try {

    Py_XINCREF(input_gmic_images);
    Py_XINCREF(input_gmic_image_names);


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
                                 "'%.50s' input element found at position %d in 'image_names' list/tuple is not a '%.400s'",
                                 Py_TYPE(current_image_name)->tp_name, image_name_position, PyUnicode_Type.tp_name);
                    Py_XDECREF(input_gmic_images);
                    Py_XDECREF(input_gmic_image_names);

                    return NULL;
                }

		current_image_name_raw = (char*) PyUnicode_AsUTF8(current_image_name);
                image_names[image_name_position].assign(strlen(current_image_name_raw)+1);
		memcpy(image_names[image_name_position]._data, current_image_name_raw, image_names[image_name_position]._width);
		image_name_position++;
            }

        } else {
            PyErr_Format(PyExc_TypeError,
                "'%.50s' 'image_names' parameter must be a list/tuple of '%.400s'(s)",
                Py_TYPE(input_gmic_images)->tp_name, PyUnicode_Type.tp_name);
            Py_XDECREF(input_gmic_images);
            Py_XDECREF(input_gmic_image_names);

            return NULL;
        }
    }

    if (input_gmic_images != NULL) {
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
                                 "'%.50s' input object found at position %d in 'images' list/tuple is not a '%.400s'",
                                 Py_TYPE(current_image)->tp_name, image_position, PyGmicImageType.tp_name);

                    Py_XDECREF(input_gmic_images);
                    Py_XDECREF(input_gmic_image_names);

                    return NULL;
                }
                images[image_position]._width = ((PyGmicImage*)current_image)->ptrObj._width;
                images[image_position]._height = ((PyGmicImage*)current_image)->ptrObj._height;
                images[image_position]._depth = ((PyGmicImage*)current_image)->ptrObj._depth;
                images[image_position]._spectrum = ((PyGmicImage*)current_image)->ptrObj._spectrum;
                images[image_position]._data = ((PyGmicImage*)current_image)->ptrObj._data;
                images[image_position]._is_shared = ((PyGmicImage*)current_image)->ptrObj._is_shared;

                image_position++;
            }

            // Process images and names
            gmic(commands_line, images, image_names);

            // Prevent images auto-deallocation by G'MIC
	    // TODO adapt to new images list size!!! (list.size())
	    // TODO adapt to new image names list size!!!
            image_position = 0;
            iter = PyObject_GetIter(input_gmic_images);
            while ((current_image = PyIter_Next(iter))) {
                // Put back the possibly modified reallocated image buffer into the original external GmicImage
                // Back up the image data into the original external image before it gets freed
                swap(((PyGmicImage*)current_image)->ptrObj._data, images[image_position]._data);
                ((PyGmicImage*)current_image)->ptrObj._width = images[image_position]._width;
                ((PyGmicImage*)current_image)->ptrObj._height = images[image_position]._height;
                ((PyGmicImage*)current_image)->ptrObj._depth = images[image_position]._depth;
                ((PyGmicImage*)current_image)->ptrObj._spectrum = images[image_position]._spectrum;
                ((PyGmicImage*)current_image)->ptrObj._is_shared = images[image_position]._is_shared;
                // Prevent freeing the data buffer's pointer now copied into the external image
                images[image_position]._data = 0;

                image_position++;
            }

        // B/ Else if a single GmicImage was provided
	} else if(Py_TYPE(input_gmic_images) == (PyTypeObject*)&PyGmicImageType) {
            images_count = 1;
            images.assign(1);
            image_position = 0;

            images[image_position]._width = ((PyGmicImage*)input_gmic_images)->ptrObj._width;
            images[image_position]._height = ((PyGmicImage*)input_gmic_images)->ptrObj._height;
            images[image_position]._depth = ((PyGmicImage*)input_gmic_images)->ptrObj._depth;
            images[image_position]._spectrum = ((PyGmicImage*)input_gmic_images)->ptrObj._spectrum;
            images[image_position]._data = ((PyGmicImage*)input_gmic_images)->ptrObj._data;
            images[image_position]._is_shared = ((PyGmicImage*)input_gmic_images)->ptrObj._is_shared;

            // Pipe the commands, our single image, and no image names
            gmic(commands_line, images, image_names);
            // TODO adapt to new images list size!!! (list.size())
            // TODO adapt to new image names list size!!!

            // Put back the possibly modified reallocated image buffer into the original external GmicImage
            // Back up the image data into the original external image before it gets freed
            swap(((PyGmicImage*)input_gmic_images)->ptrObj._data, images[0]._data);
            ((PyGmicImage*)input_gmic_images)->ptrObj._width = images[0]._width;
            ((PyGmicImage*)input_gmic_images)->ptrObj._height = images[0]._height;
            ((PyGmicImage*)input_gmic_images)->ptrObj._depth = images[0]._depth;
            ((PyGmicImage*)input_gmic_images)->ptrObj._spectrum = images[0]._spectrum;
            ((PyGmicImage*)input_gmic_images)->ptrObj._is_shared = images[0]._is_shared;
            // Prevent freeing the data buffer's pointer now copied into the external image
            images[0]._data = 0;
        } else {
            PyErr_Format(PyExc_TypeError,
                "'%.50s' 'images' parameter must be a '%.400s' or list/tuple of '%.400s'(s)",
                Py_TYPE(input_gmic_images)->tp_name, PyGmicImageType.tp_name, PyGmicImageType.tp_name);
            Py_XDECREF(input_gmic_images);
            Py_XDECREF(input_gmic_image_names);

            return NULL;
	}

        // If an image names list was provided, even if wrongly typed, let us update its Python object
        // in place, to mirror any kind of changes that may have taken place in the gmic_list of image names
        if (input_gmic_image_names != NULL) {
            // TODO implement copy-back
            // cimglist_for(image_names,l) {
            //   strreplace_bw(files[l]);
            //   files[l].back() = ',';
            // }
        }

    } else {
        gmic(commands_line, 0, true);
    }

    Py_XDECREF(input_gmic_images);
    Py_XDECREF(input_gmic_image_names);

  } catch (gmic_exception& e) {
    // TODO bind a new GmicException type?
    PyErr_SetString(PyExc_Exception, e.what());
    return NULL;
  } catch (std::exception& e) {
    PyErr_SetString(PyExc_Exception, e.what());
    return NULL;
  }
  Py_RETURN_NONE;
}

PyDoc_STRVAR(
run_impl_doc,
"run(command: str[, images: GmicImage|list|tuple, image_names: list|tuple]) -> bool\n\n\
Run G'MIC interpret following a G'MIC language command(s) string, on 0 or more GmicImage(s).\n\n\
Example:\n\
import gmic\n\
import struct\n\
import random\n\
gmic.run('echo_stdout \'hello world\'') # G'MIC command without images parameter\n\
a = gmic.GmicImage(struct.pack(*('256f',) + tuple([random.random() for a in range(256)])), 16, 16) # Build 16x16 greyscale image\n\
gmic.run('blur 12,0,1 resize 50%,50%', a) # Blur then resize the image\n\
a._width == a._height == 8 # The image is half smaller\n\
gmic.run('display', a) # If you have X11 enabled (linux only), show the image in a window\n\
image_names = ['img_' + str(i) for i in range(10)] # You can also name your images if you have several (optional)\n\
images = [gmic.GmicImage(struct.pack(*((str(w*h)+'f',) + (i*2.0,)*w*h)), w, h) for i in range(10)] # Prepare a list of image\n\
gmic.run('add 1 print', images, image_names) # And pipe those into the interpret");

static PyMethodDef gmic_methods[] = {
  {"run", (PyCFunction)run_impl, METH_VARARGS|METH_KEYWORDS, run_impl_doc},
  {nullptr, nullptr, 0, nullptr }
};

PyDoc_STRVAR(
gmic_module_doc,
"G'MIC Image Processing library Python binding\n\n\
Use gmic.run(...), gmic.GmicImage(...), gmic.Gmic(...).\n\
Make sure to visit https://github.com/myselfhimself/gmic-py for examples and documentation.");

PyModuleDef gmic_module = {
  PyModuleDef_HEAD_INIT,
  "gmic",
  gmic_module_doc,
  0,
  gmic_methods
};

PyDoc_STRVAR(
PyGmicImage_doc,
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
// TODO add gmic.Gmic example


static PyMemberDef PyGmicImage_members[] = {
    {(char*)"_width", T_UINT, offsetof(PyGmicImage, ptrObj), READONLY,
     (char*)"width"},
    {(char*)"_height", T_UINT, offsetof(PyGmicImage, ptrObj)+sizeof(unsigned int), READONLY,
     (char*)"height"},
    {(char*)"_depth", T_UINT, offsetof(PyGmicImage, ptrObj)+2*sizeof(unsigned int), READONLY,
     (char*)"depth"},
    {(char*)"_spectrum", T_UINT, offsetof(PyGmicImage, ptrObj)+3*sizeof(unsigned int), READONLY,
     (char*)"spectrum"},
    {(char*)"_is_shared", T_BOOL, offsetof(PyGmicImage, ptrObj)+4*sizeof(unsigned int), READONLY,
     (char*)"_is_shared"},
    {NULL}  /* Sentinel */
};

static PyObject*
PyGmicImage_get__data(PyGmicImage* self, void* closure)
{
    return PyBytes_FromStringAndSize((char*)self->ptrObj._data, sizeof(T)*(self->ptrObj._width)*(self->ptrObj._height)*(self->ptrObj._depth)*(self->ptrObj._spectrum));
}

PyGetSetDef PyGmicImage_getsets[] = {
    {(char*)"_data",  /* name */
     (getter) PyGmicImage_get__data,
     NULL, // no setter
     NULL,  /* doc */
     NULL /* closure */},
    {NULL}
};

static PyObject *
PyGmicImage_richcompare(PyObject *self, PyObject *other, int op)
{
    PyObject *result = NULL;

    if (Py_TYPE(other) != Py_TYPE(self)) {
        result = Py_NotImplemented;
    }
    else {
        switch (op) {
        case Py_LT:
        case Py_LE:
        case Py_GT:
        case Py_GE:
            result = Py_NotImplemented;
            break;
        case Py_EQ:
            // Leverage the CImg == C++ operator
            result = ((PyGmicImage*)self)->ptrObj == ((PyGmicImage*)other)->ptrObj ? Py_True : Py_False;
            break;
        case Py_NE:
            // Leverage the CImg != C++ operator
            result = ((PyGmicImage*)self)->ptrObj != ((PyGmicImage*)other)->ptrObj ? Py_True : Py_False;
            break;
        }
    }

    Py_XINCREF(result);
    return result;
}

PyMODINIT_FUNC PyInit_gmic() {
    PyObject* m;

    PyGmicImageType.tp_new = PyType_GenericNew;
    PyGmicImageType.tp_basicsize=sizeof(PyGmicImage);
    PyGmicImageType.tp_dealloc=(destructor) PyGmicImage_dealloc;
    PyGmicImageType.tp_methods=PyGmicImage_methods;
    PyGmicImageType.tp_repr=(reprfunc)PyGmicImage_repr;
    PyGmicImageType.tp_init=(initproc)PyGmicImage_init;
    PyGmicImageType.tp_call=(ternaryfunc)PyGmicImage_call;
    PyGmicImageType.tp_getattro=PyObject_GenericGetAttr;
    PyGmicImageType.tp_doc=PyGmicImage_doc;
    PyGmicImageType.tp_members=PyGmicImage_members;
    PyGmicImageType.tp_dictoffset = offsetof(PyGmicImage,dict);
    PyGmicImageType.tp_getset = PyGmicImage_getsets;
    PyGmicImageType.tp_richcompare = PyGmicImage_richcompare;

    if (PyType_Ready(&PyGmicImageType) < 0)
        return NULL;

    m = PyModule_Create(&gmic_module);
    if (m == NULL)
        return NULL;

    Py_INCREF(&PyGmicImageType);
    PyModule_AddObject(m, "GmicImage", (PyObject *)&PyGmicImageType); // Add GmicImage object to the module
    return m;
}

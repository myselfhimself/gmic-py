#include <Python.h>
#include "structmember.h"
#include <iostream>
#include <stdio.h>
#include "gmicpy.h"

using namespace std;


//------- G'MIC MAIN TYPES ----------//

static PyTypeObject PyGmicImageType = { PyVarObject_HEAD_INIT(NULL, 0)
                                    "gmic.GmicImage"   /* tp_name */
                                };


static PyTypeObject PyGmicType = { PyVarObject_HEAD_INIT(NULL, 0)
                                    "gmic.Gmic"   /* tp_name */
                                };

typedef struct {
    PyObject_HEAD
    gmic_image<T> _gmic_image; // G'MIC library's Gmic Image
} PyGmicImage;


typedef struct {
    PyObject_HEAD
    // Using a pointer here and PyGmic_init()-time instantiation fixes a crash with
    // empty G'MIC command-set.
    gmic* _gmic; // G'MIC library's interpreter instance
} PyGmic;

//--- NUMPY ARRAYS PROCESSING MACROS ----//
// Macro returning (int) true if type if PyObject* op is a numpy.ndarray
#define PyNumpyArray_Check(op) ((int) (strcmp(((PyTypeObject *)PyObject_Type(op))->tp_name, "numpy.ndarray") == 0))
// Macro returning GmicImage version of PyObject* op with type numpy.ndarray
#define PyNumpyArray_AS_PYGMICIMAGE(op) (PyObject_CallFunction((PyObject*) &PyGmicImageType, (const char*) "O", op))
#define PyGmicImage_AS_NUMPYARRAY(shape, dtype, buffer, any_numpy_object) (PyObject_CallFunction(PyObject_Type(any_numpy_object), (const char*) "OOS", shape, dtype, buffer))

/* TODO REMOVE THOSE NOTES WHEN READY
PyGmicImage_AS_NUMPYARRAY(Py_BuildValue("(00)", 2, 1), &PyFloat_Type, PyBytes_FromStringAndSize(current_image->_gmic_image.data, sizeof(T)*current_image->_gmic_imag.size()), any_numpy_object)
*/
// NDArray constructor: https://docs.scipy.org/doc/numpy/reference/generated/numpy.ndarray.html#numpy.ndarray
// class numpy.ndarray(shape, dtype=float, buffer=None, offset=0, strides=None, order=None)
//>>> type(a)
//<class 'numpy.ndarray'>
//>>> type(a)((2,1), dtype=np.dtype(int), buffer=struct.pack('=4i', 3, 0, 2, 0))
//array([[3],
//       [2]])
//


//------- G'MIC INTERPRETER INSTANCE BINDING ----------//


static PyObject* PyGmic_repr(PyGmic* self)
{
    return PyUnicode_FromFormat("<%s interpreter object at %p with _gmic address at %p>",
        Py_TYPE(self)->tp_name,
        self, self->_gmic
    );
}

/* Copy a GmicImage's contents into a gmic_list at a given position. Run this typically before a gmic.run(). */
static void swap_gmic_image_into_gmic_list(PyGmicImage* image, gmic_list<T>& images, int position) {
    images[position].assign(image->_gmic_image._width, image->_gmic_image._height, image->_gmic_image._depth, image->_gmic_image._spectrum);
    images[position]._width = image->_gmic_image._width;
    images[position]._height = image->_gmic_image._height;
    images[position]._depth = image->_gmic_image._depth;
    images[position]._spectrum = image->_gmic_image._spectrum;
    memcpy(images[position]._data, image->_gmic_image._data, image->_gmic_image.size()*sizeof(T));
    images[position]._is_shared = image->_gmic_image._is_shared;
}

/* Copy a GmicList's image at given index into an external GmicImage. Run this typically after gmic.run(). */
void swap_gmic_list_item_into_gmic_image(gmic_list<T>& images, int position, PyGmicImage* image) {
    // Put back the possibly modified reallocated image buffer into the original external GmicImage
    // Back up the image data into the original external image before it gets freed
    swap(image->_gmic_image._data, images[position]._data);
    image->_gmic_image._width = images[position]._width;
    image->_gmic_image._height = images[position]._height;
    image->_gmic_image._depth = images[position]._depth;
    image->_gmic_image._spectrum = images[position]._spectrum;
    image->_gmic_image._is_shared = images[position]._is_shared;
    // Prevent freeing the data buffer's pointer now copied into the external image
    images[position]._data = 0;
}


static PyObject* run_impl(PyObject* self, PyObject* args, PyObject* kwargs)
{

  char const* keywords[] = {"command", "images", "image_names", NULL};
  PyObject* input_gmic_images = NULL;
  PyObject* input_gmic_image_names = NULL;
  char* commands_line = NULL;
  int image_position;
  int image_name_position;
  int image_names_count;
  gmic_list<T> images;
  gmic_list<char> image_names; // Empty image names
  char* current_image_name_raw;
  PyObject* current_image = NULL;
  PyObject* current_image_name = NULL;
  PyObject* iter = NULL;
  bool must_return_all_items_as_numpy_array = false;
  PyObject* any_numpy_object = NULL;

  if(!PyArg_ParseTupleAndKeywords(args, kwargs, "s|OO", (char**)keywords, &commands_line, &input_gmic_images, &input_gmic_image_names)) {
      return NULL;
  }

  try {

    Py_XINCREF(input_gmic_images);
    Py_XINCREF(input_gmic_image_names);


    // Grab image names or single image name and check typings
    if (input_gmic_image_names != NULL) {
        // If list of image names provided
        if(PyList_Check(input_gmic_image_names)) {
            PyObject* iter = PyObject_GetIter(input_gmic_image_names);
            image_names_count = Py_SIZE(input_gmic_image_names);
            image_names.assign(image_names_count);
            image_name_position = 0;

            while ((current_image_name = PyIter_Next(iter))) {
                if (!PyUnicode_Check(current_image_name)) {
                    PyErr_Format(PyExc_TypeError,
                                 "'%.50s' input element found at position %d in 'image_names' list is not a '%.400s'",
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

	// If single image name provided
        } else if (PyUnicode_Check(input_gmic_image_names)) {
	    // Enforce also non-null single-GmicImage 'images' parameter
            if (input_gmic_images != NULL && Py_TYPE(input_gmic_images) != (PyTypeObject*)&PyGmicImageType) {
                PyErr_Format(PyExc_TypeError,
                             "'%.50s' 'images' parameter must be a '%.400s' if the 'image_names' parameter is a bare '%.400s'.",
                             Py_TYPE(input_gmic_images)->tp_name, PyGmicImageType.tp_name, PyUnicode_Type.tp_name);
                Py_XDECREF(input_gmic_images);
                Py_XDECREF(input_gmic_image_names);

                return NULL;
	    }

            image_names.assign(1);
	    current_image_name_raw = (char*) PyUnicode_AsUTF8(input_gmic_image_names);
	    image_names[0].assign(strlen(current_image_name_raw)+1);
	    memcpy(image_names[0]._data, current_image_name_raw, image_names[0]._width);
	// If neither a list of strings nor a single string were provided, raise exception
        } else {
            PyErr_Format(PyExc_TypeError,
                "'%.50s' 'image_names' parameter must be a list of '%.400s'(s)",
                Py_TYPE(input_gmic_image_names)->tp_name, PyUnicode_Type.tp_name);
            Py_XDECREF(input_gmic_images);
            Py_XDECREF(input_gmic_image_names);

            return NULL;
        }
    }

    if (input_gmic_images != NULL) {
        // A/ If a list of images was provided
	if(PyList_Check(input_gmic_images)) {
            image_position = 0;
            images.assign(Py_SIZE(input_gmic_images));

            // Grab images into a proper gmic_list after checking their typing
            iter = PyObject_GetIter(input_gmic_images);
            while ((current_image = PyIter_Next(iter))) {
                if (Py_TYPE(current_image) != (PyTypeObject*)&PyGmicImageType) {
	            // If current image type is a numpy.ndarray
		    if (PyNumpyArray_Check(current_image)) {
			// convert it to a GmicImage transparently
		        current_image = PyNumpyArray_AS_PYGMICIMAGE(current_image);
			any_numpy_object = current_image;
			must_return_all_items_as_numpy_array = true;
		    // Else if type is completely unknown, raise exception
		    } else {
                        PyErr_Format(PyExc_TypeError,
                                     "'%.50s' input object found at position %d in 'images' list is not a '%.400s'",
                                     Py_TYPE(current_image)->tp_name, image_position, PyGmicImageType.tp_name);

                        Py_XDECREF(input_gmic_images);
                        Py_XDECREF(input_gmic_image_names);

                        return NULL;
		   }
                }
		swap_gmic_image_into_gmic_list((PyGmicImage*) current_image, images, image_position);

                image_position++;
            }

            // Process images and names
            ((PyGmic*)self)->_gmic->run(commands_line, images, image_names, 0, 0);

            // Prevent images auto-deallocation by G'MIC
            image_position = 0;

	    // Bring new images set back into the Python world (change List items in-place)
	    // First empty the input Python images list without deleting its List object
            PySequence_DelSlice(input_gmic_images, 0, PySequence_Length(input_gmic_images));
            cimglist_for(images, l) {
		// On the fly python GmicImage build (or numpy.ndarray build if there was an ndarray in the input list)
		// per https://stackoverflow.com/questions/4163018/create-an-object-using-pythons-c-api/4163055#comment85217110_4163055
		PyObject* _data = PyBytes_FromStringAndSize((const char*)images[l]._data, sizeof(T)*images[l].size());
		PyObject* new_gmic_image = NULL;
		if (must_return_all_items_as_numpy_array) {
		    // TODO build shape tuple according to real dimensions
		    new_gmic_image = PyGmicImage_AS_NUMPYARRAY(Py_BuildValue("(00)", 2, 1), &PyFloat_Type, _data, any_numpy_object);
		} else {
                    new_gmic_image = PyObject_CallFunction((PyObject*) &PyGmicImageType,
                                           // The last argument is a p(redicate), ie. boolean..
		    		       // but Py_BuildValue() used by PyObject_CallFunction has a slightly different parameters format specification
		    			(const char*) "SIIIIi",
                                            _data,
		    			(unsigned int) images[l]._width,
		    		       (unsigned int) images[l]._height,
		    	               (unsigned int) images[l]._depth,
		    	               (unsigned int) images[l]._spectrum,
		    	               (int) images[l]._is_shared
		    			);
		    if (new_gmic_image == NULL) {
                        PyErr_Format(PyExc_RuntimeError, "Could not initialize GmicImage for appending it to provided 'images' parameter list.");
		        return NULL;
		    }
		}
                PyList_Append(input_gmic_images, new_gmic_image);
            }

        // B/ Else if a single GmicImage was provided
	} else if(Py_TYPE(input_gmic_images) == (PyTypeObject*)&PyGmicImageType) {
            images.assign(1);
	    swap_gmic_image_into_gmic_list((PyGmicImage*) input_gmic_images, images, 0);

            // Pipe the commands, our single image, and no image names
            ((PyGmic*)self)->_gmic->run(commands_line, images, image_names, 0, 0);

	    // Alter the original image only if the gmic_image list has not been downsized to 0 elements
	    // this may happen with eg. a rm[0] G'MIC command
	    // We must prevent this, because a 'core dumped' happens otherwise
	    if(images.size() > 0) {
		swap_gmic_list_item_into_gmic_image(images, 0, (PyGmicImage*)input_gmic_images);
            }
	    else
	    {
                PyErr_Format(PyExc_RuntimeError,
                    "'%.50s' 'images' single-element parameter was removed by your G\'MIC command. It was probably emptied, your optional 'image_names' list is untouched.",
                    Py_TYPE(input_gmic_images)->tp_name, PyGmicImageType.tp_name, PyGmicImageType.tp_name);
                Py_XDECREF(input_gmic_images);
                Py_XDECREF(input_gmic_image_names);

                return NULL;
	    }
        }
	// Else if provided 'images' type is unknown (or is a single numpy.ndarray, which unfortunately cannot be updated in place), raise Error
	else {
            PyErr_Format(PyExc_TypeError,
                "'%.50s' 'images' parameter must be a '%.400s', or list of either '%.400s'(s) or 'numpy.ndarray'(s)",
                Py_TYPE(input_gmic_images)->tp_name, PyGmicImageType.tp_name, PyGmicImageType.tp_name);
            Py_XDECREF(input_gmic_images);
            Py_XDECREF(input_gmic_image_names);

            return NULL;
	}

        // If a correctly-typed image names parameter was provided, even if wrongly typed, let us update its Python object
        // in place, to mirror any kind of changes that may have taken place in the gmic_list of image names
        if (input_gmic_image_names != NULL) {
            // i) If a list parameter was provided
            if(PyList_Check(input_gmic_image_names)) {
                // First empty the input Python image names list
                PySequence_DelSlice(input_gmic_image_names, 0, PySequence_Length(input_gmic_image_names));
                // Add image names from the Gmic List of names
                cimglist_for(image_names, l) {
                    PyList_Append(input_gmic_image_names, PyUnicode_FromString(image_names[l]));
                }
            }
            // ii) If a str parameter was provided
            // Because of Python's string immutability, we will not change the input string's content here :) :/
	}

    } else {
	T pixel_type;
        ((PyGmic*)self)->_gmic->run((const char* const) commands_line, (float* const) NULL, (bool* const)NULL, (const T&)pixel_type);
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

static int PyGmic_init(PyGmic *self, PyObject *args, PyObject *kwargs)
{
    int result = 0;
    self->_gmic = new gmic();
    // If parameters are provided, pipe them to our run() method, and do only exceptions raising without returning anything if things go well
    if(args != Py_None && ((args && (int)PyTuple_Size(args) > 0) || (kwargs && (int)PyDict_Size(kwargs) > 0))) {
        result = (run_impl((PyObject*) self, args, kwargs) != NULL) ? 0 : -1;
    }
    return result;
}


PyDoc_STRVAR(
run_impl_doc,
"Gmic.run(command: str[, images: GmicImage|List[GmicImage], image_names: str|List[str]]) -> None\n\n\
Run G'MIC interpreter following a G'MIC language command(s) string, on 0 or more namable GmicImage(s).\n\n\
Note (single-image short-hand calling): if 'images' is a GmicImage, then 'image_names' must be either a 'str' or not provided.\n\n\
Example:\n\
import gmic\n\
import struct\n\
import random\n\
instance1 = gmic.Gmic('echo_stdout \'instantiation and run all in one\')\n\
instance2 = gmic.Gmic()\n\
instance2.run('echo_stdout \'hello world\'') # G'MIC command without images parameter\n\
a = gmic.GmicImage(struct.pack(*('256f',) + tuple([random.random() for a in range(256)])), 16, 16) # Build 16x16 greyscale image\n\
instance2.run('blur 12,0,1 resize 50%,50%', a) # Blur then resize the image\n\
a._width == a._height == 8 # The image is half smaller\n\
instance2.run('display', a) # If you have X11 enabled (linux only), show the image in a window\n\
image_names = ['img_' + str(i) for i in range(10)] # You can also name your images if you have several (optional)\n\
images = [gmic.GmicImage(struct.pack(*((str(w*h)+'f',) + (i*2.0,)*w*h)), w, h) for i in range(10)] # Prepare a list of image\n\
instance1.run('add 1 print', images, image_names) # And pipe those into the interpreter\n\
instance1.run('blur 10,0,1 print', images[0], 'my_pic_name') # Short-hand 1-image calling style");

static PyMethodDef PyGmic_methods[] = {
    { "run", (PyCFunction)run_impl, METH_VARARGS|METH_KEYWORDS, run_impl_doc },
    {NULL}  /* Sentinel */
};

// ------------ G'MIC IMAGE BINDING ----//






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
    bool bytesObj_is_ndarray = false;
    bool bytesObj_is_bytes = false;
    PyObject* bytesObj_ndarray_dtype;
    PyObject* bytesObj_ndarray_shape;
    Py_ssize_t bytesObj_ndarray_shape_size;
    PyObject * bytesObj_ndarray_dtype_kind;
    char * bytesObj_ndarray_dtype_name_str;
    char const* keywords[] = {"data", "width", "height", "depth", "spectrum", "shared", NULL};
    _width=_height=_depth=_spectrum=1;

    // Parameters parsing and checking
    if (! PyArg_ParseTupleAndKeywords(args, kwargs, "O|IIIIp", (char**) keywords, &bytesObj, &_width, &_height, &_depth, &_spectrum, &_is_shared))
        return -1;

    bytesObj_is_bytes = (bool) PyBytes_Check(bytesObj);
    bytesObj_is_ndarray = PyNumpyArray_Check(bytesObj);
    if (! bytesObj_is_ndarray && ! bytesObj_is_bytes) {
        PyErr_Format(PyExc_TypeError, "Parameter 'data' must be a 'numpy.ndarray' or a pure-python 'bytes' buffer object.");
	// TODO pytest this
        return -1;
    }

    // Importing numpy.ndarray shape and import buffer after deinterlacing it
    // We are skipping any need for a C API include of numpy, to use either python-language level API or common-python structure access
    if (bytesObj_is_ndarray) {
       // Get ndarray.dtype
       bytesObj_ndarray_dtype = PyObject_GetAttrString(bytesObj, "dtype");
       // Ensure dtype kind is a number we can convert (from dtype values here: https://numpy.org/doc/1.18/reference/generated/numpy.dtype.kind.html#numpy.dtype.kind)
       bytesObj_ndarray_dtype_kind = PyObject_GetAttrString(bytesObj_ndarray_dtype, "kind");
       if (strchr("iuf", (PyUnicode_ReadChar(bytesObj_ndarray_dtype_kind, (Py_ssize_t) 0))) == NULL) {
           PyErr_Format(PyExc_TypeError, "Parameter 'data' of type 'numpy.ndarray' does not contain numbers ie. its 'dtype.kind'(=%U) is not one of 'i', 'u', 'f'.", bytesObj_ndarray_dtype_kind);
	   // TODO pytest this
           return -1;
       }

       bytesObj_ndarray_shape = PyObject_GetAttrString(bytesObj, "shape");
       bytesObj_ndarray_shape_size = PyTuple_GET_SIZE(bytesObj_ndarray_shape);
       switch(bytesObj_ndarray_shape_size) {
	       // TODO maybe skip other images than 2D or 3D
           case 1:
              PyErr_Format(PyExc_TypeError, "Parameter 'data' of type 'numpy.ndarray' is 1D with single-channel, this is not supported yet.");
	      return -1;
	      //_width = (unsigned int) PyLong_AsSize_t(PyTuple_GetItem(bytesObj_ndarray_shape_size, 0));
	   case 2:
              PyErr_Format(PyExc_TypeError, "Parameter 'data' of type 'numpy.ndarray' is 1D with multiple channels, this is not supported yet.");
	      return -1;
	      //TODO set _width, height
	   case 3:
              _width = (unsigned int) PyLong_AsSize_t(PyTuple_GetItem(bytesObj_ndarray_shape, 0));
              _height = (unsigned int) PyLong_AsSize_t(PyTuple_GetItem(bytesObj_ndarray_shape, 1));
              _depth = 1;
              _spectrum = (unsigned int) PyLong_AsSize_t(PyTuple_GetItem(bytesObj_ndarray_shape, 2));
	      break;
	   case 4:
              _width = (unsigned int) PyLong_AsSize_t(PyTuple_GetItem(bytesObj_ndarray_shape, 0));
              _height = (unsigned int) PyLong_AsSize_t(PyTuple_GetItem(bytesObj_ndarray_shape, 1));
              _depth = (unsigned int) PyLong_AsSize_t(PyTuple_GetItem(bytesObj_ndarray_shape, 2));
              _spectrum = (unsigned int) PyLong_AsSize_t(PyTuple_GetItem(bytesObj_ndarray_shape, 3));
	      break;
	   default:
	      if(bytesObj_ndarray_shape_size < 1) {
                  PyErr_Format(PyExc_TypeError, "Parameter 'data' of type 'numpy.ndarray' has an empty shape. This is not supported by this binding.");
	      } else { // case >4
                  PyErr_Format(PyExc_TypeError, "Parameter 'data' of type 'numpy.ndarray' has a shape larger than 3D x 1-256 channels. This is not supported by G'MIC.");
	      }
	      return -1;
	}

       bytesObj_ndarray_dtype_name_str = (char *)PyUnicode_AsUTF8(PyObject_GetAttrString(bytesObj_ndarray_dtype, (const char*) "name"));
       // See also Pillow Image modes: https://pillow.readthedocs.io/en/3.1.x/handbook/concepts.html#concept-modes
       // TODO float64,float64 uint16, uint32, float32, float16, float8
       // We are doing string comparison here instead of introspecting the dtype.kind.num which is expected to be a unique identifier of type
       // Slightly simpler to read.. slightly slower to run
       if (strcmp(bytesObj_ndarray_dtype_name_str, "uint8") == 0) {
       } else {
          PyErr_Format(PyExc_TypeError, "Parameter 'data' of type 'numpy.ndarray' has an understandable shape for us, but its data type '%s' is not supported yet(?).", bytesObj_ndarray_dtype_name_str);
	  return -1;
       }
    }

    // Bytes object spatial dimensions vs. bytes-length checking
    if (bytesObj_is_bytes) {
        dimensions_product = _width*_height*_depth*_spectrum;
        _data_bytes_size = PyBytes_Size(bytesObj);
        if((Py_ssize_t)(dimensions_product*sizeof(T)) != _data_bytes_size)
        {
            PyErr_Format(PyExc_ValueError, "GmicImage dimensions-induced buffer bytes size (%d*%dB=%d) cannot be strictly negative or different than the _data buffer size in bytes (%d)", dimensions_product, sizeof(T), dimensions_product*sizeof(T), _data_bytes_size);
            return -1;
        }
    }

    // Importing input data to an internal buffer
    try {
        self->_gmic_image.assign(_width,_height,_depth,_spectrum);
    }
    // Ugly exception catching, probably to catch a cimg::GmicInstanceException()
    catch(...)
    {
        PyErr_Format(PyExc_MemoryError, "Allocation error in GmicImage::assign(_width=%d,_height=%d,_depth=%d,_spectrum=%d), are you requesting too much memory (%d bytes)?", _width, _height, _depth, _spectrum, _data_bytes_size);
        return -1;
    }

    self->_gmic_image._is_shared = _is_shared;

    if (bytesObj_is_bytes) {
        memcpy(self->_gmic_image._data, PyBytes_AsString(bytesObj), PyBytes_Size(bytesObj));
    } else { // if bytesObj is numpy
	PyObject* bytesObjNumpyBytes = PyObject_CallMethod(bytesObj, "tobytes", NULL);
	unsigned char* ptr = (unsigned char*) PyBytes_AsString(bytesObjNumpyBytes);
	for(unsigned int y=0; y<_height; y++) {
	    for(unsigned int x=0; x<_width; x++) {
	        unsigned char R = *(ptr++);
	        unsigned char G = *(ptr++);
	        unsigned char B = *(ptr++);
		self->_gmic_image(x, y, 0, 0) = (float) R;
		self->_gmic_image(x, y, 0, 1) = (float) G;
		self->_gmic_image(x, y, 0, 2) = (float) B;
            }
	}
    }

    return 0;
}

static PyObject* PyGmicImage_repr(PyGmicImage* self)
{
    return PyUnicode_FromFormat("<%s object at %p with _data address at %p, w=%d h=%d d=%d s=%d shared=%d>",
        Py_TYPE(self)->tp_name,
        self, self->_gmic_image._data,
        self->_gmic_image._width,
        self->_gmic_image._height,
        self->_gmic_image._depth,
        self->_gmic_image._spectrum,
        self->_gmic_image._is_shared
    );
}


static PyObject *PyGmicImage_call(PyObject *self, PyObject *args, PyObject *kwargs) {
    const char* keywords[] = {"x", "y", "z", "c", NULL};
    int x,y,z,c;
    x=y=z=c=0;

    if(!PyArg_ParseTupleAndKeywords(args, kwargs, "i|iii", (char**)keywords, &x, &y, &z, &c)) {
        return NULL;
    }

    return PyFloat_FromDouble(((PyGmicImage*)self)->_gmic_image(x,y,z,c));
}



static void PyGmicImage_dealloc(PyGmicImage * self)
{
    Py_TYPE(self)->tp_free(self);
}



static PyObject * PyGmicImage_from_numpy_array(PyGmicImage * self, PyObject* args)
{
    int retval;

    if (! PyArg_ParseTuple(args, "f", &self->_gmic_image._data))
        return Py_False;

    retval = (self->_gmic_image)._data != NULL;

    return Py_BuildValue("i",retval);
}


static PyMethodDef PyGmicImage_methods[] = {
    { "from_numpy_array", (PyCFunction)PyGmicImage_from_numpy_array, METH_VARARGS|METH_KEYWORDS, "get numpy array's data" },
    {NULL}  /* Sentinel */
};


static PyObject* module_level_run_impl(PyObject*, PyObject* args, PyObject* kwargs)
{
    PyObject* temp_gmic_instance = PyObject_CallObject((PyObject*)(&PyGmicType), NULL);
    // Return None or a Python exception flag
    return run_impl(temp_gmic_instance, args, kwargs);
}

PyDoc_STRVAR(
module_level_run_impl_doc,
"run(command: str[, images: GmicImage|List[GmicImage], image_names: str|List[str]]) -> None\n\n\
Run G'MIC interpreter following a G'MIC language command(s) string, on 0 or more nameable GmicImage(s).\n\n\
This creates a single-use interpret for you and destroys it. For faster run()s, reuse instead ia G'MIC interpret instance, see gmic.Gmic() and its run() method.\n\n\
Note (single-image short-hand calling): if 'images' is a GmicImage, then 'image_names' must be either a 'str' or not provided.\n\n\
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
gmic.run('add 1 print', images, image_names) # And pipe those into the interpreter\n\
gmic.run('blur 10,0,1 print', images[0], 'my_pic_name') # Short-hand 1-image calling style");

static PyMethodDef gmic_methods[] = {
  {"run", (PyCFunction)module_level_run_impl, METH_VARARGS|METH_KEYWORDS, module_level_run_impl_doc},
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
    {(char*)"_width", T_UINT, offsetof(PyGmicImage, _gmic_image), READONLY,
     (char*)"width"},
    {(char*)"_height", T_UINT, offsetof(PyGmicImage, _gmic_image)+sizeof(unsigned int), READONLY,
     (char*)"height"},
    {(char*)"_depth", T_UINT, offsetof(PyGmicImage, _gmic_image)+2*sizeof(unsigned int), READONLY,
     (char*)"depth"},
    {(char*)"_spectrum", T_UINT, offsetof(PyGmicImage, _gmic_image)+3*sizeof(unsigned int), READONLY,
     (char*)"spectrum"},
    {(char*)"_is_shared", T_BOOL, offsetof(PyGmicImage, _gmic_image)+4*sizeof(unsigned int), READONLY,
     (char*)"_is_shared"},
    {NULL}  /* Sentinel */
};

static PyObject*
PyGmicImage_get__data(PyGmicImage* self, void* closure)
{
    return PyBytes_FromStringAndSize((char*)self->_gmic_image._data, sizeof(T)*(self->_gmic_image.size()));
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
            result = ((PyGmicImage*)self)->_gmic_image == ((PyGmicImage*)other)->_gmic_image ? Py_True : Py_False;
            break;
        case Py_NE:
            // Leverage the CImg != C++ operator
            result = ((PyGmicImage*)self)->_gmic_image != ((PyGmicImage*)other)->_gmic_image ? Py_True : Py_False;
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
    PyGmicImageType.tp_getset = PyGmicImage_getsets;
    PyGmicImageType.tp_richcompare = PyGmicImage_richcompare;

    if (PyType_Ready(&PyGmicImageType) < 0)
        return NULL;

    PyGmicType.tp_new = PyType_GenericNew;
    PyGmicType.tp_basicsize=sizeof(PyGmic);
    PyGmicType.tp_methods=PyGmic_methods;
    PyGmicType.tp_repr=(reprfunc)PyGmic_repr;
    PyGmicType.tp_init=(initproc)PyGmic_init;
    PyGmicType.tp_getattro=PyObject_GenericGetAttr;
    //PyGmicType.tp_doc=PyGmicImage_doc;

    if (PyType_Ready(&PyGmicType) < 0)
        return NULL;

    m = PyModule_Create(&gmic_module);
    if (m == NULL)
        return NULL;

    Py_INCREF(&PyGmicImageType);
    Py_INCREF(&PyGmicType);
    PyModule_AddObject(m, "GmicImage", (PyObject *)&PyGmicImageType); // Add GmicImage object to the module
    PyModule_AddObject(m, "Gmic", (PyObject *)&PyGmicType); // Add Gmic object to the module
    PyModule_AddObject(m, "__version__", gmicpy_version_info);
    PyModule_AddObject(m, "__build__", gmicpy_build_info);
    // For more debugging, the user can look at __spec__ automatically set by setup.py

    return m;
}

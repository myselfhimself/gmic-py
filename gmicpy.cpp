#include "gmicpy.h"

#include <Python.h>
#include <stdio.h>

#include <iostream>

#include "structmember.h"

using namespace std;

//------- G'MIC MAIN TYPES ----------//

static PyObject *GmicException;

static PyTypeObject PyGmicImageType = {
    PyVarObject_HEAD_INIT(NULL, 0) "gmic.GmicImage" /* tp_name */
};

static PyTypeObject PyGmicType = {
    PyVarObject_HEAD_INIT(NULL, 0) "gmic.Gmic" /* tp_name */
};

typedef struct {
    PyObject_HEAD gmic_image<T> _gmic_image;  // G'MIC library's Gmic Image
} PyGmicImage;

typedef struct {
    PyObject_HEAD
        // Using a pointer here and PyGmic_init()-time instantiation fixes a
        // crash with empty G'MIC command-set.
        gmic *_gmic;  // G'MIC library's interpreter instance
} PyGmic;

//--- NUMPY ARRAYS PROCESSING MACROS ----//
// Macro returning (int) true if type if PyObject* op is a numpy.ndarray
#define PyNumpyArray_Check(op)                                  \
    ((int)(strcmp(((PyTypeObject *)PyObject_Type(op))->tp_name, \
                  "numpy.ndarray") == 0))
// Macro returning GmicImage version of PyObject* op with type numpy.ndarray
#define PyNumpyArray_AS_PYGMICIMAGE(op)                                     \
    (PyObject_CallFunction((PyObject *)&PyGmicImageType, (const char *)"O", \
                           op))
#define PyGmicImage_AS_NUMPYARRAY(shape, dtype, buffer, any_numpy_object) \
    (PyObject_CallFunction(PyObject_Type(any_numpy_object),               \
                           (const char *)"OOS", shape, dtype, buffer))

/* TODO REMOVE THOSE NOTES WHEN READY
PyGmicImage_AS_NUMPYARRAY(Py_BuildValue("(00)", 2, 1), &PyFloat_Type,
PyBytes_FromStringAndSize(current_image->_gmic_image.data,
sizeof(T)*current_image->_gmic_imag.size()), any_numpy_object)
*/
// NDArray constructor:
// https://docs.scipy.org/doc/numpy/reference/generated/numpy.ndarray.html#numpy.ndarray
// class numpy.ndarray(shape, dtype=float, buffer=None, offset=0, strides=None,
// order=None)
//>>> type(a)
//<class 'numpy.ndarray'>
//>>> type(a)((2,1), dtype=np.dtype(int), buffer=struct.pack('=4i', 3, 0, 2,
// 0)) array([[3],
//       [2]])
//

//------- G'MIC INTERPRETER INSTANCE BINDING ----------//

static PyObject *
PyGmic_repr(PyGmic *self)
{
    return PyUnicode_FromFormat(
        "<%s interpreter object at %p with _gmic address at %p>",
        Py_TYPE(self)->tp_name, self, self->_gmic);
}

/* Copy a GmicImage's contents into a gmic_list at a given position. Run this
 * typically before a gmic.run(). */
static void
swap_gmic_image_into_gmic_list(PyGmicImage *image, gmic_list<T> &images,
                               int position)
{
    images[position].assign(
        image->_gmic_image._width, image->_gmic_image._height,
        image->_gmic_image._depth, image->_gmic_image._spectrum);
    images[position]._width = image->_gmic_image._width;
    images[position]._height = image->_gmic_image._height;
    images[position]._depth = image->_gmic_image._depth;
    images[position]._spectrum = image->_gmic_image._spectrum;
    memcpy(images[position]._data, image->_gmic_image._data,
           image->_gmic_image.size() * sizeof(T));
    images[position]._is_shared = image->_gmic_image._is_shared;
}

/* Copy a GmicList's image at given index into an external GmicImage. Run this
 * typically after gmic.run(). */
void
swap_gmic_list_item_into_gmic_image(gmic_list<T> &images, int position,
                                    PyGmicImage *image)
{
    // Put back the possibly modified reallocated image buffer into the
    // original external GmicImage Back up the image data into the original
    // external image before it gets freed
    swap(image->_gmic_image._data, images[position]._data);
    image->_gmic_image._width = images[position]._width;
    image->_gmic_image._height = images[position]._height;
    image->_gmic_image._depth = images[position]._depth;
    image->_gmic_image._spectrum = images[position]._spectrum;
    image->_gmic_image._is_shared = images[position]._is_shared;
    // Prevent freeing the data buffer's pointer now copied into the external
    // image
    images[position]._data = 0;
}

static PyObject *
run_impl(PyObject *self, PyObject *args, PyObject *kwargs)
{
    char const *keywords[] = {"command", "images", "image_names", NULL};
    PyObject *input_gmic_images = NULL;
    PyObject *input_gmic_image_names = NULL;
    char *commands_line = NULL;
    int image_position;
    int image_name_position;
    int image_names_count;
    gmic_list<T> images;
    gmic_list<char> image_names;  // Empty image names
    char *current_image_name_raw;
    PyObject *current_image = NULL;
    PyObject *current_image_name = NULL;
    PyObject *iter = NULL;
    bool must_return_all_items_as_numpy_array = false;
    PyObject *any_numpy_object = NULL;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "s|OO", (char **)keywords,
                                     &commands_line, &input_gmic_images,
                                     &input_gmic_image_names)) {
        return NULL;
    }

    try {
        Py_XINCREF(input_gmic_images);
        Py_XINCREF(input_gmic_image_names);

        // Grab image names or single image name and check typings
        if (input_gmic_image_names != NULL) {
            // If list of image names provided
            if (PyList_Check(input_gmic_image_names)) {
                PyObject *iter = PyObject_GetIter(input_gmic_image_names);
                image_names_count = Py_SIZE(input_gmic_image_names);
                image_names.assign(image_names_count);
                image_name_position = 0;

                while ((current_image_name = PyIter_Next(iter))) {
                    if (!PyUnicode_Check(current_image_name)) {
                        PyErr_Format(
                            PyExc_TypeError,
                            "'%.50s' input element found at position %d in "
                            "'image_names' list is not a '%.400s'",
                            Py_TYPE(current_image_name)->tp_name,
                            image_name_position, PyUnicode_Type.tp_name);
                        Py_XDECREF(input_gmic_images);
                        Py_XDECREF(input_gmic_image_names);

                        return NULL;
                    }

                    current_image_name_raw =
                        (char *)PyUnicode_AsUTF8(current_image_name);
                    image_names[image_name_position].assign(
                        strlen(current_image_name_raw) + 1);
                    memcpy(image_names[image_name_position]._data,
                           current_image_name_raw,
                           image_names[image_name_position]._width);
                    image_name_position++;
                }

                // If single image name provided
            }
            else if (PyUnicode_Check(input_gmic_image_names)) {
                // Enforce also non-null single-GmicImage 'images' parameter
                if (input_gmic_images != NULL &&
                    Py_TYPE(input_gmic_images) !=
                        (PyTypeObject *)&PyGmicImageType) {
                    PyErr_Format(
                        PyExc_TypeError,
                        "'%.50s' 'images' parameter must be a '%.400s' if the "
                        "'image_names' parameter is a bare '%.400s'.",
                        Py_TYPE(input_gmic_images)->tp_name,
                        PyGmicImageType.tp_name, PyUnicode_Type.tp_name);
                    Py_XDECREF(input_gmic_images);
                    Py_XDECREF(input_gmic_image_names);

                    return NULL;
                }

                image_names.assign(1);
                current_image_name_raw =
                    (char *)PyUnicode_AsUTF8(input_gmic_image_names);
                image_names[0].assign(strlen(current_image_name_raw) + 1);
                memcpy(image_names[0]._data, current_image_name_raw,
                       image_names[0]._width);
                // If neither a list of strings nor a single string were
                // provided, raise exception
            }
            else {
                PyErr_Format(PyExc_TypeError,
                             "'%.50s' 'image_names' parameter must be a list "
                             "of '%.400s'(s)",
                             Py_TYPE(input_gmic_image_names)->tp_name,
                             PyUnicode_Type.tp_name);
                Py_XDECREF(input_gmic_images);
                Py_XDECREF(input_gmic_image_names);

                return NULL;
            }
        }

        if (input_gmic_images != NULL) {
            // A/ If a list of images was provided
            if (PyList_Check(input_gmic_images)) {
                image_position = 0;
                images.assign(Py_SIZE(input_gmic_images));

                // Grab images into a proper gmic_list after checking their
                // typing
                iter = PyObject_GetIter(input_gmic_images);
                while ((current_image = PyIter_Next(iter))) {
                    // If gmic_list item type is not a GmicImage
                    if (Py_TYPE(current_image) !=
                        (PyTypeObject *)&PyGmicImageType) {
                        // If current image type is a numpy.ndarray
                        if (PyNumpyArray_Check(current_image)) {
                            // convert it to a GmicImage transparently
                            current_image =
                                PyNumpyArray_AS_PYGMICIMAGE(current_image);
                            any_numpy_object = current_image;
                            must_return_all_items_as_numpy_array = true;
                            // Else if type is completely unknown, raise
                            // exception
                        }
                        else {
                            PyErr_Format(
                                PyExc_TypeError,
                                "'%.50s' input object found at position %d in "
                                "'images' list is not a '%.400s'",
                                Py_TYPE(current_image)->tp_name,
                                image_position, PyGmicImageType.tp_name);

                            Py_XDECREF(input_gmic_images);
                            Py_XDECREF(input_gmic_image_names);

                            return NULL;
                        }
                    }
                    // Fill our just created gmic_list at same index with
                    // gmic_image coming from Python or just converted from
                    // numpy type
                    swap_gmic_image_into_gmic_list(
                        (PyGmicImage *)current_image, images, image_position);

                    image_position++;
                }

                // Process images and names
                ((PyGmic *)self)
                    ->_gmic->run(commands_line, images, image_names, 0, 0);

                // Prevent images auto-deallocation by G'MIC
                image_position = 0;

                // Bring new images set back into the Python world (change List
                // items in-place) First empty the input Python images List
                // object from its items without deleting it (empty list, same
                // reference)
                PySequence_DelSlice(input_gmic_images, 0,
                                    PySequence_Length(input_gmic_images));

                cimglist_for(images, l)
                {
                    // On the fly python GmicImage build (or numpy.ndarray
                    // build if there was an ndarray in the input list) per
                    // https://stackoverflow.com/questions/4163018/create-an-object-using-pythons-c-api/4163055#comment85217110_4163055
                    PyObject *_data = PyBytes_FromStringAndSize(
                        (const char *)images[l]._data,
                        (Py_ssize_t)sizeof(T) * images[l].size());
                    PyObject *new_gmic_image = NULL;
                    if (must_return_all_items_as_numpy_array) {
                        // TODO build shape tuple according to real dimensions
                        new_gmic_image = PyGmicImage_AS_NUMPYARRAY(
                            Py_BuildValue("(00)", 2, 1), &PyFloat_Type, _data,
                            any_numpy_object);
                    }
                    else {
                        new_gmic_image = PyObject_CallFunction(
                            (PyObject *)&PyGmicImageType,
                            // The last argument is a p(redicate), ie.
                            // boolean..
                            // but Py_BuildValue() used by
                            // PyObject_CallFunction has a slightly different
                            // parameters format specification
                            (const char *)"SIIIIi", _data,
                            (unsigned int)images[l]._width,
                            (unsigned int)images[l]._height,
                            (unsigned int)images[l]._depth,
                            (unsigned int)images[l]._spectrum,
                            (int)images[l]._is_shared);
                        if (new_gmic_image == NULL) {
                            PyErr_Format(
                                PyExc_RuntimeError,
                                "Could not initialize GmicImage for appending "
                                "it to provided 'images' parameter list.");
                            return NULL;
                        }
                    }
                    PyList_Append(input_gmic_images, new_gmic_image);
                }

                // B/ Else if a single GmicImage was provided
            }
            else if (Py_TYPE(input_gmic_images) ==
                     (PyTypeObject *)&PyGmicImageType) {
                images.assign(1);
                swap_gmic_image_into_gmic_list(
                    (PyGmicImage *)input_gmic_images, images, 0);

                // Pipe the commands, our single image, and no image names
                ((PyGmic *)self)
                    ->_gmic->run(commands_line, images, image_names, 0, 0);

                // Alter the original image only if the gmic_image list has not
                // been downsized to 0 elements this may happen with eg. a
                // rm[0] G'MIC command We must prevent this, because a 'core
                // dumped' happens otherwise
                if (images.size() > 0) {
                    swap_gmic_list_item_into_gmic_image(
                        images, 0, (PyGmicImage *)input_gmic_images);
                }
                else {
                    PyErr_Format(PyExc_RuntimeError,
                                 "'%.50s' 'images' single-element parameter "
                                 "was removed by your G\'MIC command. It was "
                                 "probably emptied, your optional "
                                 "'image_names' list is untouched.",
                                 Py_TYPE(input_gmic_images)->tp_name,
                                 PyGmicImageType.tp_name,
                                 PyGmicImageType.tp_name);
                    Py_XDECREF(input_gmic_images);
                    Py_XDECREF(input_gmic_image_names);

                    return NULL;
                }
            }
            // Else if provided 'images' type is unknown (or is a single
            // numpy.ndarray, which unfortunately cannot be updated in place),
            // raise Error
            else {
                PyErr_Format(
                    PyExc_TypeError,
                    "'%.50s' 'images' parameter must be a '%.400s', or list "
                    "of either '%.400s'(s) or 'numpy.ndarray'(s)",
                    Py_TYPE(input_gmic_images)->tp_name,
                    PyGmicImageType.tp_name, PyGmicImageType.tp_name);
                Py_XDECREF(input_gmic_images);
                Py_XDECREF(input_gmic_image_names);

                return NULL;
            }

            // If a correctly-typed image names parameter was provided, even if
            // wrongly typed, let us update its Python object in place, to
            // mirror any kind of changes that may have taken place in the
            // gmic_list of image names
            if (input_gmic_image_names != NULL) {
                // i) If a list parameter was provided
                if (PyList_Check(input_gmic_image_names)) {
                    // First empty the input Python image names list
                    PySequence_DelSlice(
                        input_gmic_image_names, 0,
                        PySequence_Length(input_gmic_image_names));
                    // Add image names from the Gmic List of names
                    cimglist_for(image_names, l)
                    {
                        PyList_Append(input_gmic_image_names,
                                      PyUnicode_FromString(image_names[l]));
                    }
                }
                // ii) If a str parameter was provided
                // Because of Python's string immutability, we will not change
                // the input string's content here :) :/
            }
        }
        else {
            T pixel_type;
            ((PyGmic *)self)
                ->_gmic->run((const char *const)commands_line,
                             (float *const)NULL, (bool *const)NULL,
                             (const T &)pixel_type);
        }

        Py_XDECREF(input_gmic_images);
        Py_XDECREF(input_gmic_image_names);
    }
    catch (gmic_exception &e) {
        PyErr_SetString(GmicException, e.what());
        return NULL;
    }
    catch (std::exception &e) {
        PyErr_SetString(GmicException, e.what());
        return NULL;
    }
    Py_RETURN_NONE;
}

/** Instancing of any c++ gmic::gmic G'MIC language interpreter object (Python:
 * gmic.Gmic) **/
static int
PyGmic_init(PyGmic *self, PyObject *args, PyObject *kwargs)
{
    int result = 0;
    self->_gmic = new gmic();

    // Init resources folder.
    if (!gmic::init_rc()) {
        PyErr_Format(GmicException,
                     "Unable to create G'MIC resources folder.");
    }

    // Load general and user scripts if they exist
    // Since this project is a library the G'MIC "update" command that runs an
    // internet download, is never triggered the user should run it
    // him/herself.
    self->_gmic->run("m $_path_rc/update$_version.gmic");
    self->_gmic->run("m $_path_user");

    // If parameters are provided, pipe them to our run() method, and do only
    // exceptions raising without returning anything if things go well
    if (args != Py_None && ((args && (int)PyTuple_Size(args) > 0) ||
                            (kwargs && (int)PyDict_Size(kwargs) > 0))) {
        result = (run_impl((PyObject *)self, args, kwargs) != NULL) ? 0 : -1;
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
    {"run", (PyCFunction)run_impl, METH_VARARGS | METH_KEYWORDS, run_impl_doc},
    {NULL} /* Sentinel */
};

// ------------ G'MIC IMAGE BINDING ----//

static int
PyGmicImage_init(PyGmicImage *self, PyObject *args, PyObject *kwargs)
{
    unsigned int _width =
        1;  // Number of image columns (dimension along the X-axis)
    unsigned int _height =
        1;  // Number of image lines (dimension along the Y-axis)
    unsigned int _depth =
        1;  // Number of image slices (dimension along the Z-axis)
    unsigned int _spectrum =
        1;  // Number of image channels (dimension along the C-axis)
    Py_ssize_t
        dimensions_product;  // All integer parameters multiplied together,
                             // will help for allocating (ie. assign()ing)
    Py_ssize_t _data_bytes_size;
    int _is_shared =
        0;  // Whether image should be shared across gmic operations (if true,
            // operations like resize will fail)
    PyObject *bytesObj = NULL;  // Incoming bytes buffer object pointer
    bool bytesObj_is_ndarray = false;
    bool bytesObj_is_bytes = false;
    PyObject *bytesObj_ndarray_dtype;
    PyObject *bytesObj_ndarray_shape;
    Py_ssize_t bytesObj_ndarray_shape_size;
    PyObject *bytesObj_ndarray_dtype_kind;
    char *bytesObj_ndarray_dtype_name_str;
    char const *keywords[] = {"data",     "width",  "height", "depth",
                              "spectrum", "shared", NULL};

    // Parameters parsing and checking
    if (!PyArg_ParseTupleAndKeywords(
            args, kwargs, "|OIIIIp", (char **)keywords, &bytesObj, &_width,
            &_height, &_depth, &_spectrum, &_is_shared))
        return -1;

    if (bytesObj != NULL) {
        bytesObj_is_bytes = (bool)PyBytes_Check(bytesObj);
        bytesObj_is_ndarray = PyNumpyArray_Check(bytesObj);
        if (!bytesObj_is_ndarray && !bytesObj_is_bytes) {
            PyErr_Format(PyExc_TypeError,
                         "Parameter 'data' must be a 'numpy.ndarray' or a "
                         "pure-python 'bytes' buffer object.");
            // TODO pytest this
            return -1;
        }
    }
    else {  // if bytesObj is NULL
        if (_width == 1 && _height == 1 && _depth == 1 && _spectrum == 1) {
            PyErr_Format(PyExc_TypeError,
                         "If you do not provide a 'data' parameter, make at "
                         "least one of the dimensions >1.");
            // TODO pytest this
            return -1;
        }
    }

    // Importing numpy.ndarray shape and import buffer after deinterlacing it
    // We are skipping any need for a C API include of numpy, to use either
    // python-language level API or common-python structure access
    if (bytesObj_is_ndarray) {
        // Get ndarray.dtype
        bytesObj_ndarray_dtype = PyObject_GetAttrString(bytesObj, "dtype");
        // Ensure dtype kind is a number we can convert (from dtype values
        // here:
        // https://numpy.org/doc/1.18/reference/generated/numpy.dtype.kind.html#numpy.dtype.kind)
        bytesObj_ndarray_dtype_kind =
            PyObject_GetAttrString(bytesObj_ndarray_dtype, "kind");
        if (strchr("biuf", (PyUnicode_ReadChar(bytesObj_ndarray_dtype_kind,
                                               (Py_ssize_t)0))) == NULL) {
            PyErr_Format(PyExc_TypeError,
                         "Parameter 'data' of type 'numpy.ndarray' does not "
                         "contain numbers ie. its 'dtype.kind'(=%U) is not "
                         "one of 'b', 'i', 'u', 'f'.",
                         bytesObj_ndarray_dtype_kind);
            // TODO pytest this
            return -1;
        }

        bytesObj_ndarray_shape = PyObject_GetAttrString(bytesObj, "shape");
        bytesObj_ndarray_shape_size = PyTuple_GET_SIZE(bytesObj_ndarray_shape);
        switch (bytesObj_ndarray_shape_size) {
            // TODO maybe skip other images than 2D or 3D
            case 1:
                PyErr_Format(
                    PyExc_TypeError,
                    "Parameter 'data' of type 'numpy.ndarray' is 1D with "
                    "single-channel, this is not supported yet.");
                return -1;
                //_width = (unsigned int)
                // PyLong_AsSize_t(PyTuple_GetItem(bytesObj_ndarray_shape_size,
                // 0));
            case 2:
                PyErr_Format(
                    PyExc_TypeError,
                    "Parameter 'data' of type 'numpy.ndarray' is 1D with "
                    "multiple channels, this is not supported yet.");
                return -1;
                // TODO set _width, height
            case 3:
                _width = (unsigned int)PyLong_AsSize_t(
                    PyTuple_GetItem(bytesObj_ndarray_shape, 0));
                _height = (unsigned int)PyLong_AsSize_t(
                    PyTuple_GetItem(bytesObj_ndarray_shape, 1));
                _depth = 1;
                _spectrum = (unsigned int)PyLong_AsSize_t(
                    PyTuple_GetItem(bytesObj_ndarray_shape, 2));
                break;
            case 4:
                _width = (unsigned int)PyLong_AsSize_t(
                    PyTuple_GetItem(bytesObj_ndarray_shape, 0));
                _height = (unsigned int)PyLong_AsSize_t(
                    PyTuple_GetItem(bytesObj_ndarray_shape, 1));
                _depth = (unsigned int)PyLong_AsSize_t(
                    PyTuple_GetItem(bytesObj_ndarray_shape, 2));
                _spectrum = (unsigned int)PyLong_AsSize_t(
                    PyTuple_GetItem(bytesObj_ndarray_shape, 3));
                break;
            default:
                if (bytesObj_ndarray_shape_size < 1) {
                    PyErr_Format(
                        PyExc_TypeError,
                        "Parameter 'data' of type 'numpy.ndarray' has an "
                        "empty shape. This is not supported by this binding.");
                }
                else {  // case >4
                    PyErr_Format(PyExc_TypeError,
                                 "Parameter 'data' of type 'numpy.ndarray' "
                                 "has a shape larger than 3D x 1-256 "
                                 "channels. This is not supported by G'MIC.");
                }
                return -1;
        }

        bytesObj_ndarray_dtype_name_str =
            (char *)PyUnicode_AsUTF8(PyObject_GetAttrString(
                bytesObj_ndarray_dtype, (const char *)"name"));
        // See also Pillow Image modes:
        // https://pillow.readthedocs.io/en/3.1.x/handbook/concepts.html#concept-modes
        // TODO float64,float64 uint16, uint32, float32, float16, float8
        // We are doing string comparison here instead of introspecting the
        // dtype.kind.num which is expected to be a unique identifier of type
        // Slightly simpler to read.. slightly slower to run
        if (strcmp(bytesObj_ndarray_dtype_name_str, "uint8") == 0) {
        }
        else {
            PyErr_Format(PyExc_TypeError,
                         "Parameter 'data' of type 'numpy.ndarray' has an "
                         "understandable shape for us, but its data type '%s' "
                         "is not supported yet(?).",
                         bytesObj_ndarray_dtype_name_str);
            return -1;
        }
    }

    // Bytes object spatial dimensions vs. bytes-length checking
    if (bytesObj_is_bytes) {
        dimensions_product = _width * _height * _depth * _spectrum;
        _data_bytes_size = PyBytes_Size(bytesObj);
        if ((Py_ssize_t)(dimensions_product * sizeof(T)) != _data_bytes_size) {
            PyErr_Format(PyExc_ValueError,
                         "GmicImage dimensions-induced buffer bytes size "
                         "(%d*%dB=%d) cannot be strictly negative or "
                         "different than the _data buffer size in bytes (%d)",
                         dimensions_product, sizeof(T),
                         dimensions_product * sizeof(T), _data_bytes_size);
            return -1;
        }
    }

    // Importing input data to an internal buffer
    try {
        self->_gmic_image.assign(_width, _height, _depth, _spectrum);
    }
    // Ugly exception catching, probably to catch a
    // cimg::GmicInstanceException()
    catch (...) {
        dimensions_product = _width * _height * _depth * _spectrum;
        PyErr_Format(
            PyExc_MemoryError,
            "Allocation error in "
            "GmicImage::assign(_width=%d,_height=%d,_depth=%d,_spectrum=%d), "
            "are you requesting too much memory (%d bytes)?",
            _width, _height, _depth, _spectrum,
            dimensions_product * sizeof(T));
        return -1;
    }

    self->_gmic_image._is_shared = _is_shared;

    if (bytesObj_is_bytes) {
        memcpy(self->_gmic_image._data, PyBytes_AsString(bytesObj),
               PyBytes_Size(bytesObj));
    }
    else {  // if bytesObj is numpy
        PyObject *bytesObjNumpyBytes =
            PyObject_CallMethod(bytesObj, "tobytes", NULL);
        unsigned char *ptr =
            (unsigned char *)PyBytes_AsString(bytesObjNumpyBytes);
        for (unsigned int y = 0; y < _height; y++) {
            for (unsigned int x = 0; x < _width; x++) {
                unsigned char R = *(ptr++);
                unsigned char G = *(ptr++);
                unsigned char B = *(ptr++);
                self->_gmic_image(x, y, 0, 0) = (float)R;
                self->_gmic_image(x, y, 0, 1) = (float)G;
                self->_gmic_image(x, y, 0, 2) = (float)B;
            }
        }
    }

    return 0;
}

static PyObject *
PyGmicImage_repr(PyGmicImage *self)
{
    return PyUnicode_FromFormat(
        "<%s object at %p with _data address at %p, w=%d h=%d d=%d s=%d "
        "shared=%d>",
        Py_TYPE(self)->tp_name, self, self->_gmic_image._data,
        self->_gmic_image._width, self->_gmic_image._height,
        self->_gmic_image._depth, self->_gmic_image._spectrum,
        self->_gmic_image._is_shared);
}

static PyObject *
PyGmicImage_call(PyObject *self, PyObject *args, PyObject *kwargs)
{
    const char *keywords[] = {"x", "y", "z", "c", NULL};
    int x, y, z, c;
    x = y = z = c = 0;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "i|iii", (char **)keywords,
                                     &x, &y, &z, &c)) {
        return NULL;
    }

    return PyFloat_FromDouble(((PyGmicImage *)self)->_gmic_image(x, y, z, c));
}

static void
PyGmicImage_dealloc(PyGmicImage *self)
{
    Py_TYPE(self)->tp_free(self);
}

static PyObject *
module_level_run_impl(PyObject *, PyObject *args, PyObject *kwargs)
{
    PyObject *temp_gmic_instance =
        PyObject_CallObject((PyObject *)(&PyGmicType), NULL);
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
    {"run", (PyCFunction)module_level_run_impl, METH_VARARGS | METH_KEYWORDS,
     module_level_run_impl_doc},
    {nullptr, nullptr, 0, nullptr}};

PyDoc_STRVAR(gmic_module_doc,
             "G'MIC Image Processing library Python binding\n\n\
Use gmic.run(...), gmic.GmicImage(...), gmic.Gmic(...).\n\
Make sure to visit https://github.com/myselfhimself/gmic-py for examples and documentation.");

PyModuleDef gmic_module = {PyModuleDef_HEAD_INIT, "gmic", gmic_module_doc, 0,
                           gmic_methods};

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
i._width == i._height == 2 # Use the _width, _height, _depth, _spectrum, _data, _data_str, _is_shared read-only attributes");
// TODO add gmic.Gmic example

static PyMemberDef PyGmicImage_members[] = {
    {(char *)"_width", T_UINT, offsetof(PyGmicImage, _gmic_image), READONLY,
     (char *)"width"},
    {(char *)"_height", T_UINT,
     offsetof(PyGmicImage, _gmic_image) + sizeof(unsigned int), READONLY,
     (char *)"height"},
    {(char *)"_depth", T_UINT,
     offsetof(PyGmicImage, _gmic_image) + 2 * sizeof(unsigned int), READONLY,
     (char *)"depth"},
    {(char *)"_spectrum", T_UINT,
     offsetof(PyGmicImage, _gmic_image) + 3 * sizeof(unsigned int), READONLY,
     (char *)"spectrum"},
    {(char *)"_is_shared", T_BOOL,
     offsetof(PyGmicImage, _gmic_image) + 4 * sizeof(unsigned int), READONLY,
     (char *)"_is_shared"},
    {NULL} /* Sentinel */
};

static PyObject *
PyGmicImage_get__data(PyGmicImage *self, void *closure)
{
    return PyBytes_FromStringAndSize((char *)self->_gmic_image._data,
                                     sizeof(T) * (self->_gmic_image.size()));
}

static PyObject *
PyGmicImage_get__data_str(PyGmicImage *self, void *closure)
{
    unsigned int image_size = self->_gmic_image.size();
    PyObject *unicode_json = PyUnicode_New((Py_ssize_t)image_size, 65535);

    for (unsigned int a = 0; a < image_size; a++) {
        PyUnicode_WriteChar(unicode_json, (Py_ssize_t)a,
                            (Py_UCS4)self->_gmic_image._data[a]);
    }

    return unicode_json;
}

PyGetSetDef PyGmicImage_getsets[] = {{(char *)"_data", /* name */
                                      (getter)PyGmicImage_get__data,
                                      NULL,  // no setter
                                      NULL,  /* doc */
                                      NULL /* closure */},
                                     {(char *)"_data_str", /* name */
                                      (getter)PyGmicImage_get__data_str,
                                      NULL,  // no setter
                                      NULL,  /* doc */
                                      NULL /* closure */},
                                     {NULL}};

/**
 * Predictable Python 3.x 'numpy' module importer.
 */
PyObject *
import_numpy_module()
{
    PyObject *numpy_module = PyImport_ImportModule("numpy");

    // exit raising numpy_module import exception
    if (!numpy_module) {
        // Do not raise a Python >= 3.6 ModuleImportError, but something more
        // compatible with any Python 3.x
        PyErr_Clear();
        return PyErr_Format(PyExc_ImportError,
                            "The 'numpy' module cannot be imported. Is it "
                            "installed or in your Python path?");
    }

    return numpy_module;
}

/*
 * GmicImage class method from_numpy_array().
 * This is a factory class method generating a G'MIC Image from a
 * numpy.ndarray.
 *
 *  GmicImage.from_numpy_array(obj: numpy.ndarray, deinterleave=True: bool) ->
 * GmicImage()
 */
static PyObject *
PyGmicImage_from_numpy_array(PyObject *cls, PyObject *args, PyObject *kwargs)
{
    int arg_deinterleave =
        1;  // Will deinterleave the incoming numpy.ndarray by default
    PyObject *arg_ndarray = NULL;
    PyObject *ndarray_type = NULL;
    PyObject *ndarray_dtype = NULL;
    PyObject *ndarray_dtype_kind = NULL;
    PyObject *ndarray_as_3d_unsqueezed_view = NULL;
    PyObject *ndarray_shape_tuple = NULL;
    PyObject *ndarray_as_3d_unsqueezed_view_expanded_dims = NULL;
    unsigned int _width = 1, _height = 1, _depth = 1, _spectrum = 1;
    PyObject *numpy_module = NULL;
    PyObject *new_gmic_image = NULL;
    PyObject *_data_bytesObj = NULL;
    char const *keywords[] = {"numpy_array", "deinterleave", NULL};

    numpy_module = PyImport_ImportModule("numpy");
    if (!numpy_module)
        return NULL;

    ndarray_type = PyObject_GetAttrString(numpy_module, "ndarray");

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O!|p", (char **)keywords,
                                     &arg_ndarray, &ndarray_type,
                                     &arg_deinterleave))
        return NULL;

    // Get input ndarray.dtype and prevent non-integer/float/bool data types to
    // be processed
    ndarray_dtype = PyObject_GetAttrString(arg_ndarray, "dtype");
    // Ensure dtype kind is a number we can convert (from dtype values here:
    // https://numpy.org/doc/1.18/reference/generated/numpy.dtype.kind.html#numpy.dtype.kind)
    ndarray_dtype_kind = PyObject_GetAttrString(ndarray_dtype, "kind");
    if (strchr("biuf", (PyUnicode_ReadChar(ndarray_dtype_kind,
                                           (Py_ssize_t)0))) == NULL) {
        PyErr_Format(PyExc_TypeError,
                     "Parameter 'data' of type 'numpy.ndarray' does not "
                     "contain numbers ie. its 'dtype.kind'(=%U) is not one of "
                     "'b', 'i', 'u', 'f'.",
                     ndarray_dtype_kind);
        // TODO pytest this
        return NULL;
    }

    // Get unsqueezed shape of numpy array -> GmicImage width, height, depth,
    // spectrum Getting a shape with the most axes from array:
    // https://docs.scipy.org/doc/numpy-1.17.0/reference/generated/numpy.atleast_3d.html#numpy.atleast_3d
    // Adding a depth axis using numpy.expand_dims:
    // https://docs.scipy.org/doc/numpy-1.17.0/reference/generated/numpy.expand_dims.html
    // (numpy tends to squeeze dimensions when calling the standard
    // array().shape, we circuvent this)
    ndarray_as_3d_unsqueezed_view =
        PyObject_CallMethod(numpy_module, "atleast_3d", NULL);
    ndarray_as_3d_unsqueezed_view_expanded_dims = PyObject_CallMethod(
        numpy_module, "expand_dims", "OI", ndarray_as_3d_unsqueezed_view,
        2);  // Adding z axis if absent
    ndarray_shape_tuple = PyObject_GetAttrString(
        ndarray_as_3d_unsqueezed_view_expanded_dims, "shape");
    _width =
        (unsigned int)PyLong_AsSize_t(PyTuple_GetItem(ndarray_shape_tuple, 0));
    _height =
        (unsigned int)PyLong_AsSize_t(PyTuple_GetItem(ndarray_shape_tuple, 1));
    _depth =
        (unsigned int)PyLong_AsSize_t(PyTuple_GetItem(ndarray_shape_tuple, 2));
    _spectrum =
        (unsigned int)PyLong_AsSize_t(PyTuple_GetItem(ndarray_shape_tuple, 3));

    new_gmic_image = PyObject_CallFunction(
        (PyObject *)&PyGmicImageType, (const char *)"SIIII",
        NULL,  // tentative passing of a empty _data
        _width, _height, _depth, _spectrum);

    // TODO if deinterleave needed, copy deinterleaved to a _data buffer with
    // type casting, else just copy with type casting

    _data_bytesObj = PyObject_CallMethod(arg_ndarray, "tobytes", NULL);
    unsigned char *ptr = (unsigned char *)PyBytes_AsString(_data_bytesObj);

    // TODO adapt input buffer step to incoming type if
    // (strcmp(bytesObj_ndarray_dtype_name_str, "uint8") == 0) {
    if (!arg_deinterleave) {
        for (unsigned int x = 0; x < _width; x++) {
            for (unsigned int y = 0; y < _height; y++) {
                for (unsigned int z = 0; z < _depth; z++) {
                    for (unsigned int c = 0; c < _spectrum; c++) {
                        // if (strcmp(bytesObj_ndarray_dtype_name_str, "uint8")
                        // == 0) { //TODO ptr step should be uint8 size
                        ((PyGmicImage *)new_gmic_image)
                            ->_gmic_image(x, y, z, c) =
                            (T) * ((uint8_t *)ptr++);
                    }
                }
            }
        }
    }
    else {
        // TODO adapt input buffer step to incoming type if
        // (strcmp(bytesObj_ndarray_dtype_name_str, "uint8") == 0) {
        for (unsigned int c = 0; c < _spectrum; c++) {
            for (unsigned int z = 0; z < _depth; z++) {
                for (unsigned int y = 0; y < _height; y++) {
                    for (unsigned int x = 0; x < _width; x++) {
                        ((PyGmicImage *)new_gmic_image)
                            ->_gmic_image(x, y, z, c) = (T) * (ptr++);
                    }
                }
            }
        }
    }

    Py_DECREF(arg_ndarray);
    Py_DECREF(ndarray_dtype);
    Py_DECREF(ndarray_dtype_kind);
    Py_DECREF(ndarray_as_3d_unsqueezed_view);
    Py_DECREF(ndarray_as_3d_unsqueezed_view_expanded_dims);
    Py_DECREF(ndarray_shape_tuple);
    Py_DECREF(_data_bytesObj);
    Py_DECREF(ndarray_type);
    Py_DECREF(numpy_module);

    return new_gmic_image;
}

/*
 * GmicImage object method to_numpy_array().
 *
 * GmicImage().to_numpy_array(astype=numpy.float32: numpy.dtype,
 * interleave=True: bool) -> numpy.ndarray
 *
 * TODO monitor this more closely, there seems to be a memory leak...
 */
static PyObject *
PyGmicImage_to_numpy_array(PyGmicImage *self, PyObject *args, PyObject *kwargs)
{
    char const *keywords[] = {"astype", "interleave", NULL};
    PyObject *numpy_module = NULL;
    PyObject *ndarray_type = NULL;
    PyObject *return_ndarray = NULL;
    PyObject *return_ndarray_astype = NULL;
    PyObject *_shape = NULL;
    PyObject *shape = NULL;
    PyObject *dtype = NULL;
    PyObject *numpy_bytes_buffer = NULL;
    float *numpy_buffer = NULL;
    float *ptr;
    int buffer_size = 0;
    PyObject *arg_astype = NULL;
    int arg_interleave = 1;  // Will interleave the final matrix by default

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|Op", (char **)keywords,
                                     &arg_astype, &arg_interleave)) {
        return NULL;
    }

    numpy_module = PyImport_ImportModule("numpy");
    if (!numpy_module)
        return NULL;

    ndarray_type = PyObject_GetAttrString(numpy_module, "ndarray");

    // Create shape by squeezing 1-dimension dimensions from it first
    _shape = PyList_New(0);
    if (self->_gmic_image._width > 1) {
        PyList_Append(_shape,
                      PyLong_FromSize_t((size_t)self->_gmic_image._width));
    }
    if (self->_gmic_image._height > 1) {
        PyList_Append(_shape,
                      PyLong_FromSize_t((size_t)self->_gmic_image._height));
    }
    if (self->_gmic_image._depth > 1) {
        PyList_Append(_shape,
                      PyLong_FromSize_t((size_t)self->_gmic_image._depth));
    }
    if (self->_gmic_image._spectrum > 1) {
        PyList_Append(_shape,
                      PyLong_FromSize_t((size_t)self->_gmic_image._spectrum));
    }
    shape = PyList_AsTuple(_shape);
    dtype = PyObject_GetAttrString(numpy_module, "float32");
    buffer_size = sizeof(T) * self->_gmic_image.size();
    numpy_buffer = (float *)malloc(buffer_size);
    ptr = numpy_buffer;
    // If interlacing is needed, copy the gmic_image buffer towards numpy by
    // interlacing RRR,GGG,BBB into RGB,RGB,RGB
    if (arg_interleave) {
        for (unsigned int z = 0; z < self->_gmic_image._depth; z++) {
            for (unsigned int y = 0; y < self->_gmic_image._height; y++) {
                for (unsigned int x = 0; x < self->_gmic_image._width; x++) {
                    for (unsigned int c = 0; c < 3; c++) {
                        (*ptr++) = self->_gmic_image(x, y, z, c);
                    }
                }
            }
        }
    }
    else {
        // If deinterlacing is needed, since this is G'MIC's internal image
        // shape, keep pixel data order as and copy it simply
        memcpy(numpy_buffer, self->_gmic_image._data,
               self->_gmic_image.size() * sizeof(T));
    }
    numpy_bytes_buffer =
        PyBytes_FromStringAndSize((const char *)numpy_buffer, buffer_size);
    free(numpy_buffer);
    // class numpy.ndarray(shape, dtype=float, buffer=None, offset=0,
    // strides=None, order=None)
    return_ndarray = PyObject_CallFunction(ndarray_type, (const char *)"OOS",
                                           shape, dtype, numpy_bytes_buffer);

    Py_DECREF(ndarray_type);
    Py_DECREF(shape);
    Py_DECREF(_shape);
    Py_DECREF(dtype);
    Py_DECREF(numpy_bytes_buffer);
    Py_DECREF(numpy_module);

    if (arg_astype != NULL && PyType_Check(arg_astype)) {
        return_ndarray_astype =
            PyObject_CallMethod(return_ndarray, "astype", "O", arg_astype);
        Py_DECREF(return_ndarray);
        return return_ndarray_astype;
    }
    else {
        return return_ndarray;
    }
}

static PyMethodDef PyGmicImage_methods[] = {
    {"from_numpy_array", (PyCFunction)PyGmicImage_from_numpy_array,
     METH_CLASS | METH_VARARGS | METH_KEYWORDS,
     "Make a GmicImage from a numpy.ndarray"},
    {"to_numpy_array", (PyCFunction)PyGmicImage_to_numpy_array,
     METH_VARARGS | METH_KEYWORDS, "Make a numpy.ndarray from a GmicImage"},
    {NULL} /* Sentinel */
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
                result = ((PyGmicImage *)self)->_gmic_image ==
                                 ((PyGmicImage *)other)->_gmic_image
                             ? Py_True
                             : Py_False;
                break;
            case Py_NE:
                // Leverage the CImg != C++ operator
                result = ((PyGmicImage *)self)->_gmic_image !=
                                 ((PyGmicImage *)other)->_gmic_image
                             ? Py_True
                             : Py_False;
                break;
        }
    }

    Py_XINCREF(result);
    return result;
}

PyMODINIT_FUNC
PyInit_gmic()
{
    PyObject *m;

    // The GmicException inherits Python's builtin Exception.
    // Used for non-precise errors raised from this module.
    GmicException = PyErr_NewExceptionWithDoc(
        "gmic.GmicException",                       /* char *name */
        "Base exception class of the Gmic module.", /* char *doc */
        NULL,                                       /* PyObject *base */
        NULL /* PyObject *dict */);

    PyGmicImageType.tp_new = PyType_GenericNew;
    PyGmicImageType.tp_basicsize = sizeof(PyGmicImage);
    PyGmicImageType.tp_dealloc = (destructor)PyGmicImage_dealloc;
    PyGmicImageType.tp_methods = PyGmicImage_methods;
    PyGmicImageType.tp_repr = (reprfunc)PyGmicImage_repr;
    PyGmicImageType.tp_init = (initproc)PyGmicImage_init;
    PyGmicImageType.tp_call = (ternaryfunc)PyGmicImage_call;
    PyGmicImageType.tp_getattro = PyObject_GenericGetAttr;
    PyGmicImageType.tp_doc = PyGmicImage_doc;
    PyGmicImageType.tp_members = PyGmicImage_members;
    PyGmicImageType.tp_getset = PyGmicImage_getsets;
    PyGmicImageType.tp_richcompare = PyGmicImage_richcompare;

    if (PyType_Ready(&PyGmicImageType) < 0)
        return NULL;

    PyGmicType.tp_new = PyType_GenericNew;
    PyGmicType.tp_basicsize = sizeof(PyGmic);
    PyGmicType.tp_methods = PyGmic_methods;
    PyGmicType.tp_repr = (reprfunc)PyGmic_repr;
    PyGmicType.tp_init = (initproc)PyGmic_init;
    PyGmicType.tp_getattro = PyObject_GenericGetAttr;
    // PyGmicType.tp_doc=PyGmicImage_doc;

    if (PyType_Ready(&PyGmicType) < 0)
        return NULL;

    m = PyModule_Create(&gmic_module);
    if (m == NULL)
        return NULL;

    Py_INCREF(&PyGmicImageType);
    Py_INCREF(&PyGmicType);
    Py_INCREF(GmicException);
    PyModule_AddObject(
        m, "GmicImage",
        (PyObject *)&PyGmicImageType);  // Add GmicImage object to the module
    PyModule_AddObject(
        m, "Gmic", (PyObject *)&PyGmicType);  // Add Gmic object to the module
    PyModule_AddObject(
        m, "GmicException",
        (PyObject *)GmicException);  // Add Gmic object to the module
    PyModule_AddObject(
        m, "__version__",
        PyUnicode_Join(PyUnicode_FromString("."),
                       PyUnicode_FromString(xstr(gmic_version))));
    PyModule_AddObject(m, "__build__", gmicpy_build_info);
    // For more debugging, the user can look at __spec__ automatically set by
    // setup.py

    return m;
}

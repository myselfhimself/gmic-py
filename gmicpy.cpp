#include "gmicpy.h"

#include <Python.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#include <iostream>

#include "structmember.h"

using namespace std;

//------- G'MIC-PY MACROS ----------//

// Set the GMIC_PY_DEBUG environment variable to any value to enable logging
#ifndef GMIC_PY_LOG
#define GMIC_PY_LOG(msg)           \
    if (getenv("GMIC_PY_DEBUG")) { \
        cout << msg;               \
    }
#endif

//------- G'MIC MAIN TYPES ----------//

static PyObject *GmicException;

static PyTypeObject PyGmicImageType = {
    PyVarObject_HEAD_INIT(NULL, 0) "gmic.GmicImage" /* tp_name */
};

static PyTypeObject PyGmicType = {
    PyVarObject_HEAD_INIT(NULL, 0) "gmic.Gmic" /* tp_name */
};

typedef struct {
    PyObject_HEAD gmic_image<T> *_gmic_image;  // G'MIC library's Gmic Image
} PyGmicImage;

typedef struct {
    PyObject_HEAD
        // Using a pointer here and PyGmic_new()-time instantiation fixes a
        // crash with empty G'MIC command-set.
        gmic *_gmic;  // G'MIC library's interpreter instance
} PyGmic;

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
        image->_gmic_image->_width, image->_gmic_image->_height,
        image->_gmic_image->_depth, image->_gmic_image->_spectrum);
    images[position]._width = image->_gmic_image->_width;
    images[position]._height = image->_gmic_image->_height;
    images[position]._depth = image->_gmic_image->_depth;
    images[position]._spectrum = image->_gmic_image->_spectrum;
    memcpy(images[position]._data, image->_gmic_image->_data,
           image->_gmic_image->size() * sizeof(T));
    images[position]._is_shared = image->_gmic_image->_is_shared;
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
    swap(image->_gmic_image->_data, images[position]._data);
    image->_gmic_image->_width = images[position]._width;
    image->_gmic_image->_height = images[position]._height;
    image->_gmic_image->_depth = images[position]._depth;
    image->_gmic_image->_spectrum = images[position]._spectrum;
    image->_gmic_image->_is_shared = images[position]._is_shared;
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
                        PyErr_Format(
                            PyExc_TypeError,
                            "'%.50s' input object found at position %d in "
                            "'images' list is not a '%.400s'",
                            Py_TYPE(current_image)->tp_name, image_position,
                            PyGmicImageType.tp_name);

                        Py_XDECREF(input_gmic_images);
                        Py_XDECREF(input_gmic_image_names);

                        return NULL;
                    }
                    // Fill our just created gmic_list at same index with
                    // gmic_image coming from Python
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
                    // On the fly python GmicImage build per
                    // https://stackoverflow.com/questions/4163018/create-an-object-using-pythons-c-api/4163055#comment85217110_4163055
                    PyObject *_data = PyBytes_FromStringAndSize(
                        (const char *)images[l]._data,
                        (Py_ssize_t)sizeof(T) * images[l].size());
                    PyObject *new_gmic_image = NULL;

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
            // Else if provided 'images' type is unknown, raise Error
            else {
                PyErr_Format(
                    PyExc_TypeError,
                    "'%.50s' 'images' parameter must be a '%.400s', or list "
                    "of either '%.400s'(s)",
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

#ifdef gmic_py_numpy
/**
 * Predictable Python 3.x 'numpy' module importer.
 */
PyObject *
import_numpy_module()
{
    PyObject *numpy_module = PyImport_ImportModule("numpy");

    // exit raising numpy_module import exception
    if (!numpy_module) {
        PyErr_Clear();
        return PyErr_Format(GmicException,
                            "The 'numpy' module cannot be imported. Is it "
                            "installed or in your Python path?");
    }

    return numpy_module;
}

static PyObject *
PyGmicImage_validate_numpy_preset(PyObject *cls, PyObject *args,
                                  PyObject *kwargs)
{
    const unsigned int preset_length = 6;
    char const *keywords[] = {"numpy_conversion_preset", NULL};
    char *preset = NULL;
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, (const char *)"s",
                                     (char **)keywords, &preset))
        return NULL;

    if (strlen(preset) != preset_length) {
        PyErr_Format(
            GmicException,
            "Numpy conversion preset string must be %d-characters long.",
            preset_length);
        return NULL;
    }

    if (preset[1] != '_') {
        PyErr_Format(GmicException,
                     "Numpy conversion preset string must be like '*_*****'.");
        return NULL;
    }

    if (preset[0] != 'i' && preset[0] != 'd') {
        PyErr_Format(GmicException,
                     "Numpy conversion preset string must start with either "
                     "'i' or 'd', for interleaved / deinterleaved.");
        return NULL;
    }

    for (unsigned int i = 2; i < preset_length; i++) {
        if (preset[i] != 'x' && preset[i] != 'y' && preset[i] != 'z' &&
            preset[i] != 'c') {
            PyErr_Format(GmicException,
                         "Numpy conversion preset string's list of axes to "
                         "permute must be made of letters 'x','y','z' and "
                         "'c'. Encountered letter '%c' at position '%d'",
                         preset[i], i);
            return NULL;
        }
    }

    Py_RETURN_TRUE;
}

/*
 * GmicImage class method from_numpy_array().
 * This factory class method generates a G'MIC Image from a
 * numpy.ndarray.
 *
 *  GmicImage.from_numpy_array(obj: numpy.ndarray, deinterleave=True: bool) ->
 * GmicImage
 */
static PyObject *
PyGmicImage_from_numpy_array(PyObject *cls, PyObject *args, PyObject *kwargs)
{
    PyObject *py_arg_deinterleave =
        Py_True;  // Will deinterleave the incoming numpy.ndarray by default
    PyObject *py_arg_ndarray = NULL;
    PyObject *ndarray_type = NULL;
    unsigned int ndarray_ndim = 0;
    PyObject *ndarray_dtype = NULL;
    PyObject *ndarray_dtype_kind = NULL;
    PyObject *float32_ndarray = NULL;
    PyObject *ndarray_as_3d_unsqueezed_view = NULL;
    PyObject *ndarray_as_3d_unsqueezed_view_expanded_dims = NULL;
    PyObject *ndarray_shape_tuple = NULL;
    unsigned int _width = 1, _height = 1, _depth = 1, _spectrum = 1;
    PyObject *numpy_module = NULL;
    PyObject *ndarray_data_bytesObj = NULL;
    T *ndarray_data_bytesObj_ptr = NULL;
    char const *keywords[] = {"numpy_array", "deinterleave", NULL};
    PyGmicImage *py_gmicimage_to_fill = NULL;

    numpy_module = import_numpy_module();
    if (!numpy_module)
        return NULL;

    ndarray_type = PyObject_GetAttrString(numpy_module, "ndarray");

    if (!PyArg_ParseTupleAndKeywords(
            args, kwargs, (const char *)"O!|O!", (char **)keywords,
            (PyTypeObject *)ndarray_type, &py_arg_ndarray, &PyBool_Type,
            &py_arg_deinterleave))
        return NULL;

    Py_XINCREF(py_arg_ndarray);
    Py_XINCREF(py_arg_deinterleave);

    // Get number of dimensions and ensure we are >=1D <=4D
    ndarray_ndim = (unsigned int)PyLong_AsSize_t(
        PyObject_GetAttrString(py_arg_ndarray, "ndim"));
    if (ndarray_ndim < 1 || ndarray_ndim > 4) {
        PyErr_Format(GmicException,
                     "Provided 'data' of type 'numpy.ndarray' must be between "
                     "1D and 4D ('data.ndim'=%d).",
                     ndarray_ndim);
        return NULL;
    }

    // Get input ndarray.dtype and prevent non-integer/float/bool data types to
    // be processed
    ndarray_dtype = PyObject_GetAttrString(py_arg_ndarray, "dtype");
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

    // Using an 'ndarray.astype' array casting operation first into G'MIC's
    // core point type T <=> float32 With a memory-efficient-'ndarray.view'
    // instead of copy-obligatory 'ndarray.astype' conversion, we might get the
    // following error: ValueError: When changing to a larger dtype, its size
    // must be a divisor of the total size in bytes of the last axis of the
    // array. So, using 'astype' is the most stable, less memory-efficient way
    // :-) :-/
    float32_ndarray =
        PyObject_CallMethod(py_arg_ndarray, "astype", "O",
                            PyObject_GetAttrString(numpy_module, "float32"));

    // Get unsqueezed shape of numpy array -> GmicImage width, height, depth,
    // spectrum Getting a shape with the most axes from array:
    // https://docs.scipy.org/doc/numpy-1.17.0/reference/generated/numpy.atleast_3d.html#numpy.atleast_3d
    // Adding a depth axis using numpy.expand_dims:
    // https://docs.scipy.org/doc/numpy-1.17.0/reference/generated/numpy.expand_dims.html
    // (numpy tends to squeeze dimensions when calling the standard
    // array().shape, we circumvent this)
    ndarray_as_3d_unsqueezed_view =
        PyObject_CallMethod(numpy_module, "atleast_3d", "O", float32_ndarray);
    ndarray_as_3d_unsqueezed_view_expanded_dims = PyObject_CallMethod(
        numpy_module, "expand_dims", "OI", ndarray_as_3d_unsqueezed_view,
        2);  // Adding z axis if absent
    // After this the shape should be (w, h, 1, 3)
    ndarray_shape_tuple = PyObject_GetAttrString(
        ndarray_as_3d_unsqueezed_view_expanded_dims, "shape");
    _height =
        (unsigned int)PyLong_AsSize_t(PyTuple_GetItem(ndarray_shape_tuple, 0));
    _width =
        (unsigned int)PyLong_AsSize_t(PyTuple_GetItem(ndarray_shape_tuple, 1));
    _depth =
        (unsigned int)PyLong_AsSize_t(PyTuple_GetItem(ndarray_shape_tuple, 2));
    _spectrum =
        (unsigned int)PyLong_AsSize_t(PyTuple_GetItem(ndarray_shape_tuple, 3));

    py_gmicimage_to_fill = (PyGmicImage *)PyObject_CallFunction(
        (PyObject *)&PyGmicImageType, (const char *)"OIIII",
        Py_None,  // This empty _data buffer will be regenerated by the
                  // GmicImage constructor as a zero-filled bytes object
        _width, _height, _depth, _spectrum);

    ndarray_data_bytesObj =
        PyObject_CallMethod(ndarray_as_3d_unsqueezed_view, "tobytes", NULL);
    ndarray_data_bytesObj_ptr = (T *)PyBytes_AsString(ndarray_data_bytesObj);

    // no deinterleaving
    if (!PyObject_IsTrue(py_arg_deinterleave)) {
        for (unsigned int c = 0; c < _spectrum; c++) {
            for (unsigned int z = 0; z < _depth; z++) {
                for (unsigned int y = 0; y < _height; y++) {
                    for (unsigned int x = 0; x < _width; x++) {
                        (*(py_gmicimage_to_fill->_gmic_image))(x, y, z, c) =
                            *(ndarray_data_bytesObj_ptr++);
                    }
                }
            }
        }
    }
    else {  // deinterleaving
        for (unsigned int z = 0; z < _depth; z++) {
            for (unsigned int y = 0; y < _height; y++) {
                for (unsigned int x = 0; x < _width; x++) {
                    for (unsigned int c = 0; c < _spectrum; c++) {
                        (*(py_gmicimage_to_fill->_gmic_image))(x, y, z, c) =
                            *(ndarray_data_bytesObj_ptr++);
                    }
                }
            }
        }
    }

    Py_XDECREF(py_arg_ndarray);
    Py_XDECREF(py_arg_deinterleave);
    Py_XDECREF(ndarray_dtype);
    Py_XDECREF(ndarray_dtype_kind);
    Py_XDECREF(float32_ndarray);
    Py_XDECREF(ndarray_as_3d_unsqueezed_view);
    Py_XDECREF(ndarray_as_3d_unsqueezed_view_expanded_dims);
    Py_XDECREF(ndarray_shape_tuple);
    Py_XDECREF(ndarray_data_bytesObj);
    Py_XDECREF(ndarray_type);
    Py_XDECREF(numpy_module);

    return (PyObject *)py_gmicimage_to_fill;
}

// End of ifdef gmic_py_numpy
#endif

/** Instancing of any c++ gmic::gmic G'MIC language interpreter object (Python:
 * gmic.Gmic) **/
PyObject *
PyGmic_new(PyTypeObject *subtype, PyObject *args, PyObject *kwargs)
{
    PyGmic *self = NULL;

    self = (PyGmic *)subtype->tp_alloc(subtype, 0);

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
        if (run_impl((PyObject *)self, args, kwargs) == NULL) {
            return NULL;
        }
    }

    return (PyObject *)self;
}

PyDoc_STRVAR(run_impl_doc,
             "Gmic.run(command, images=None, image_names=None)\n\
Run G'MIC interpreter following a G'MIC language command(s) string, on 0 or more namable ``GmicImage`` items.\n\n\
Note (single-image short-hand calling): if ``images`` is a ``GmicImage``, then ``image_names`` must be either a ``str`` or be omitted.\n\n\
Example:\n\
    Here is a long example describing several use cases::\n\n\
        import gmic\n\
        import struct\n\
        import random\n\
        instance1 = gmic.Gmic('echo_stdout \\'instantiation and run all in one\\')\n\
        instance2 = gmic.Gmic()\n\
        instance2.run('echo_stdout \\'hello world\\'') # G'MIC command without images parameter\n\
        a = gmic.GmicImage(struct.pack(*('256f',) + tuple([random.random() for a in range(256)])), 16, 16) # Build 16x16 greyscale image\n\
        instance2.run('blur 12,0,1 resize 50%,50%', a) # Blur then resize the image\n\
        a._width == a._height == 8 # The image is half smaller\n\
        instance2.run('display', a) # If you have X11 enabled (linux only), show the image in a window\n\
        image_names = ['img_' + str(i) for i in range(10)] # You can also name your images if you have several (optional)\n\
        images = [gmic.GmicImage(struct.pack(*((str(w*h)+'f',) + (i*2.0,)*w*h)), w, h) for i in range(10)] # Prepare a list of image\n\
        instance1.run('add 1 print', images, image_names) # And pipe those into the interpreter\n\
        instance1.run('blur 10,0,1 print', images[0], 'my_pic_name') # Short-hand 1-image calling style\n\n\
Args:\n\
    command (str): An image-processing command in the G'MIC language\n\
    images (Optional[Union[List[gmic.GmicImage], gmic.GmicImage]]): A list of ``GmicImage`` items that G'MIC will edit in place, or a single ``gmic.GmicImage`` which will used for input only. Defaults to None.\n\
        Put a list variable here, not a plain ``[]``.\n\
        If you pass a list, it can be empty if you intend to fill or complement it using your G'MIC command.\n\
    image_names (Optional[List<str>]): A list of names for the images, defaults to None.\n\
        In-place editing by G'MIC can happen, you might want to pass your list as a variable instead.\n\
\n\
Returns:\n\
    None: Returns ``None`` or raises a ``GmicException``.\n\
\n\
Raises:\n\
    GmicException: This translates' G'MIC C++ same-named exception. Look at the exception message for details.");

static PyMethodDef PyGmic_methods[] = {
    {"run", (PyCFunction)run_impl, METH_VARARGS | METH_KEYWORDS, run_impl_doc},
    {NULL} /* Sentinel */
};

// ------------ G'MIC IMAGE BINDING ----//

PyObject *
PyGmicImage_new(PyTypeObject *subtype, PyObject *args, PyObject *kwargs)
{
    PyGmicImage *self = NULL;
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

    bool bytesObj_is_bytes = false;
    char const *keywords[] = {"data",     "width",  "height", "depth",
                              "spectrum", "shared", NULL};

    // Parameters parsing and checking
    if (!PyArg_ParseTupleAndKeywords(
            args, kwargs, "|OIIIIp", (char **)keywords, &bytesObj, &_width,
            &_height, &_depth, &_spectrum, &_is_shared))
        return NULL;

    self = (PyGmicImage *)subtype->tp_alloc(subtype, 0);
    if (self == NULL) {
        return NULL;
    }

    // Default bytesObj value to None
    if (bytesObj == NULL) {
        bytesObj = Py_None;
    }
    else {
        Py_INCREF(bytesObj);
    }

    if (bytesObj != Py_None) {
        bytesObj_is_bytes = (bool)PyBytes_Check(bytesObj);
        if (!bytesObj_is_bytes) {
            PyErr_Format(PyExc_TypeError,
                         "Parameter 'data' must be a "
                         "pure-python 'bytes' buffer object.");
            // TODO pytest this
            return NULL;
        }
    }
    else {  // if bytesObj is None, attempt to set it as an empty bytes object
        // following image dimensions
        // If dimensions are OK, create a pixels-count-zero-filled
        // bytesarray-based bytes object to be ingested by the _data parameter
        if (_width >= 1 && _height >= 1 && _depth >= 1 && _spectrum >= 1) {
            bytesObj = PyObject_CallFunction(
                (PyObject *)&PyBytes_Type, "O",
                PyObject_CallFunction(
                    (PyObject *)&PyByteArray_Type, "I",
                    _width * _height * _depth * _spectrum * sizeof(T), NULL),
                NULL);
            Py_INCREF(bytesObj);
            bytesObj_is_bytes = true;
            // TODO pytest this
        }
        else {  // If dimensions are not OK, raise exception
            PyErr_Format(PyExc_TypeError,
                         "If you do not provide a 'data' parameter, make at "
                         "least all dimensions >=1.");
            // TODO pytest this
            return NULL;
        }
    }

    // Bytes object spatial dimensions vs. bytes-length checking
    dimensions_product = _width * _height * _depth * _spectrum;
    _data_bytes_size = PyBytes_Size(bytesObj);
    if ((Py_ssize_t)(dimensions_product * sizeof(T)) != _data_bytes_size) {
        PyErr_Format(PyExc_ValueError,
                     "GmicImage dimensions-induced buffer bytes size "
                     "(%d*%dB=%d) cannot be strictly negative or "
                     "different than the _data buffer size in bytes (%d)",
                     dimensions_product, sizeof(T),
                     dimensions_product * sizeof(T), _data_bytes_size);
        return NULL;
    }

    // Importing input data to an internal buffer
    try {
        self->_gmic_image->assign(_width, _height, _depth, _spectrum);
        self->_gmic_image->_is_shared = _is_shared;
    }
    // Ugly exception catching, probably to catch a
    // cimg::GmicInstanceException()
    catch (...) {
        dimensions_product = _width * _height * _depth * _spectrum;
        PyErr_Format(PyExc_MemoryError,
                     "Allocation error in "
                     "GmicImage::assign(_width=%d,_height=%d,_depth=%d,_"
                     "spectrum=%d), "
                     "are you requesting too much memory (%d bytes)?",
                     _width, _height, _depth, _spectrum,
                     dimensions_product * sizeof(T));
        return NULL;
    }

    memcpy(self->_gmic_image->_data, PyBytes_AsString(bytesObj),
           PyBytes_Size(bytesObj));

    Py_XDECREF(bytesObj);

    return (PyObject *)self;
}

static PyObject *
PyGmicImage_repr(PyGmicImage *self)
{
    return PyUnicode_FromFormat(
        "<%s object at %p with _data address at %p, w=%d h=%d d=%d s=%d "
        "shared=%d>",
        Py_TYPE(self)->tp_name, self, self->_gmic_image->_data,
        self->_gmic_image->_width, self->_gmic_image->_height,
        self->_gmic_image->_depth, self->_gmic_image->_spectrum,
        self->_gmic_image->_is_shared);
}

static PyObject *
PyGmicImage_call(PyObject *self, PyObject *args, PyObject *kwargs)
{
    const char *keywords[] = {"x", "y", "z", "s", NULL};
    int x, y, z, c;
    x = y = z = c = 0;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|iiii", (char **)keywords,
                                     &x, &y, &z, &c)) {
        return NULL;
    }

    return PyFloat_FromDouble(
        (*((PyGmicImage *)self)->_gmic_image)(x, y, z, c));
}

static PyObject *
PyGmicImage_alloc(PyTypeObject *type, Py_ssize_t nitems)
{
    PyObject *obj = (PyObject *)PyObject_Malloc(type->tp_basicsize);
    ((PyGmicImage *)obj)->_gmic_image = new gmic_image<T>();
    GMIC_PY_LOG("PyGmicImage_alloc\n");
    PyObject_Init(obj, type);
    return obj;
}

static PyObject *
PyGmic_alloc(PyTypeObject *type, Py_ssize_t nitems)
{
    PyObject *obj = (PyObject *)PyObject_Malloc(type->tp_basicsize);
    ((PyGmic *)obj)->_gmic = new gmic();
    GMIC_PY_LOG("PyGmic_alloc\n");
    PyObject_Init(obj, type);
    return obj;
}

static void
PyGmicImage_free(PyObject *v)
{
    PyObject_Free(v);
}

static void
PyGmic_free(PyObject *v)
{
    PyObject_Free(v);
}

static void
PyGmicImage_dealloc(PyGmicImage *self)
{
    delete self->_gmic_image;
    self->_gmic_image = NULL;
    GMIC_PY_LOG("PyGmicImage_dealloc\n");
    Py_TYPE(self)->tp_free((PyObject *)self);
}

static void
PyGmic_dealloc(PyGmic *self)
{
    delete self->_gmic;
    self->_gmic = NULL;
    // keep this in place for test_gmic_py_memfreeing.py pytest case
    GMIC_PY_LOG("PyGmic_dealloc\n");
    Py_TYPE(self)->tp_free((PyObject *)self);
}

static PyObject *
module_level_run_impl(PyObject *, PyObject *args, PyObject *kwargs)
{
    PyObject *temp_gmic_instance =
        PyObject_CallObject((PyObject *)(&PyGmicType), NULL);

    Py_INCREF(temp_gmic_instance);

    // Return None or a Python exception flag
    PyObject *run_impl_result = run_impl(temp_gmic_instance, args, kwargs);

    Py_XDECREF(temp_gmic_instance);

    return run_impl_result;
}

PyDoc_STRVAR(module_level_run_impl_doc,
             "run(command, images=None, image_names=None)\n\n\
Run the G'MIC interpreter with a G'MIC language command(s) string, on 0 or more nameable GmicImage(s). This is a short-hand for calling ``gmic.Gmic().run`` with the exact same parameters signature.\n\n\
Note (single-image short-hand calling): if ``images`` is a ``GmicImage``, then ``image_names`` must be either a ``str`` or be omitted.\n\n\
Note (interpreter warm-up): calling ``gmic.run`` multiple times is inefficient as it spawns then drops a new G'MIC interpreter instance for every call. For better performance, you can tie a ``gmic.Gmic`` G'MIC interpreter instance to a variable instead and call its ``run`` method multiple times. Look at ``gmic.Gmic.run`` for more information.\n\n\
Example:\n\
    Several ways to use the module-level ``gmic.run()`` function::\n\n\
        import gmic\n\
        import struct\n\
        import random\n\
        gmic.run('echo_stdout \\'hello world\\'') # G'MIC command without images parameter\n\
        a = gmic.GmicImage(struct.pack(*('256f',) + tuple([random.random() for a in range(256)])), 16, 16) # Build 16x16 greyscale image\n\
        gmic.run('blur 12,0,1 resize 50%,50%', a) # Blur then resize the image\n\
        a._width == a._height == 8 # The image is half smaller\n\
        gmic.run('display', a) # If you have X11 enabled (linux only), show the image in a window\n\
        image_names = ['img_' + str(i) for i in range(10)] # You can also name your images if you have several (optional)\n\
        images = [gmic.GmicImage(struct.pack(*((str(w*h)+'f',) + (i*2.0,)*w*h)), w, h) for i in range(10)] # Prepare a list of image\n\
        gmic.run('add 1 print', images, image_names) # And pipe those into the interpreter\n\
        gmic.run('blur 10,0,1 print', images[0], 'my_pic_name') # Short-hand 1-image calling style\n\n\
Args:\n\
    command (str): An image-processing command in the G'MIC language\n\
    images (Optional[Union[List[gmic.GmicImage], gmic.GmicImage]]): A list of ``GmicImage`` items that G'MIC will edit in place, or a single ``gmic.GmicImage`` which will used for input only. Defaults to None.\n\
        Put a list variable here, not a plain ``[]``.\n\
        If you pass a list, it can be empty if you intend to fill or complement it using your G'MIC command.\n\
    image_names (Optional[List<str>]): A list of names for the images, defaults to None.\n\
        In-place editing by G'MIC can happen, you might want to pass your list as a variable instead.\n\
\n\
Returns:\n\
    None: Returns ``None`` or raises a ``GmicException``.\n\
\n\
Raises:\n\
    GmicException: This translates' G'MIC C++ same-named exception. Look at the exception message for details.");

static PyMethodDef gmic_methods[] = {
    {"run", (PyCFunction)module_level_run_impl, METH_VARARGS | METH_KEYWORDS,
     module_level_run_impl_doc},
    {nullptr, nullptr, 0, nullptr}};

PyDoc_STRVAR(gmic_module_doc,
             "G'MIC image processing library Python binary module.\n\n\
Use ``gmic.run`` or ``gmic.Gmic`` to run G'MIC commands inside the G'MIC C++ interpreter, manipulate ``gmic.GmicImage`` especially with ``numpy``.\n\n\
Below are constants to be used by ``GmicImage.from_numpy_array`` and ``GmicImage.to_numpy_array`` conversion methods.\n\n"
#ifdef gmic_py_numpy
             "\nAttributes:\n\n\
    NUMPY_FORMAT_DEFAULT:\n\
        Basically an interleaved non-squeezed ``zyxc`` array (the same as ``NUMPY_FORMAT_PIL`` but unsqueezed):\n\n\
        - **output image:** shape will be *(depth, height, width, channels)* unsqueezed, pixel values will be interleaved. Equates to *interleave=True*, *permute='zyxc'*, *squeeze=False*.\n\
        - **input image:** assuming shape as *(depth, height, width, channels)*, with interleaved pixel values. Equates to *deinterleave=True*, *permute='zyxc'*.\n\
    NUMPY_FORMAT_GMIC: The exact same format as G'MIC internally - ``xyzc`` deinterleaved non-squeezed:\n\n\
        - **output image:** shape will be *(width, depth, height, channels)* unsqueezed, pixel values will be deinterleaved. Equates to *interleave=False*, *permute='xyzc'* or *permute=''*, *squeeze=False*.\n\
        - **input image:** assuming shape as *(width, depth, height, channels)*, with deinterleaved pixel values. Equates to *deinterleave=False*, *permute='xyzc'* or *permute=''*.\n\
    NUMPY_FORMAT_PIL: The format liked by PIL/Pillow Python Imaging Library (2D) - ``(z)yxc`` interleaved squeezed:\n\n\
        - **output image:** shape will be *([depth,] height, width, channels)* squeezed (ie. the depth=1 dimension is hidden), pixel values will be interleaved. Equates to *interleave=True*, *permute='zyxc'*, *squeeze=True*.\n\
        - **input image:** assuming shape as *([depth,] height, width, channels)*, with interleaved pixel values. Equates to *deinterleave=True*, *permute='zyxc'*.\n\
    NUMPY_FORMAT_SCIKIT_IMAGE: An interleaved ``zxyc`` unsqueezed array:\n\n\
        - **output image:** shape will be *(depth, width, height, channels)* unsqueezed, pixel values will be interleaved. Equates to *interleave=True*, *permute='zxyc'*, *squeeze=True*.\n\
        - **input image:** assuming shape as *(depth, width, height, channels)*, with interleaved pixel values. Equates to *deinterleave=True*, *permute='zxyc'*.");
#endif

PyModuleDef gmic_module = {PyModuleDef_HEAD_INIT, "gmic", gmic_module_doc, 0,
                           gmic_methods};

PyDoc_STRVAR(
    PyGmicImage_doc,
    "GmicImage(data=None, width=1, height=1, depth=1, spectrum=1, shared=False)\n\n\
Simplified mapping of the C++ ``gmic_image`` type. Stores a binary buffer of data, a height, width, depth, spectrum.\n\n\
Example:\n\n\
    Several ways to use a GmicImage simply::\n\n\
        import gmic\n\
        empty_1x1x1_black_image = gmic.GmicImage() # or gmic.GmicImage(None,1,1,1,1) for example\n\
        import struct\n\
        i = gmic.GmicImage(struct.pack('2f', 0.0, 1.5), 1, 1) # 2D 1x1 image\n\
        gmic.run('add 1', i) # GmicImage injection into G'MIC's interpreter\n\
        i # Using GmicImage's repr() string representation\n\
        # Output: <gmic.GmicImage object at 0x7f09bfb504f8 with _data address at 0x22dd5b0, w=1 h=1 d=1 s=1 shared=0>\n\
        i(0,0) == 1.0 # Using GmicImage(x,y,z) pixel reading operator after initialization\n\
        gmic.run('resize 200%,200%', i) # Some G'MIC operations may reallocate the image buffer in place without risk\n\
        i._width == i._height == 2 # Use the _width, _height, _depth, _spectrum, _data, _data_str, _is_shared read-only attributes\n\n\
Args:\n\
    data (Optional[bytes]): Raw data for the image (must be a sequence of 4-bytes floats blocks, with as many blocks as all the dimensions multiplied together).\n\
    width (Optional[int]): Image width in pixels. Defaults to 1.\n\
    height (Optional[int]): Image height in pixels. Defaults to 1.\n\
    depth (Optional[int]): Image height in pixels. Defaults to 1.\n\
    spectrum (Optional[int]): Number of channels per pixel. Defaults to 1.\n\
    shared (Optional[bool]): C++ option: whether the buffer should be shareable between several GmicImages and operations. Defaults to False.\n\n\
Note:\n\
    **GmicImage(x=0, y=0, z=0, s=0)**\n\n\
    This instance method allows you to read pixels in a ``GmicImage`` for given coordinates.\n\n\
    You can read, but cannot write pixel values by passing some or all coordinates the following way::\n\n\
        import gmic\n\
        images = []\n\
        gmic.run(\"sp apples\", images)\n\
        image = images[0]\n\
        print(image(0,2,0,2)) # or image(y=2,z=2)\n\
        print(image(0,0,0,0)) # or image()\n\
        for x in range(image._width):\n\
            for y in range(image._height):\n\
                for z in range(image._depth):\n\
                    for c in range(image._spectrum):\n\
                        print(image(x,y,z,c))");

static PyObject *
PyGmicImage_get_width(PyGmicImage *self, void *closure)
{
    return PyLong_FromSize_t(self->_gmic_image->_width);
}

static PyObject *
PyGmicImage_get_height(PyGmicImage *self, void *closure)
{
    return PyLong_FromSize_t(self->_gmic_image->_height);
}

static PyObject *
PyGmicImage_get_depth(PyGmicImage *self, void *closure)
{
    return PyLong_FromSize_t(self->_gmic_image->_depth);
}

static PyObject *
PyGmicImage_get_spectrum(PyGmicImage *self, void *closure)
{
    return PyLong_FromSize_t(self->_gmic_image->_spectrum);
}

static PyObject *
PyGmicImage_get__is_shared(PyGmicImage *self, void *closure)
{
    return PyBool_FromLong((long)self->_gmic_image->_is_shared);
}

static PyObject *
PyGmicImage_get__data(PyGmicImage *self, void *closure)
{
    // Py_FinalizeEx();
    return PyBytes_FromStringAndSize((char *)self->_gmic_image->_data,
                                     sizeof(T) * (self->_gmic_image->size()));
}

static PyObject *
PyGmicImage_get__data_str(PyGmicImage *self, void *closure)
{
    unsigned int image_size = self->_gmic_image->size();
    PyObject *unicode_json = PyUnicode_New((Py_ssize_t)image_size, 65535);

    for (unsigned int a = 0; a < image_size; a++) {
        PyUnicode_WriteChar(unicode_json, (Py_ssize_t)a,
                            (Py_UCS4)self->_gmic_image->_data[a]);
    }

    return unicode_json;
}

PyGetSetDef PyGmicImage_getsets[] = {
    {(char *)"_data", /* name */
     (getter)PyGmicImage_get__data,
     NULL,          // no setter
     "_data bytes", /* doc */
     NULL /* closure */},
    {(char *)"_data_str", /* name */
     (getter)PyGmicImage_get__data_str,
     NULL,                      // no setter
     "_data bytes decoded str", /* doc */
     NULL /* closure */},
    {(char *)"_width", (getter)PyGmicImage_get_width, NULL, "_width", NULL},
    {(char *)"_height", (getter)PyGmicImage_get_height, NULL, "_height", NULL},
    {(char *)"_depth", (getter)PyGmicImage_get_depth, NULL, "_depth", NULL},
    {(char *)"_spectrum", (getter)PyGmicImage_get_spectrum, NULL, "_spectrum",
     NULL},
    {(char *)"_is_shared", (getter)PyGmicImage_get__is_shared, NULL,
     "_is_shared", NULL},
    {NULL}};

#ifdef gmic_py_numpy

/*
 * GmicImage object method to_numpy_array().
 *
 * GmicImage().to_numpy_array(astype=numpy.float32: numpy.dtype,
 * interleave=False: bool, squeeze_shape=False: bool) -> numpy.ndarray
 *
 */
static PyObject *
PyGmicImage_to_numpy_array(PyGmicImage *self, PyObject *args, PyObject *kwargs)
{
    char const *keywords[] = {"astype", "interleave", "squeeze_shape", NULL};
    // TODO add "permute" and "output_format" keywords + implementation
    PyObject *numpy_module = NULL;
    PyObject *ndarray_type = NULL;
    PyObject *return_ndarray = NULL;
    PyObject *ndarray_shape_tuple = NULL;
    PyObject *ndarray_shape_list = NULL;
    PyObject *float32_dtype = NULL;
    PyObject *numpy_bytes_buffer = NULL;
    float *numpy_buffer = NULL;
    float *ndarray_bytes_buffer_ptr = NULL;
    int buffer_size = 0;
    PyObject *arg_astype = NULL;
    int arg_interleave = 1;     // Will interleave the final matrix by default
    int arg_squeeze_shape = 0;  // Will squeeze the final shape if asked, for
                                // easier python-matplotlib display

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|Opp", (char **)keywords,
                                     &arg_astype, &arg_interleave,
                                     &arg_squeeze_shape)) {
        return NULL;
    }

    numpy_module = import_numpy_module();
    if (!numpy_module)
        return NULL;

    ndarray_type = PyObject_GetAttrString(numpy_module, "ndarray");

    ndarray_shape_tuple = PyList_New(0);
    PyList_Append(ndarray_shape_tuple,
                  PyLong_FromSize_t((size_t)self->_gmic_image->_depth));
    PyList_Append(ndarray_shape_tuple,
                  PyLong_FromSize_t((size_t)self->_gmic_image->_height));
    PyList_Append(ndarray_shape_tuple,
                  PyLong_FromSize_t((size_t)self->_gmic_image->_width));
    PyList_Append(ndarray_shape_tuple,
                  PyLong_FromSize_t((size_t)self->_gmic_image->_spectrum));
    ndarray_shape_list = PyList_AsTuple(ndarray_shape_tuple);

    float32_dtype = PyObject_GetAttrString(numpy_module, "float32");
    buffer_size = sizeof(T) * self->_gmic_image->size();
    numpy_buffer = (float *)malloc(buffer_size);
    ndarray_bytes_buffer_ptr = numpy_buffer;
    // If interleaving is needed, copy the gmic_image buffer towards numpy by
    // interleaving RRR,GGG,BBB into RGB,RGB,RGB
    if (arg_interleave) {
        for (unsigned int z = 0; z < self->_gmic_image->_depth; z++) {
            for (unsigned int y = 0; y < self->_gmic_image->_height; y++) {
                for (unsigned int x = 0; x < self->_gmic_image->_width; x++) {
                    for (unsigned int c = 0; c < self->_gmic_image->_spectrum;
                         c++) {
                        (*ndarray_bytes_buffer_ptr++) =
                            (*(self->_gmic_image))(x, y, z, c);
                    }
                }
            }
        }
    }
    else {
        // If deinterleaving is not needed, since this is G'MIC's internal
        // image shape, keep pixel data order as is and copy it simply
        memcpy(numpy_buffer, self->_gmic_image->_data,
               self->_gmic_image->size() * sizeof(T));
    }
    numpy_bytes_buffer =
        PyBytes_FromStringAndSize((const char *)numpy_buffer, buffer_size);
    free(numpy_buffer);
    // class numpy.ndarray(<our shape>, dtype=<float32>, buffer=<our bytes>,
    // offset=0, strides=None, order=None)
    return_ndarray = PyObject_CallFunction(ndarray_type, (const char *)"OOS",
                                           ndarray_shape_list, float32_dtype,
                                           numpy_bytes_buffer);

    if (arg_squeeze_shape) {
        return_ndarray =
            PyObject_CallMethod(numpy_module, "squeeze", "O", return_ndarray);
        if (!return_ndarray) {
            PyErr_Format(GmicException, "'%.50s' failed to run numpy.squeeze.",
                         ((PyTypeObject *)Py_TYPE(ndarray_type))->tp_name);
        }
    }

    // arg_astype should be according to ndarray.astype's documentation, a
    // string, python type or numpy.dtype delegating this type check to the
    // astype() method
    if (return_ndarray != NULL && arg_astype != NULL) {
        return_ndarray =
            PyObject_CallMethod(return_ndarray, "astype", "O", arg_astype);
    }

    Py_XDECREF(ndarray_type);
    Py_XDECREF(ndarray_shape_list);
    Py_XDECREF(ndarray_shape_tuple);
    Py_XDECREF(float32_dtype);
    Py_XDECREF(numpy_bytes_buffer);
    Py_XDECREF(numpy_module);

    return return_ndarray;
}
#endif
// end ifdef gmic_py_numpy

#ifdef gmic_py_numpy
PyDoc_STRVAR(
    PyGmicImage_from_numpy_array_doc,
    "GmicImage.from_numpy_array(numpy_array, input_format=gmic.NUMPY_FORMAT_DEFAULT, deinterleave=False, permute='')\n\n\
Make a GmicImage from a 1-4 dimensions numpy.ndarray.\n\n\
G'MIC works with (width, height, depth, spectrum/channels) matrix layout, with 32bit-float pixel values deinterleaved (ie. RRR,GGG,BBB).\n\
If your input matrix does not have that G'MIC data layout, you may select a reformatter using the ``input_format`` parameter;\n\
or fine-grain-create your own using the ``deinterleave`` and ``permute`` parameters.\n\n\
If your matrix is less than 4D, G'MIC will tentatively add append void dimensions to it (eg. for a shape of (3,1) -> (3,1,1,1)). You can avoid this by using ``numpy.expand_dims`` or ``numpy.atleast_*d`` functions yourself first.\n\
If your pixel values (ie. ``numpy.ndarray.dtype``) are not in a ``float32`` format, G'MIC will tentatively call ``numpy.astype(numpy_array, numpy.float32)`` to cast its contents first.\n\
\n\
Example:\n\n\
    Several ways to use a GmicImage simply::\n\n\
        import gmic\n\
        empty_1x1x1_black_image = gmic.GmicImage() # or gmic.GmicImage(None,1,1,1,1) for example\n\
        import struct\n\
        i = gmic.GmicImage(struct.pack('2f', 0.0, 1.5), 1, 1) # 2D 1x1 image\n\
        gmic.run('add 1', i) # GmicImage injection into G'MIC's interpreter\n\
        i # Using GmicImage's repr() string representation\n\
        # Output: <gmic.GmicImage object at 0x7f09bfb504f8 with _data address at 0x22dd5b0, w=1 h=1 d=1 s=1 shared=0>\n\
        i(0,0) == 1.0 # Using GmicImage(x,y,z) pixel reading operator after initialization\n\
        gmic.run('resize 200%,200%', i) # Some G'MIC operations may reallocate the image buffer in place without risk\n\
        i._width == i._height == 2 # Use the _width, _height, _depth, _spectrum, _data, _data_str, _is_shared read-only attributes\n\n\
Args:\n\
    numpy_array (numpy.ndarray): A non-empty 1D-4D Numpy array.\n\
    input_format (Optional[int]): one of the following preset values (defaults to `gmic.NUMPY_FORMAT_DEFAULT`):\n\n\
        - ``gmic.NUMPY_FORMAT_DEFAULT``: assuming input matrix is formatted as (width, depth, height, channels) and pixel values are interleaved. Pixel-channels deinterleaving will be done, no dimensions permutation will be done. Equates to deinterleave=True, permute='' defaults.\n\
        - ``gmic.NUMPY_FORMAT_GMIC``: assuming input matrix is formatted as (width, depth, height, channels) and pixel values are deinterleaved. No pixel-channels deinterleaving will be done, no dimensions permutation will be done. Equates to deinterleave=False, permute=''.\n\
        - ``gmic.NUMPY_FORMAT_PIL``: assuming input matrix is formatted as ([depth,] height, width, channels) and pixel values are interleaved. Equates to deinterleave=True, permute='zyxc'.\n\
        - ``gmic.NUMPY_FORMAT_SCIKIT_IMAGE``: assuming input matrix is formatted as (depth, width, height, channels) and pixel values are interleaved. Equates to deinterleave=True, permute='zxyc'. Defaults to ``gmic.NUMPY_FORMAT_GMIC``.\n\
    deinterleave (Optional[bool]): If ``True``, pixel channel values will be deinterleaved inside the GmicImage data. If ``False``, pixel channels vector values will be untouched.\n\
        Defaults to ``False``. This parameter will be omitted if ``input_format`` is set to a different value than ``gmic.NUMPY_FORMAT_DEFAULT``.\n\
    permute (Optional[str]): If non-empty, a G'MIC ``permute`` operation will be run with this parameter (eg. yxzc) on the input matrix before saving into the GmicImage.\n\
        See https://gmic.eu/reference.shtml#permute\n\
        This parameter will be omitted if ``input_format`` is set to a different value than ``gmic.NUMPY_FORMAT_DEFAULT``\n\
        Defaults to \"\" (no permutation).\n\
\n\
Returns:\n\
    GmicImage: A new ``GmicImage`` based the input ``numpy.ndarray`` data.\n\
\n\
Raises:\n\
    GmicException, TypeError: Look at the exception message for details. Matrices with dimensions <1D or >4D will be rejected.");

PyDoc_STRVAR(
    PyGmicImage_to_numpy_array_doc,
    "GmicImage.to_numpy_array(astype=numpy.float32, output_format=gmic.NUMPY_FORMAT_DEFAULT, interleave=False, permute='', squeeze_shape=False)\n\n\
Make a numpy.ndarray from a GmicImage.\n\
G'MIC does not squeeze dimensions internally, so unless you use the ``squeeze_shape`` flag calling ``numpy.squeeze`` for you, the output matrix will be 4D.\n\n\
Args:\n\
    astype (numpy.dtype): The type to which G'MIC's float32 pixel values will cast to for the output matrix.\n\
    output_format (Optional[int]): Preset for the output matrix layout and pixel vector format. Defaults to ``gmic.NUMPY_FORMAT_DEFAULT``. Choose among one of the following preset values:\n\n\
        - ``gmic.NUMPY_FORMAT_DEFAULT``: output matrix will be formatted as (width, depth, height, channels), with pixel values interleaved (ie. ``RGB,RGB,RGB``). Equates to interleave=True, permute='' defaults.\n\
        - ``gmic.NUMPY_FORMAT_GMIC``: output matrix will be formatted as (width, depth, height, channels), with pixel values deinterleaved (ie. ``RRR,GGG,BBB``). Equates to interleave=False, permute='' defaults.\n\
        - ``gmic.NUMPY_FORMAT_PIL``: output matrix matrix will be formatted as (depth, height, width, channels), with pixel values interleaved. Equates to interleave=True, permute='zyxc'.\n\
        - ``gmic.NUMPY_FORMAT_SCIKIT_IMAGE``: output matrix will be formatted as (depth, width, height, channels), with pixel values interleaved. Equates to interleave=True, permute='zxyc'.\n\
    interleave (Optional[bool]): If ``True``, pixel channel values will be interleaved (ie. RGB, RGB, RGB) within the numpy array. If ``False``, pixel channels vector values will be untouched/deinterleaved (ie. RRR,GGG,BBB).\n\
        Defaults to ``False``.\n\
        This parameter will be omitted if ``output_format`` is set to a different value than ``gmic.NUMPY_FORMAT_DEFAULT``.\n\
    permute (Optional[str]): If non-empty, a G'MIC ``permute`` operation will be run with this parameter (eg. yxzc) on the output matrix before saving into the GmicImage.\n\
        See https://gmic.eu/reference.shtml#permute\n\
        This parameter will be omitted if ``output_format`` is set to a different value than ``gmic.NUMPY_FORMAT_DEFAULT``\n\
        Defaults to \"\" (ie. no permutation).\n\
\n\
Returns:\n\
    numpy.ndarray: A new ``numpy.ndarray`` based the input ``GmicImage`` data.");

PyDoc_STRVAR(PyGmicImage_validate_numpy_preset_doc,
             "GmicImage.validate_numpy_preset(numpy_conversion_preset)\n\n\
Validate a preset encoded string for ``GmicImage.to_numpy_array`` and ``GmicImage.from_numpy_array``.\n\
G'MIC defines its own ``gmic.NUMPY_FORMAT_*`` validation presets, but you can define your own as a string in the form of ``d`` (deinterleaved pixel channels) or ``i`` (interleaved pixel channels) followed by a 5-letters axes-permutation string.\n\n\
Example: ``i_xyzc``.\n\n\
Args:\n\
    numpy_conversion_preset: a ``gmic.NUMPY_FORMAT_*``-like preset string to validate.\n\
\n\
Returns:\n\
    bool: ``True`` or raises a ``GmicException`` with an explanatoray misvalidation error.");
#endif

static PyObject *
PyGmicImage__copy__(PyGmicImage *self, PyObject *args)
{
    return PyObject_CallFunction(
        (PyObject *)&PyGmicImageType, (const char *)"SIIIIi",
        PyGmicImage_get__data((PyGmicImage *)self, (void *)NULL),
        (unsigned int)((PyGmicImage *)self)->_gmic_image->_width,
        (unsigned int)((PyGmicImage *)self)->_gmic_image->_height,
        (unsigned int)((PyGmicImage *)self)->_gmic_image->_depth,
        (unsigned int)((PyGmicImage *)self)->_gmic_image->_spectrum,
        (int)((PyGmicImage *)self)->_gmic_image->_is_shared);
}

static PyMethodDef PyGmicImage_methods[] = {
#ifdef gmic_py_numpy
    {"from_numpy_array", (PyCFunction)PyGmicImage_from_numpy_array,
     METH_CLASS | METH_VARARGS | METH_KEYWORDS,
     PyGmicImage_from_numpy_array_doc},
    {"to_numpy_array", (PyCFunction)PyGmicImage_to_numpy_array,
     METH_VARARGS | METH_KEYWORDS, PyGmicImage_to_numpy_array_doc},
    {"validate_numpy_preset", (PyCFunction)PyGmicImage_validate_numpy_preset,
     METH_CLASS | METH_VARARGS | METH_KEYWORDS,
     PyGmicImage_validate_numpy_preset_doc},
#endif
    {"__copy__", (PyCFunction)PyGmicImage__copy__, METH_VARARGS,
     "Copy method for copy.copy() support. Deepcopying and pickle-ing are not "
     "supported."},
    {NULL} /* Sentinel */
};

static PyObject *
PyGmicImage_richcompare(PyObject *self, PyObject *other, int op)
{
    PyObject *result = NULL;

    if (Py_TYPE(other) != Py_TYPE(self)) {
        Py_RETURN_NOTIMPLEMENTED;
    }

    Py_INCREF(self);
    Py_INCREF(other);

    switch (op) {
        case Py_LT:
        case Py_LE:
        case Py_GT:
        case Py_GE:
            Py_XDECREF(self);
            Py_XDECREF(other);
            Py_RETURN_NOTIMPLEMENTED;
        case Py_EQ:
            // Leverage the CImg == C++ operator
            result = *((PyGmicImage *)self)->_gmic_image ==
                             *((PyGmicImage *)other)->_gmic_image
                         ? Py_True
                         : Py_False;
            break;
        case Py_NE:
            // Leverage the CImg != C++ operator
            result = *((PyGmicImage *)self)->_gmic_image !=
                             *((PyGmicImage *)other)->_gmic_image
                         ? Py_True
                         : Py_False;
            break;
    }

    Py_XDECREF(self);
    Py_XDECREF(other);

    return result;
}

PyMODINIT_FUNC
PyInit_gmic()
{
    PyObject *m;

    // The GmicException inherits Python's builtin Exception.
    // Used for non-precise errors raised from this module.
    GmicException = PyErr_NewExceptionWithDoc(
        "gmic.GmicException", /* char *name */
        "Only exception class of the Gmic module.\n\nThis wraps G'MIC's C++ "
        "gmic_exception. Refer to the exception message itself.", /* char *doc
                                                                   */
        NULL, /* PyObject *base */
        NULL /* PyObject *dict */);

    PyGmicImageType.tp_new = (newfunc)PyGmicImage_new;
    PyGmicImageType.tp_init = 0;
    PyGmicImageType.tp_basicsize = sizeof(PyGmicImage);
    PyGmicImageType.tp_dealloc = (destructor)PyGmicImage_dealloc;
    PyGmicImageType.tp_alloc = (allocfunc)PyGmicImage_alloc;
    PyGmicImageType.tp_free = (freefunc)PyGmicImage_free;
    PyGmicImageType.tp_methods = PyGmicImage_methods;
    PyGmicImageType.tp_repr = (reprfunc)PyGmicImage_repr;
    PyGmicImageType.tp_call = (ternaryfunc)PyGmicImage_call;
    PyGmicImageType.tp_getattro = PyObject_GenericGetAttr;
    PyGmicImageType.tp_doc = PyGmicImage_doc;
    PyGmicImageType.tp_members = NULL;
    PyGmicImageType.tp_getset = PyGmicImage_getsets;
    PyGmicImageType.tp_richcompare = PyGmicImage_richcompare;
    PyGmicImageType.tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE;

    if (PyType_Ready(&PyGmicImageType) < 0)
        return NULL;

    PyGmicType.tp_new = (newfunc)PyGmic_new;
    PyGmicType.tp_basicsize = sizeof(PyGmic);
    PyGmicType.tp_methods = PyGmic_methods;
    PyGmicType.tp_repr = (reprfunc)PyGmic_repr;
    PyGmicType.tp_init = 0;
    PyGmicType.tp_alloc = (allocfunc)PyGmic_alloc;
    PyGmicType.tp_getattro = PyObject_GenericGetAttr;
    PyGmicType.tp_dealloc = (destructor)PyGmic_dealloc;
    PyGmicType.tp_free = (freefunc)PyGmic_free;
    PyGmicType.tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE;

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

    // Numpy input-output matrix conversion presets
    // see from_numpy_array() and to_numpy_array(), as well as their
    // resepective C doc strings. Each preset constant format value is as
    // follows:
    // -'i'(interleaved pixel channels) or 'd'(interleaved pixel channels) - in
    // terms of how the matrix is, when outside G'MIC
    // -'_' separator
    // -'llll' 5-letters axes-permutation* string to be handled to G'MIC's
    // 'permute' command. 'l' can be any of 'x','y','z','c' *Note that a
    // 'permute' string is unique and valid for both conversion directions:
    // from and to numpy or G'MIC.

    // Default: width, depth, height, channels interleaved - same as
    // NUMPY_FORMAT_PIL
    PyModule_AddStringConstant(m, "NUMPY_FORMAT_DEFAULT", "i_xyzc");
    // depth, height, width (ie. no axis swapping); channels NOT interleaved
    PyModule_AddStringConstant(m, "NUMPY_FORMAT_GMIC", "d_xyzc");
    // depth-plane, width-rows, height-cols, channels interleaved
    PyModule_AddStringConstant(m, "NUMPY_FORMAT_SCIKIT_IMAGE", "i_zxyc");
    // depth, height, width, channels interleaved
    PyModule_AddStringConstant(m, "NUMPY_FORMAT_PIL", "i_zyxc");

    return m;
}

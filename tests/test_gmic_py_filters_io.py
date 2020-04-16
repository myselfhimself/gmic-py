# Important: this test suite requires that you have gmic cli executable of the same version as gmic-py in your PATH!
import copy
import filecmp
import json
import random
import os
import urllib.request

import pytest

import gmic

import PIL.Image

"""
This big parameterized test suite helps to compare gmic-cli vs. gmic-py output idempotence of all gui filters for a fixed input.
You should run it nightly or not often, as it is time-consuming.

Any plug-ins, add-ons etc.. relying on gmic-py may want to imitate this strategy and ensure eg. that the UIs they provide
keep yielding the same result as their exposed gmic-py's filters themselves.

This could be coupled with non-regression I/O results (ie. archived sets of fixed parameters and input images -> fixed dated/versioned outputs)
to ensure result stability across versions. Not implementing this for now.
"""

GMIC_IMAGES_DIFFERENCE_PIL_MAX_PERCENT = 10 # If images differ more than 8%, the test is deemed as failing
GMIC_OUTPUT_FILE_EXTENSION = '.png'
GMIC_FILTERS_URL_PATTERN = 'https://gmic.eu/filters{}.json'
GMIC_FILTERS_FILENAME_PATTERN = 'filters{}.json'
GMIC_FILTERS_TEST_BLACKLIST = (
        'gui_download_all_data', # no image output
        'fx_mask_color', # opens X11 display which is blocking
        '_none_', # obvious
        'fx_gmic_demos', # too interactive
        'samj_Ecraser_Etirer_V2', # buggy cli vs. python 1-pixel width error
        'samj_Ecraser_Etirer', # buggy cli vs. python 1-pixel width error
        'samj_Texture_Granuleuse', # 30% image difference between two runs
        'fx_gcd_etch', # 20% image difference between two runs
        'Couleurs_Metalliques_samj_en', # 30% image difference between two runs
        'fx_texture_afre_broken', # unknown y50_afre subcommand
        'fx_shapeism', # 19% image difference
        'Couleurs_Metalliques', # 32% image difference
        'fx_gb_mcfx', # strange syntax error
        'fx_gb_ub', # strange syntax error
        'luminance_nr', # strange parameters error
        'gcd_wiremap', # 39% image difference
        'jeje_deconvolve', # arguments error
        'jpr_line_edges', # 24% image difference
        'nr3', # undefined fft argument 8
        'samj_en_Courtepointe', # needs display
        'samj_Courtepointe', # needs display
        'iain_savenoiseprint', # invalid selection
        'spot_mask', # ian denoise subcommand syntax error
        'fx_boxfitting', # 19% image difference
        'Denim_samj_en', # 29% image difference
        'Denim_samj', # 29% image difference
        'jeje_freqy_pattern', # 40% image difference
        'fx_metalgrain', # 24% image difference
        'samj_Motifs_7200_VarianteC', # 27% image difference
        'samj_Soft_Random_Shades', # 14% image difference
        'fx_pack_sprites', # 29% image difference
        'fx_circle_art', # 27% image difference
        'fx_rorschach', # 27% image difference
        'fx_quick_copyright', # arguments error
        'fx_tk_stereogram', # 10.9% image difference
        'gimp_recolorize_20130115_modifie', # rv range error
        'samj_test_A', # 27% image difference
        'gui_rep_objvf', # variance error
        'fx_fourier_picture_watermark', # buffer selection error
        'fx_vibrato', # invalid selection error
        'samj_reptile_en', # 16% image difference
        'samj_reptile', # 42% image difference
        'fx_charred_plastic', # 368% image difference
        'samj_en_chalkitup', # 11% image difference
        'fx_Squiggly', # 15% image difference
        'samj_Pointillisme', # 34% image difference
        'samj_Contours_Blancs', # 10.3% image difference
        'fx_custom_deformation', # undefined argument 5
        'fx_custom_transform', # undefined argument 3
        'fx_apply_RGBcurve', # missing .dlm file
        'gtutor_blur_img', # invalid selection
        'exfusion', # invalid selection
        'exfusion3', # invalid selection
        'iain_fast_formula', # undefined variable endlocal
        'fx_gb_mp', # unmatching brackets
        'XY_hardsketchbw_samj', # parameter 13 error
        'samj_Motifs_7200_VarianteB', # 11% image difference
        'fx_compose_graphixcolor', # command keep invalid
        'fx_scaledown3', # invalid argument
        'fx_OOBS', # invalid selection
        'red_eye', # 59% image difference
        'samj_test_Dither_Color', # 16% image difference
        'fx_colorsketchbw', # 11% image difference
        'fx_OldSquiggly', # unknown command or filename 6-8
        'jeje_clouds', # 10.6% image difference
        'fx_gcd_crmt_tile', # unknown command or filename string
        'samj_chalkitup', # 11% image difference
        'samj_Scintillements_Colores', # invalid const value
        'fx_rotate_tileable', # invalid image dimensions
        'fx_isolate_tiles', # different cli vs gmicpy image sizes
        )
GMIC_FILTERS_USELESS_PARAMETERS = ('note', 'separator', 'link')
"""
Fields with non-empty "default" attribute:
grep -E '"default": "[^"]+"' filters290.json | grep -Eo '"type": "[^"]+"' | sort | uniq
"type": "bool"
"type": "choice"
"type": "color"
"type": "float"
"type": "int"
"type": "text"
"""
GMIC_FILTERS_SUPPORTED_PARAMETERS = ('int', 'float', 'choice', 'bool', 'color', 'text') # Filters with other types of parameters are unsupported for now
GMIC_FILTERS_ALLOWED_LANG = ('en',) # Skipping 'fr', 'ja' etc
GMIC_FILTERS_RANDOM_SEED = '781123'
GMIC_IMAGES_DIRECTORY = 'test-images'
GMIC_AVAILABLE_INPUT_IMAGES = ["sp " + a for a in "apples | balloons | barbara | boats | bottles | butterfly | cameraman | car | cat | cliff | chick | colorful | david | dog | duck | eagle | elephant | earth | flower | fruits | gmicky | gmicky_mahvin | gmicky_wilber | greece | gummy | house | inside | landscape | leaf | lena | leno | lion | mandrill | monalisa | monkey | parrots | pencils | peppers | portrait0 | portrait1 | portrait2 | portrait3 | portrait4 | portrait5 | portrait6".split(" | ")]
GMIC_FILTERS_WITH_SPECIAL_INPUTS = {
        'afre_halfhalf': {'input_images_count': 2},
        'rep_z_render': {'input_images_count': 3},
        'gui_rep_regm': {'input_images_count': 2},
        'fx_stylize': {'input_images_count': 2}
        }
gmic_instance = gmic.Gmic()
gmic_instance.run('update') # allows more filter to work
os.system("gmic update") # same


def get_images_difference_percent(filename1, filename2):
    # From https://rosettacode.org/wiki/Percentage_difference_between_images
    # Return: value between 0 and 100
    i1 = PIL.Image.open(filename1)
    i2 = PIL.Image.open(filename2)
    assert i1.mode == i2.mode, "Different kinds of images."
    assert i1.size == i2.size, "Different sizes."

    pairs = zip(i1.getdata(), i2.getdata())
    if len(i1.getbands()) == 1:
        # for gray-scale jpegs
        dif = sum(abs(p1-p2) for p1,p2 in pairs)
    else:
        dif = sum(abs(c1-c2) for p1,p2 in pairs for c1,c2 in zip(p1,p2))

    ncomponents = i1.size[0] * i1.size[1] * 3

    return (dif / 255.0 * 100.0) / ncomponents



def get_gmic_filters_json_str():
    gmic_version_suffix = gmic.__version__.replace('.', '')
    json_filename = GMIC_FILTERS_FILENAME_PATTERN.format(gmic_version_suffix)

    # Use filters JSON description file if exists, else download it first from gmic.eu
    if not os.path.exists(json_filename):
        print("downloading json file")
        json_url = GMIC_FILTERS_URL_PATTERN.format(gmic_version_suffix)
        with urllib.request.urlopen(json_url) as response:
            json_str = response.read()
            with open(json_filename, 'wb') as json_file:
                json_file.write(json_str)
    else:
        print("reusing json file")

    with open(json_filename) as json_file:
        json_str = json_file.read()

    return json_str

def is_filter_testable_for_now(filter_dict, already_parsed_filter_commands):
    return filter_dict['lang'] in GMIC_FILTERS_ALLOWED_LANG and filter_dict['command'] not in already_parsed_filter_commands and filter_dict['command'] not in GMIC_FILTERS_TEST_BLACKLIST and is_filter_non_pure_documentation(filter_dict)

def is_filter_non_pure_documentation(filter_dict):
    for parameter in filter_dict['parameters']:
        if parameter['type'] not in GMIC_FILTERS_USELESS_PARAMETERS:
            return True

def get_generated_filter_inputs(filter_dict):
    if filter_dict['command'] in GMIC_FILTERS_WITH_SPECIAL_INPUTS:
        if 'input_images_count' in GMIC_FILTERS_WITH_SPECIAL_INPUTS[filter_dict['command']]:
            return random.sample(GMIC_AVAILABLE_INPUT_IMAGES, GMIC_FILTERS_WITH_SPECIAL_INPUTS[filter_dict['command']]['input_images_count'])
    return [random.choice(GMIC_AVAILABLE_INPUT_IMAGES)]

def get_generated_filter_params(filter_dict):
    generated_parameters_values = []
    for parameter in filter_dict['parameters']:
        parameter_type = parameter['type']
        if parameter_type not in GMIC_FILTERS_USELESS_PARAMETERS:
            if parameter_type not in GMIC_FILTERS_SUPPORTED_PARAMETERS:
                raise NotImplementedError('Filter {}\'s {} parameter ({}) must be of supported type {} for now.'.format(filter_dict['command'], (parameter['name'] if 'name' in parameter else '<unnamed>'), parameter['type'], GMIC_FILTERS_SUPPORTED_PARAMETERS))
            if 'default' in parameter:
                generated_parameters_values.append(parameter['default']) # TODO use fuzzying there?
            else:
                raise NotImplementedError('Filter {}\'s {} parameter ({}) is one of supported type {} but has no "default" value.'.format(filter_dict['command'], (parameter['name'] if 'name' in parameter else '<unnamed>'), parameter['type'], GMIC_FILTERS_SUPPORTED_PARAMETERS))

    return generated_parameters_values

def get_gmic_filters_inputs():
    argvalues = []
    ids = []

    filters_json_str = get_gmic_filters_json_str()
    filters_json_dict = json.loads(filters_json_str)
    for category in filters_json_dict['categories']:
        for filter_dict in category['filters']:
            if is_filter_testable_for_now(filter_dict, ids):
                filter_command = filter_dict['command']
                try:
                    filter_test_params = get_generated_filter_params(filter_dict)
                except NotImplementedError as err:
                    print(err, "Skipped.")
                    continue
                filter_inputs = get_generated_filter_inputs(filter_dict)
                filter_argvalue = (filter_inputs, filter_command, filter_test_params)

                argvalues.append(filter_argvalue)
                ids.append(filter_command)
            else:
                print("Skipped {}. Not testable or is blacklisted.".format(filter_dict['command']))
                continue

    # TODO use an intermediated ordered dict for easy debugging, before generating a list
    # Referring to function parameters of parametrize here: https://docs.pytest.org/en/latest/reference.html#pytest-mark-parametrize
    #return {'argnames': ['filter_id', 'filter_params'], 'argvalues': [('fx_painting', ['3', '3', '3', '200', '0'])], 'ids': ['fx_painting']}
    return {'argnames': ['filter_inputs', 'filter_id', 'filter_params'], 'argvalues': argvalues, 'ids': ids}

# from https://stackoverflow.com/a/15357477/420684
def isfloat(x):
    try:
        a = float(x)
    except ValueError:
        return False
    else:
        return True

def isint(x):
    try:
        a = float(x)
        b = int(a)
    except ValueError:
        return False
    else:
        return a == b

@pytest.mark.xfail
@pytest.mark.parametrize(**get_gmic_filters_inputs())
def test_gmic_filter_io(filter_inputs, filter_id, filter_params):
    global gmic_instance
    print(filter_inputs)
    print(filter_id)
    print(filter_params)

    # Escape parameters before piping them to gmic-py and gmic-cli
    filter_params_cli = copy.copy(filter_params)
    for pos, param in enumerate(filter_params):
        if type(param) is str and not all(isint(param_subelement) or isfloat(param_subelement) for param_subelement in param.split(',')) and not isint(param) and not isfloat(param) and not param.endswith(GMIC_OUTPUT_FILE_EXTENSION):
            filter_params[pos] = '"{}"'.format(param.replace('"','\\"'))
            # One of the worst CLI expression that works thanks to escaping similar to the one below:
            # gmic sp parrots -srand 781123 fx_watermark_fourier \"\(a\) b\'o\\\"nsoir\",53 output[0]  "/home/jd/Productions/GMIC/gmic-py/build/lib.linux-x86_64-3.7/test-images/fx_watermark_fourier_gmiccli.png"
            filter_params_cli[pos] = '\\"{}\\"'.format(param.replace('(', '\\(').replace(')', '\\)').replace("'", "\\'").replace('"','\\\\\\"'))
    gmic_cli_subcommand = "{} -srand {} {} {} output[0] ".format(" ".join(filter_inputs), GMIC_FILTERS_RANDOM_SEED, filter_id, ",".join(filter_params_cli))
    gmic_py_subcommand = "{} -srand {} {} {} output[0] ".format(" ".join(filter_inputs), GMIC_FILTERS_RANDOM_SEED, filter_id, ",".join(filter_params))

    if not os.path.exists(GMIC_IMAGES_DIRECTORY):
        os.mkdir(GMIC_IMAGES_DIRECTORY)

    gmic_py_output_file = os.path.realpath(os.path.join(GMIC_IMAGES_DIRECTORY, "{}_gmicpy{}".format(filter_id, GMIC_OUTPUT_FILE_EXTENSION)))
    gmic_py_command = "{} \"{}\"".format(gmic_py_subcommand, gmic_py_output_file)

    gmic_cli_output_file = os.path.realpath(os.path.join(GMIC_IMAGES_DIRECTORY, "{}_gmiccli{}".format(filter_id, GMIC_OUTPUT_FILE_EXTENSION)))
    gmic_cli_command = "gmic {} \"{}\"".format(gmic_cli_subcommand, gmic_cli_output_file)

    print(gmic_py_command)
    gmic_instance.run(gmic_py_command)

    print(gmic_cli_command)
    os.system(gmic_cli_command)

    # assert output files equality
    assert filecmp.cmp(gmic_py_output_file, gmic_cli_output_file, shallow=False) or get_images_difference_percent(gmic_py_output_file, gmic_cli_output_file) <= GMIC_IMAGES_DIFFERENCE_PIL_MAX_PERCENT

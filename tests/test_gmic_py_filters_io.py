import os
import filecmp
import urllib.request
import json

import pytest

import gmic

GMIC_FILTERS_URL_PATTERN = 'https://gmic.eu/filters{}.json'
GMIC_FILTERS_TEST_BLACKLIST = (
        'gui_download_all_data', #no image output
        'fractalize', #too long
        'fx_mask_color', # opens X11 display which is blocking
        'jeje_turing_pattern' #too long
        )
GMIC_FILTERS_USELESS_PARAMETERS = ('note', 'separator', 'link')
GMIC_FILTERS_SUPPORTED_PARAMETERS = ('int', 'float', 'choice') # Filters with other types of parameters are unsupported for now
GMIC_IMAGES_DIRECTORY = 'test-images'

gmic_instance = gmic.Gmic()
gmic_instance.run('update') # allows more filter to work

"""
This big parameterized test helps to compare gmic-cli vs. gmic-py output idempotence of all gui filters for a fixed input.
You should run it nightly or not often, as it is time-consuming.

Any plug-ins, add-ons etc.. relying on gmic-py may want to imitate this strategy and ensure eg. that the UIs they provide
keep yielding the same result as their exposed gmic-py's filters themselves.

This could be coupled with non-regression I/O results (ie. archived sets of fixed parameters and input images -> fixed dated/versioned outputs)
to ensure result stability across versions. Not implementing this for now.
"""

def get_gmic_filters_json_str():
    json_url = GMIC_FILTERS_URL_PATTERN.format(gmic.__version__.replace('.', ''))
    with urllib.request.urlopen(json_url) as response:
        json_str = response.read().decode('utf-8')

    return json_str

def is_filter_testable_for_now(filter_dict):
    return filter_dict['command'] not in GMIC_FILTERS_TEST_BLACKLIST and is_filter_non_pure_documentation(filter_dict)

def is_filter_non_pure_documentation(filter_dict):
    for parameter in filter_dict['parameters']:
        if parameter['type'] not in GMIC_FILTERS_USELESS_PARAMETERS:
            return True

def get_generated_filter_params(filter_dict):
    generated_parameters_values = []
    for parameter in filter_dict['parameters']:
        parameter_type = parameter['type']
        if parameter_type not in GMIC_FILTERS_USELESS_PARAMETERS:
            if parameter_type not in GMIC_FILTERS_SUPPORTED_PARAMETERS:
                raise NotImplementedError('Filter {}\'s {} parameter ({}) must be of supported type {} for now.'.format(filter_dict['command'], (parameter['name'] if 'name' in parameter else '<unnamed>'), parameter['type'], GMIC_FILTERS_SUPPORTED_PARAMETERS))
            if 'default' in parameter: # parameter_type == 'int':
                generated_parameters_values.append(parameter['default']) # TODO use fuzzying there?

    return generated_parameters_values

def get_gmic_filters_inputs():
    argvalues = []
    ids = []

    filters_json_str = get_gmic_filters_json_str()
    filters_json_dict = json.loads(filters_json_str)
    for category in filters_json_dict['categories']:
        for filter_dict in category['filters']:
            if is_filter_testable_for_now(filter_dict):
                filter_command = filter_dict['command']
                try:
                    filter_test_params = get_generated_filter_params(filter_dict)
                except NotImplementedError as err:
                    print(err, "Skipped.")
                    continue
                filter_argvalue = (filter_command, filter_test_params)

                argvalues.append(filter_argvalue)
                ids.append(filter_command)
            else:
                print("Skipped {}. Not testable or is blacklisted.".format(filter_dict['command']))
                continue

    # TODO use an intermediated ordered dict for easy debugging, before generating a list
    # Referring to function parameters of parametrize here: https://docs.pytest.org/en/latest/reference.html#pytest-mark-parametrize 
    #return {'argnames': ['filter_id', 'filter_params'], 'argvalues': [('fx_painting', ['3', '3', '3', '200', '0'])], 'ids': ['fx_painting']}
    return {'argnames': ['filter_id', 'filter_params'], 'argvalues': argvalues, 'ids': ids}


@pytest.mark.parametrize(**get_gmic_filters_inputs())
def test_gmic_filter_io(filter_id, filter_params):
    global gmic_instance
    print(filter_id)
    print(filter_params)
    gmic_command = "sp leno {} {} output ".format(filter_id, ",".join(filter_params))

    if not os.path.exists(GMIC_IMAGES_DIRECTORY):
        os.mkdir(GMIC_IMAGES_DIRECTORY)

    gmic_py_output_file = os.path.realpath(os.path.join(GMIC_IMAGES_DIRECTORY, "{}_gmicpy.png".format(filter_id)))
    gmic_py_command = gmic_command + gmic_py_output_file

    gmic_cli_output_file = os.path.realpath(os.path.join(GMIC_IMAGES_DIRECTORY, "{}_gmiccli.png".format(filter_id)))
    gmic_cli_command = "gmic " + gmic_command + gmic_cli_output_file

    print(gmic_py_command)
    gmic_instance.run(gmic_py_command)

    print(gmic_cli_command)
    os.system(gmic_cli_command)
    
    # assert output files equality
    assert filecmp.cmp(gmic_py_output_file, gmic_cli_output_file, shallow=False)

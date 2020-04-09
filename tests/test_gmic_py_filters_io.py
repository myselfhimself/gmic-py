import os
import filecmp

import pytest

import gmic


gmic_instance = gmic.Gmic()

"""
This big parameterized test helps to compare gmic-cli vs. gmic-py output idempotence of all gui filters for a fixed input.
You should run it nightly or not often, as it is time-consuming.

Any plug-ins, add-ons etc.. relying on gmic-py may want to imitate this strategy and ensure eg. that the UIs they provide
keep yielding the same result as their exposed gmic-py's filters themselves.

This could be coupled with non-regression I/O results (ie. archived sets of fixed parameters and input images -> fixed dated/versioned outputs)
to ensure result stability across versions. Not implementing this for now.
"""

def get_gmic_filters_inputs():
    # TODO Grab the GUI filters JSON
    # TODO Iterate over them and generate calling parameters
    # TODO make something dynamic
    # TODO add parameters fuzzing in accepted ranges?
    # TODO use an intermediated ordered dict for easy debugging, before generating a list
    # Referring to function parameters of parametrize here: https://docs.pytest.org/en/latest/reference.html#pytest-mark-parametrize 
    # TODO build this in a nice for loop
    return {'argnames': ['filter_id', 'filter_params'], 'argvalues': [('fx_painting', ['3', '3', '3', '200', '0'])], 'ids': ['fx_painting']}


@pytest.mark.parametrize(**get_gmic_filters_inputs())
def test_gmic_filter_io(filter_id, filter_params):
    global gmic_instance
    print(filter_id)
    print(filter_params)
    gmic_command = "{} {} output ".format(filter_id, ",".join(filter_params))
    gmic_py_output_file = os.path.realpath("out_gmicpy.png")
    gmic_py_command = gmic_command + gmic_py_output_file

    gmic_cli_output_file = os.path.realpath("out_gmiccli.png")
    gmic_cli_command = "gmic " + gmic_command + gmic_cli_output_file

    print(gmic_py_command)
    gmic_instance.run(gmic_py_command)

    print(gmic_cli_command)
    os.system(gmic_cli_command)
    
    # assert output files equality
    filecmp.cmp(gmic_py_output_file, gmic_cli_output_file, shallow=False)

    # clean generated files
    os.unlink(gmic_py_output_file)
    os.unlink(gmic_cli_output_file)

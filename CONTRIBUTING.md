Hello fellow developer!
Here is some help for working on the project :)

# Cleaning, Formatting, Building and Testing
- the gmic-py binding is super skinny and consists in files `gmicpy.cpp`, `gmicpy.h` and `setup.py` mostly. Pytest test cases belong in the `tests/` directory.
- no specific IDE was used to build the code, sometimes vim, gedit, pycharm etc
- note that for C/C++ debugging of an imported gmic-py module, you can use `gdb python` and try to understand where your segfault happened, or you run a debug session in CLion (or another C/C++ editor) and attach to the most freshly run python interpreter.
- Run `bash build_tools.bash` (on Linux) for listing commands to work with the project. The most useful ones for everyday work are the following and require no additional parameter to start:
  - `1_clean_and_regrab_gmic_src` which depends especially on the version number you put in the `VERSION` file. This cleans your libgmic sources and downloads them again.
  - `2_compile` compiles gmic-py with production-grade optimization for you, you might want to run this step in a python3 virtual environment with `dev-requirements.txt` loaded (using `pip install -r dev-req..`)
  - `2b_compile_debug` same but much faster, without optimization and with debug symbols included
  - `20_reformat_all` reformats both Python and C/C++ code. This is necessary because the Github Action worfklows will crash if any of your is not formatted the same way.
  - `3_test_compiled_so` (you can add a part of a pytest test case name after for filtering): runs all pytest test cases
- If your computer lacks power or tools, do not worry too much, you can rely on the Github Actions jobs, run after each commit. Remember that myselfhimself has developed a part of this project on a smartphone only in Prague's Technical University's library, using Github's in-browser file edit pen functionality and no compiler installed :)
- In day-to-day development, building wheels and building manylinux wheels through docker is not usual, despite the existence of `build_tools.bash` commands for this, only through automated online Github Actions.
- For more usage on how to use those commands, look at their respective code or read the `.github/workflows/` files.

# Working day-by-day without releasing
- releases are not triggered automatically unless you git-push a tag starting with v
- if you want test build jobs locally for own OS and Linux, you may want to use [nektos/act](https://github.com/nektos/act) leveraging the `.actrc` file in the repository's root directory. This is not necessary but may save you some troubleshooting headache when Github Actions' bots have strange configuration issues.
- Otherwise, just push your code online and watch the builds turn green :)

# Releasing a new version to Pypi.org
- edit the VERSION file and put your new version number, make sure you have no endline or trailing space at all
- create a Git tab named "v[your version]"
- git push your tag
- the builds that are sensible to `v*` tags will trigger in addition to the regular ones, make sure all turns green :)

# Writing documentation
- Offline Pythonic documentation: function/class parameters: for now no Python C Argument Clinic documentation has been written to help document parameters, especially as it needs a third-party build tool obviously. Basic pythonic `help()` support for most module-level types has been written though, with examples. If the binding were written in eg. Pybind11, fine-grain documentation would be easier.
- An online user-friendly documentation is hosted and updated automatically for every Git push at [gmic-py.readthedocs.io](https://gmic-py.readthedocs.io). It is in sync with the master branch and the `docs/` directory. The readthedocs.io documentation is managed through myselfhimself's account (ie. the current Github repository manager's account), on [readthedocs.io](https://readthedocs.io). Build statuses for each Git push can be monitored and this may help in troubleshooting formatting or docs configuration files errors.

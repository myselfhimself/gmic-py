Hello fellow developer!
Here is some help for working on the project :)

# Disambiguation
- G'MIC is the name of the C++ framework and language altogether.
- `gmic` is the name of both the Github project and CLI executable.
- `gmic-py` is the project name for the G'MIC Python binding, though its Python module (or package name) is just `gmic`
- thus we do not `import gmic_py` but `import gmic`.

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

# Writing & generating documentation
## Generating offline documentation
- The project's documentation lies in the `docs/` directory, which is a Sphinx project formatted in ReST, intended for HTML rendering only.
- In order to build the documentation, you might want to create a dedicated Python 3.7+ environment and run `pip install -r docs/requirements.txt`, then run `make html` within the `docs/` directory.
  - The `gmicpy.cpp` binding code has `_doc` Pythonic variables for documenting in [Napoleon Google Style](https://github.com/sphinx-contrib/napoleon#google-vs-numpy) for parsing by Sphinx Apidoc
  - `gmic.rst` contains the API Reference for `gmicpy.cpp` and is generated on the fly by parsing the virtual environment's installed `gmic` module's objects (most probably a robots scraps the `__doc__` attributes)
    - `gmic.rst` contains API-generating macros and was generated once for all using a command similar to: `sphinx-apidoc -o . ../build/lib.linux-x86_64-3.7/ -f` from `docs/`, with `sphinx-apidoc` looking up the freshest `gmic-py` compiled module
    - the html static webpage for `gmic.rst` has its detailed contents macros run thanks to the `gmic` module installed in your virtual environment, this is different than the `sphinx-apidoc` command just before, which uses a module directory path
        - in order to render `gmic.rst` to HTML locally to reflect your current C code, you must:
            - make sure `gmicpy.cpp` has had the reformatting pass by clang-format
            - compile the `gmic` module if not done (eg. in debug mode for a shortest compilation time)
            - generate a `.whl` file
            - uninstall your current `gmic` module if installed, install the `gmic` wheel
            - touch `gmic.rst` to make it feel changed to the `sphinx` generating command
            - run `make html` in `docs/`
            - in short, eg. on a Python37 environment targetting gmic 2.9.0, you can run this one-liner:
            ```sh
            bash build_tools.bash 6_make_full_doc
            # or without recompilation:
            bash build_tools.bash 6b_make_doc_without_c_recompilation
            ```
  - the rest of the `.rst` files are static but may use the home-made [gmic-sphinx directive](https://github.com/myselfhimself/gmic-sphinx)
  - viewing the generated documentation can be done with eg. `firefox _build/html/index.html` (this is a plain static website).

## Generating online documentation and `readthedocs.io` hosting:
- The project documentation (API reference+regular pages) is hosted and updated automatically for every Git push at [gmic-py.readthedocs.io](https://gmic-py.readthedocs.io). It is in sync with the master branch and the `docs/` directory.
- Note that the API Reference page is generated at build time within the `readthedocs.io` online pipeline and it depends on `pypi.org`'s latest `gmic` (so not the repository master `gmic` module). To have this page updated online, you should push a new release to pypi.org (ie. git tag push) :)
- The `readthedocs.io` documentation is managed through myselfhimself's account (ie. the current Github repository manager's account), on [readthedocs.io](https://readthedocs.io).
- Build statuses for each Git push can be monitored on `readthedocs.io` and this may help in troubleshooting formatting or docs configuration files errors.
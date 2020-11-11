#!/usr/bin/env python

import os
import sys
import shutil
import hashlib
import zipfile
import argparse
import tempfile
from collections import defaultdict

import pefile
from machomachomangler.pe import redll


def hash_filename(filepath, blocksize=65536):
    hasher = hashlib.sha256()

    with open(filepath, "rb") as afile:
        buf = afile.read(blocksize)
        while len(buf) > 0:
            hasher.update(buf)
            buf = afile.read(blocksize)

    root, ext = os.path.splitext(filepath)
    return f"{os.path.basename(root)}-{hasher.hexdigest()[:8]}{ext}"


def find_dll_dependencies(dll_filepath, vcpkg_bin_dir):
    pe = pefile.PE(dll_filepath)

    for entry in pe.DIRECTORY_ENTRY_IMPORT:
        entry_name = entry.dll.decode("utf-8")
        print("debug: attempting to find", entry, entry.dll, entry.imports, entry.struct, "in", vcpkg_bin_dir)
        if entry_name in os.listdir(vcpkg_bin_dir):
            dll_dependencies[os.path.basename(dll_filepath)].add(entry_name)
            _dll_filepath = os.path.join(vcpkg_bin_dir, entry_name)
            find_dll_dependencies(_dll_filepath, vcpkg_bin_dir)


def mangle_filename(old_filename, new_filename, mapping):
    with open(old_filename, "rb") as f:
        buf = f.read()

    try:
        new_buf = redll(buf, mapping)
        print("Building mangle filename mapping and redll:", old_filename, new_filename, mapping)

        with open(new_filename, "wb") as f:
            f.write(new_buf)
    except ValueError:
        print("Unsolvable machomangler buffer length error. Skipping mangling of:", old_filename)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Vendor in external shared library dependencies of a wheel."
    )
    
    parser.add_argument("WHEEL_FILE", type=str, help="Path to wheel file")
    parser.add_argument(
        "-d", "--dll-dir", dest="DLL_DIR", type=str, help="Directory to find the DLLs"
    )
    parser.add_argument(
        "-w",
        "--wheel-dir",
        dest="WHEEL_DIR",
        type=str,
        help=('Directory to store delocated wheels (default: "wheelhouse/")'),
        default="wheelhouse/",
    )
    
    args = parser.parse_args()
    
    wheel_name = os.path.basename(args.WHEEL_FILE)
    package_name = wheel_name.split("-")[0]
    repaired_wheel = os.path.join(args.WHEEL_DIR, wheel_name)
    
    old_wheel_dir = tempfile.mkdtemp()
    new_wheel_dir = tempfile.mkdtemp()
    
    with zipfile.ZipFile(args.WHEEL_FILE, "r") as wheel:
        wheel.extractall(old_wheel_dir)
        print("showing old_wheel_dir contents")
        print(os.listdir(old_wheel_dir))
        print("attempting stat of old_wheel_dir:", old_wheel_dir)
        os.stat(old_wheel_dir)
        wheel.extractall(new_wheel_dir)
        pe_path = list(filter(lambda x: x.endswith((".pyd", ".dll")), wheel.namelist()))[0]
        print("debug: pe_path is:", pe_path)
        #tmp_pe_path = os.path.join(old_wheel_dir, package_name, os.path.basename(pe_path))
        # add dll recursive autodetection
        tmp_pe_path = os.path.join(old_wheel_dir, os.path.basename(pe_path))
        print("debug: tmp_pe_path is:", tmp_pe_path)
    
    # https://docs.python.org/3/library/platform.html#platform.architecture
    x = "x64" if sys.maxsize > 2**32 else "x86"
    # set VCPKG_INSTALLATION_ROOT=C:\dev\vcpkg
    #dll_dir = os.path.join(os.environ["VCPKG_INSTALLATION_ROOT"], "installed", f"{x}-windows", "bin")

    dll_dir = args.DLL_DIR
    if not dll_dir and os.environ["VCPKG_INSTALLATION_ROOT"]:
        # https://docs.python.org/3/library/platform.html#platform.architecture
        #dll_dir = os.path.join(os.environ["VCPKG_INSTALLATION_ROOT"], "installed", f"{x}-windows", "bin")
        x = "x64" if sys.maxsize > 2**32 else "x86"
        # set VCPKG_INSTALLATION_ROOT=C:\dev\vcpkg

    print("debug: dll_dir (lookup directory) is:", dll_dir)
    
    dll_dependencies = defaultdict(set)
    find_dll_dependencies(tmp_pe_path, dll_dir)
    print("dll_dependencies found:", dll_dependencies)


    new_wheel_libs_dir = os.path.join(new_wheel_dir, package_name)
    os.makedirs(new_wheel_dir, exist_ok=True)
    
    for dll, dependencies in dll_dependencies.items():
        print("about to mangle:", dll)
        mapping = {}
    
        for dep in dependencies:
            print("about to hash:",os.path.join(dll_dir, dep))
            hashed_name = hash_filename(os.path.join(dll_dir, dep))  # already basename
            mapping[dep.encode("ascii")] = hashed_name.encode("ascii")
            shutil.copy(
                os.path.join(dll_dir, dep),
                os.path.join(new_wheel_libs_dir, hashed_name),
            )
    
        if dll == pe_path:
            # skip mangling module's portable executable itself
            continue
        elif dll.endswith(".pyd"):
            old_name = os.path.join(
                new_wheel_libs_dir, os.path.basename(tmp_pe_path)
            )
            new_name = os.path.join(
                new_wheel_libs_dir, os.path.basename(tmp_pe_path)
            )
        elif dll.endswith(".dll"):
            old_name = os.path.join(dll_dir, dll)
            print("about to hash:",os.path.join(dll_dir, dll))
            hashed_name = hash_filename(os.path.join(dll_dir, dll))  # already basename
            new_name = os.path.join(new_wheel_libs_dir, hashed_name)
    
        mangle_filename(old_name, new_name, mapping)
    
    with zipfile.ZipFile(repaired_wheel, "w", zipfile.ZIP_DEFLATED) as new_wheel:
        for root, dirs, files in os.walk(new_wheel_dir):
            for file in files:
                print("new wheel copying:", os.path.join(root, file), os.path.join(os.path.basename(root), file))
                new_wheel.write(
                    os.path.join(root, file), os.path.join(os.path.basename(root), file)
                )

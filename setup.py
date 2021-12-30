import sys
import setuptools
import codecs
import os
import re

with open("README.md", "r", encoding='utf-8') as fh:
    long_description = fh.read()
packages = setuptools.find_namespace_packages(include=["pyrallis*"])
print("PACKAGES FOUND:", packages)
print(sys.version_info)

def find_version(*file_paths: str) -> str:
    with codecs.open(os.path.join(*file_paths), "r") as fp:
        version_file = fp.read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

setuptools.setup(
    name="pyrallis",
    version=find_version("pyrallis", "__init__.py"),
    author="Elad Richardson",
    description="A framework for simple dataclass-based configurations.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://eladrich.github.io/pyrallis/",
    packages=packages,
    package_data={"pyrallis": ["py.typed"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "typing_inspect",
        "dataclasses;python_version<'3.7'",
        'pyyaml'
    ],
    setup_requires=["pre-commit"],
)

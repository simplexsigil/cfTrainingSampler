import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="cfwrapper",
    version="0.0.1",
    author="Tino Fuhrmann",
    author_email="tino-fuhrmann@web.de",
    description="Some base classes for communication with zmq",
    long_description="",
    long_description_content_type="text/markdown",
    url="",
    packages=setuptools.find_packages(),
    classifiers=(
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ),
)
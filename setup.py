import setuptools
import os


with open("README.md", "r") as f:
    readme = f.read()

with open('LICENSE', "r") as f:
    license = f.read()


setuptools.setup(
    name="svd2py",
    author="Gembcior",
    author_email="gembcior@gmail.com",
    description="Converter CMSIS SVD file format to python data structures",
    url="https://github.com/gembcior/cmsis-svd",
    license=license,
    long_description=readme,
    long_description_content_type="text/markdown",
    classifiers=[
        "License :: MIT",
        "Operating System :: Unix",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 3",
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    python_requires='>=3.6',
    setup_requires=['setuptools_scm'],
    install_requires=[
    ],
    extras_require={
        'tests': [
            'pyyaml',
            'pytest',
            'pytest-sugar'
            'pytest-cov'
            'pytest-clarity'
        ],
    },
    use_scm_version=True,
    include_package_data=True,
    packages=setuptools.find_packages('src'),
    package_dir={'': 'src'},
)

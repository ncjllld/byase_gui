import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="byase-gui",
    version="1.0.3",
    author="Lili Dong",
    author_email="ncjllld@hit.edu.cn",
    description="A GUI tool for BYASE software.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ncjllld/byase_gui",
    packages=setuptools.find_packages(),
    include_package_data=True,
    install_requires=[
        'byase',
        'psutil',
        'wxPython'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    entry_points={
        'console_scripts': [
            'byase-gui=byase_gui.gui:main'],
    },
)

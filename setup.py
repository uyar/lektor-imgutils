from pathlib import Path

from setuptools import setup


readme = Path("README.rst").read_text()

setup(
    name="lektor-imgutils",
    version="0.1",
    description="Image handling utilities for Lektor.",
    long_description=readme,
    url="https://github.com/uyar/lektor-imgutils",
    author="H. Turgut Uyar",
    author_email="uyar@tekir.org",
    license="MIT",
    keywords=["lektor", "plugin", "image", "responsive", "srcset", "picture"],
    classifiers=[
        "Framework :: Lektor",
        "Environment :: Plugins",
    ],
    install_requires=["beautifulsoup4", "pillow"],
    py_modules=["lektor_imgutils"],
    entry_points={
        "lektor.plugins": [
            "imgutils = lektor_imgutils:ImgUtilsPlugin",
        ]
    }
)

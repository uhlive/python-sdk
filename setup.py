from setuptools import find_packages, setup

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="uhlive",
    version="1.5.1",
    url="https://github.com/uhlive/python-sdk",
    author="Allo-Media",
    author_email="support@allo-media.fr",
    description="Python bindings for the Uh!ive APIs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Intended Audience :: Developers",
        "Operating System :: POSIX :: Linux",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    extras_require={
        "examples": ["websocket-client", "requests", "aiohttp", "sounddevice", "toml"]
    },
    python_requires=">=3.7",
)

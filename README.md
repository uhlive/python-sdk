# Uh!ive Python SDK

The Uh!live Python SDK provides convenient access to the Uh!live API from
applications written in the Python language.

Read the [full documentation](https://python-uhlive-sdk.netlify.app/).


## Installation from source

This project uses [`uv`](https://docs.astral.sh/uv/).

`uv sync --all-extras`

## Installation from Pypi

```
pip install uhlive
```

or as a dependency to a project managed by `uv`:

```
uv add uhlive
```

## Tools

If you have [`just`](https://just.systems/man/en/) and `uv` installed, you have a convenient way to run the tooling.
Otherwise, you can run the commands in the `justfile` manually.

### Format the sources

```
just format
```

Will run `isort` & `black`

### Lint the sources

```
just lint
```

Will run `ruff` & `mypy`

### Run the tests

```
just test
```

### Compile the docs to html

```
just docs
```

### Run format, lint and tests in one go

```
just
```

Contrary to `tox`, it will stop at the first error. So that we're not drown in (duplicate) error messages.

## Usage

See the `README.md` in each of the example folders.

### Audio files

To play with the examples, you should have a raw audio file.
This raw audio file should be in the proper format. This can be done
using a source audio file in wav format using the following command:
```
sox audio_file.wav  -t raw -c 1 -b 16 -r 8k -e signed-integer audio_file.raw
```

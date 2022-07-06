# Uh!ive Python SDK

The Uh!live Python SDK provides convenient access to the Uh!live API from
applications written in the Python language.

Read the [documentation for the Conversation API](https://docs.allo-media.net/live-api/) and [for the Recognition API (vocal bot toolkit)](https://docs.allo-media.net/stream-api-bots/).

## Requirements

### Installation from source

Install with `pip install .[examples]` to install the the library and all the dependencies necessary to run the examples.

### Audio files

To play with the examples, you should have a raw audio file.
This raw audio file should be in the proper format. This can be done
using a source audio file in wav format using the following command:
```
sox audio_file.wav  -t raw -c 1 -b 16 -r 8k -e signed-integer audio_file.raw
```

## Usage

See the `README.md` in each of the example folders.

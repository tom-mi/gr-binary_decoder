# gr-binary_decoder

Decode simple binary signals encoded with OOK, PPM etc.

These are simple, easy-to-use blocks that help decoding simple binary signals as emitted from temperature sensors,
remote controls or similar. They might not be the most sophisticated implementations, but they also don't require
deep knowledge in signal processing to be configured and used.

I wrote them while learning GnuRadio, to get from "decoding by eyeball" as suggested in many tutorials
to a simple, but working end-to-end decoder.

## Prerequisites

- Python 3.8
- Gnuradio 3.8.0.0 (<- tested with, might work with older versions though)

## Installation

```
git clone https://github.com/tom-mi/gr-binary_decoder
cd gr-binary_decoder
mkdir build
cd build
cmake ..
make
sudo make install
```

## Usage

### Block overview

#### Binary DPPM Decoder

Decodes differential [pulse position modulation](https://en.wikipedia.org/wiki/Pulse-position_modulation)
(aka pulse _pause_ modulation).

#### Binary Message Debug Sink

Prints [gnuradio messages](https://wiki.gnuradio.org/index.php/Message_Passing) to stdout.
Different representations for arbitrary PMT data can be chosen. Especially useful for PDUs with binary payload.

#### Binary Message Processor

This block has the same purpose as _Python Block_ from _Core_, but with less boilerplate.
It takes a message, (optionally) decodes it to python data structures, and runs a small custom python snippet
configured by the user to return 0, 1 or multiple messages as output.

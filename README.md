Some simple code to aggregate an image stack (average, median, absolute average deviation, standard error).
There are transparency-aware versions of most routines.
The `imagestack.py` module is generally useful for image stack processing,
and automates tiling and reassembling an image stack that is too large to fit in memory.

## Dependencies

* Python >= 2.6 and < 3
* PIL (Python Image Library)
* numpy

---

## Troubleshooting

### `import Image` fails

Following http://jaredforsyth.com/blog/2010/apr/28/accessinit-hash-collision-3-both-1-and-1/
add the following lines at the top of `helpers.py`:

    import sys
    import PIL.Image
    sys.modules['Image'] = PIL.Image

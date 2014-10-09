#!/usr/local/bin/python2.7

from numpy import *
from imagestack import *

import sys

def usage():
    print >> sys.stderr, 'Usage:', sys.argv[0], '[--convert L|RGB|RGBA (default: RGB)] [--size-mismatch skip|error|crop-upperleft (default: error)] path/to/image1 path/to/image2 [... path/to/imageN] path/to/output'
    sys.exit(-1)

argv = list( sys.argv[1:] )

convert = 'RGB'
try:
    i = argv.index( '--convert' )
    convert = argv[ i + 1 ]
    del argv[ i : i + 2 ]
except IndexError: usage()
except ValueError: pass

size_mismatch = 'error'
try:
    i = argv.index( '--size-mismatch' )
    size_mismatch = argv[ i + 1 ]
    del argv[ i : i + 2 ]
except IndexError: usage()
except ValueError: pass

if len( argv ) < 3:
    usage()

filenames = argv[:-1]
outname = argv[-1]

stack = image_stack_from_filenames( filenames, size_mismatch_behavior = size_mismatch, convert = convert )

avg = average( stack, axis = 0 )
variance = average( ( stack - avg[newaxis,...] )**2, axis = 0 )
stddev = sqrt( variance )

## Use one minus so that the darker the color, the more it could change.
arr2img( 1. - stddev ).save( outname )
print '[Saved "%s"]' % ( outname, )

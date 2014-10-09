#!/usr/local/bin/python2.7

from numpy import *
from helpers import *

import os, sys

def usage():
    print >> sys.stderr, 'Usage:', sys.argv[0], 'path/to/RGBA-image path/to/output'
    sys.exit(-1)

argv = list( sys.argv[1:] )

if len( argv ) != 2:
    usage()

filename = argv[0]
outname = argv[1]

if os.path.exists( outname ):
    print >> sys.stderr, 'ERROR: Output file exists, will not clobber:', outname
    usage()

stack = image_stack_from_filenames( [filename], convert = 'RGBA' )
## Squeeze out the first dimension.
stack = stack.squeeze()
## The result should be three dimensional (rows x cols x RGBA).
assert len( stack.shape ) == 3
## len( RGBA ) == 4
assert stack.shape[2] == 4

'''
M present values
N total values
alpha channel = M/N

red channel (mixed with black) = sum of present red / N = (sum of present red + 0*(N-M)) / N

red channel (mixed with white) = (sum of present red + 1*(N-M)) / N
                               = sum of present red / N + 1*(N-M) / N
                               = red channel (mixed with black) + (N/N-M/N)
                               = red channel (mixed with black) + (1-alpha channel)

alpha channel (mixed with white) = alpha channel + (1-alpha channel) = 1
'''
mixed_with_white = stack + (1-stack[:,:,3])[...,newaxis]
## Drop the alpha channel, since it is all 1's.
assert allclose( mixed_with_white[:,:,3], 1. )
mixed_with_white = mixed_with_white[:,:,:3]

arr2img( mixed_with_white ).save( outname )
print '[Saved "%s"]' % ( outname, )

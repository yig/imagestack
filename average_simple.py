#!/usr/local/bin/python2.7

import Image
from numpy import *

import sys

def usage():
    print >> sys.stderr, 'Usage:', sys.argv[0], 'path/to/image1 path/to/image2 [... path/to/imageN] path/to/output'
    sys.exit(-1)

if len( sys.argv ) < 4:
    usage()

filenames = sys.argv[1:-1]
outname = sys.argv[-1]

num = 0
avg = None

for fname in filenames:
    print 'Averaging with "%s"' % ( fname, )
    img = Image.open( fname ).convert( 'RGBA' )
    arr = asarray( img, dtype = uint8 ) / 255.
    
    if avg is None:
        avg = zeros( arr.shape, dtype = float )
    
    if avg.shape != arr.shape:
        print 'Error! Image has a different shape.  Skipping.'
        continue
    
    avg += arr
    num += 1

avg /= num

def arr2img( arr ):
    assert arr.dtype in ( float32, float64, float )
    return Image.fromarray( asarray( ( arr * 255 ).clip( 0, 255 ), dtype = uint8 ) )

arr2img( avg ).save( outname )
print '[Saved "%s"]' % ( outname, )

#!/usr/local/bin/python2.7

from numpy import *
from helpers import *

import os, sys

def usage():
    print >> sys.stderr, 'Usage:', sys.argv[0], '[--tile pixel_rows/pixel_columns] [--convert L|RGB|RGBA (default: RGB)] [--size-mismatch skip|error|crop-upperleft (default: error)] path/to/image1 [path/to/image2 ... path/to/imageN] path/to/output'
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

tile = None
try:
    i = argv.index( '--tile' )
    tile = argv[ i + 1 ]
    del argv[ i : i + 2 ]
except IndexError: usage()
except ValueError: pass

if len( argv ) < 2:
    usage()

filenames = argv[:-1]
outname = argv[-1]

if os.path.exists( outname ):
    print >> sys.stderr, 'ERROR: Output file exists, will not clobber:', outname
    usage()

if tile is not None:
    if tile == 'auto':
        ## Let's use a maximum of 1 GB of RAM for a stack.
        ## Let N be the number of images.
        ## Let M be the amount of memory each image should contribute: 1 GB / N.
        ## Assuming square floating-point-with-double-precision RGBA images (4*8 bytes per pixel),
        ## and the need to make a copy of all image data (another factor of 2),
        ## tiles' pixel edge lengths should be sqrt( 1 GB / (N*4*8) ).
        pixel_edge_length = max( int( sqrt( float( 1024*1024*1024 ) / ( len( filenames ) * 4*8 * 2 ) ) ), 1 )
        print 'Automatic tiling with tiles of size:', pixel_edge_length, 'by', pixel_edge_length
        tile = '%d/%d' % ( pixel_edge_length, pixel_edge_length )
    
    try:
        tile = tuple([ int( val ) for val in tile.split('/') ])
        assert len( tile ) == 2
        assert tile[0] > 0
        assert tile[1] > 0
    except:
        usage()

def process_image_stack( stack ):
    med = median( stack, axis = 0 )
    return med

# result = process_image_stack( image_stack_from_filenames( filenames, size_mismatch_behavior = size_mismatch, convert = convert ) )
result = process_tiled_image_stack_from_filenames( process_image_stack, tile, filenames, size_mismatch_behavior = size_mismatch, convert = convert )

arr2img( result ).save( outname )
print '[Saved "%s"]' % ( outname, )

#!/usr/local/bin/python2.7

from numpy import *
from imagestack import *

import os, sys

def usage():
    print >> sys.stderr, 'Usage:', sys.argv[0], '[--tile pixel_rows/pixel_columns] [--convert L|RGB|RGBA (default: RGB)] [--size-mismatch skip|error|crop-upperleft (default: error)] [--glob] path/to/image1 [path/to/image2 ... path/to/imageN] path/to/output'
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

glob_filenames = False
try:
    i = argv.index( '--glob' )
    glob_filenames = True
    del argv[ i ]
except ValueError: pass

if len( argv ) < 2:
    usage()

filenames = argv[:-1]
outname = argv[-1]

if glob_filenames:
    from glob import glob
    from itertools import chain
    filenames = list( chain( *[ glob( fname ) for fname in filenames ] ) )

if os.path.exists( outname ):
    print >> sys.stderr, 'ERROR: Output file exists, will not clobber:', outname
    usage()

if tile is not None:
    if tile == 'auto':
        tile = tile_parameter_for_1GB( len( filenames ), GB = 1, size_mismatch_behavior = size_mismatch, convert = convert )
    
    try:
        tile = tuple([ int( val ) for val in tile.split('/') ])
        assert len( tile ) == 2
        assert tile[0] > 0
        assert tile[1] > 0
    except:
        usage()

def process_image_stack( stack ):
    avg = average( stack, axis = 0 )
    return avg

# result = process_image_stack( image_stack_from_filenames( filenames, size_mismatch_behavior = size_mismatch, convert = convert ) )
result = process_tiled_image_stack_from_filenames( process_image_stack, tile, filenames, size_mismatch_behavior = size_mismatch, convert = convert )

arr2img( result ).save( outname )
print '[Saved "%s"]' % ( outname, )

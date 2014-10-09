#!/usr/local/bin/python2.7

from numpy import *
from imagestack import *

import os, sys

def usage():
    print >> sys.stderr, 'Usage:', sys.argv[0], '[--tile pixel_rows/pixel_columns] [--size-mismatch skip|error|crop-upperleft (default: error)] path/to/image1 [path/to/image2 ... path/to/imageN] path/to/output'
    sys.exit(-1)

argv = list( sys.argv[1:] )

## We have to have alpha, so convert must be RGBA.
convert = 'RGBA'

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
        ## and the need for an additional 8*(4*N)^2 of memory,
        ## tiles' pixel edge lengths should be sqrt( 1 GB / (N*4*8) ).
        pixel_edge_length = max( int( sqrt( float( 1024*1024*1024 - 8*(4*len( filenames ))**2 ) / ( len( filenames ) * 4*8 * 2 ) ) ), 1 )
        print 'Automatic tiling with tiles of size:', pixel_edge_length, 'by', pixel_edge_length
        tile = '%d/%d' % ( pixel_edge_length, pixel_edge_length )
    
    try:
        tile = tuple([ int( val ) for val in tile.split('/') ])
        assert len( tile ) == 2
        assert tile[0] > 0
        assert tile[1] > 0
    except:
        usage()

def median_spatial( points ):
    '''
    Given a sequence of K-dimensional 'points',
    return the element of 'points' whose total L1 distance to every other point is minimal.
    
    from: ~/Work/rutgerscolumbia/crowdavg/drawing/general/smileys1/data-and-analysis/average_helper.py
    '''
    
    stack = asarray( points )
    allDistSqrs = ( (stack[newaxis,...] - stack[:,newaxis,:])**2 ).sum(-1)
    ## It should be N-by-N, where N is the number of data points.
    assert allDistSqrs.shape == ( len( stack ), len( stack ) )
    ## It should be symmetric.
    assert abs(allDistSqrs-allDistSqrs.T).max() < 1e-12
    ## The spatial median takes the point whose total distance to all other points is smallest.
    closest = argmin( sqrt( allDistSqrs ).sum( axis = 0 ) )
    return stack[ closest ]

def process_image_stack( stack ):
    assert stack.shape[-1] == 4
    
    out = zeros( stack[0].shape, stack[0].dtype )
    assert out.shape[2] == 4
    
    num_existing = []
    for r in xrange( out.shape[0] ):
        for c in xrange( out.shape[1] ):
            pixel_stack = stack[:,r,c,:]
            existing = where( abs( pixel_stack[:,3] - 1. ) < 1e-5 )
            
            #print len( existing[0] )
            num_existing.append( len( existing[0] ) )
            
            if len( existing[0] ) > 0:
                out[r,c] = median_spatial( pixel_stack[ existing ] )
    
    print 'average num existing:', average( num_existing )
    print 'median num existing:', median( num_existing )
    print 'minimum num existing:', min( num_existing )
    print 'maximum num existing:', max( num_existing )
    
    return out

# result = process_image_stack( image_stack_from_filenames( filenames, size_mismatch_behavior = size_mismatch, convert = convert ) )
result = process_tiled_image_stack_from_filenames( process_image_stack, tile, filenames, size_mismatch_behavior = size_mismatch, convert = convert )

arr2img( result ).save( outname )
print '[Saved "%s"]' % ( outname, )

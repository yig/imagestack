import Image
from numpy import *

def image_stack_from_filenames( filenames, size_mismatch_behavior = None, convert = None, tile = None ):
    '''
    Given a list of pathnames to images 'filenames',
    optional parameter 'size_mismatch_behavior' which can be one of 'skip', 'error', or 'crop-upperleft' (default: 'error'), and
    optional parameter 'convert' to specify what pixel format to convert the loaded image into ('L' for grayscale (default), 'RGB', or 'RGBA'),
    returns a numpy.array containing all images (the first dimension selects the image) with floating point values between 0 and 1.
    
    Optional parameter tile, if present is a sequence of four integers.
    The first two integers are the row and column of the tile, and the second two
    integers specify how many pixel rows and columns are in each tile.
    The resulting stack will have a zero in its shape's 1-th or 2-th entry
    if the requested tile is outside of the images.
    '''
    
    assert len( filenames ) > 0
    if size_mismatch_behavior is None: size_mismatch_behavior = 'error'
    if convert is None: convert = 'L'
    
    stack = []
    for fname in filenames:
        print 'Loading "%s"' % ( fname, )
        img = Image.open( fname ).convert( convert )
        arr = asarray( img, dtype = uint8 ) / 255.
        
        if tile is not None:
            rows, cols = arr.shape[:2]
            row,col, pixels_per_row, pixels_per_column = tile
            assert row >= 0
            assert col >= 0
            assert pixels_per_row > 0
            assert pixels_per_column > 0
            arr = arr[
                row*pixels_per_row : (row+1)*pixels_per_row,
                col*pixels_per_column : (col+1)*pixels_per_column
                ]
        
        stack.append( arr )
    
    shapes = [ arr.shape for arr in stack ]
    shape2count = {}
    for shape in shapes:
        shape2count.setdefault( shape, 0 )
        shape2count[ shape ] += 1
    
    if len( shape2count ) > 1:
        print 'Images have different sizes:', shape2count
        if 'error' == size_mismatch_behavior:
            raise RuntimeError( 'Images have varying sizes.' )
        elif 'skip' == size_mismatch_behavior:
            shape = max( [ ( count, shape ) for shape, count in shape2count.iteritems() ] )[1]
            
            drop = [ filename for arr, filename in zip( stack, filenames ) if arr.shape != shape ]
            print 'Ignoring %d images: %s' % ( len( drop ), drop )
            
            stack = [ arr for arr in stack if arr.shape == shape ]
        elif 'crop-upperleft' == size_mismatch_behavior:
            shape = ( min( [ s[0] for s in shape2count.keys() ] ), min( [ s[1] for s in shape2count.keys() ] ) )
            print 'Cropping to upper-left', shape
            
            stack = [ arr[ :shape[0], :shape[1] ] for arr in stack ]
            assert len( set( [ arr.shape for arr in stack ] ) ) == 1
    
    stack = concatenate( [ arr[newaxis,...] for arr in stack ] ).astype( float )
    return stack

def arr2img( arr ):
    '''
    Given a numpy.array 'arr' representing a floating point image (one whose values are between 0 and 1),
    returns the conversion of 'arr' into a PIL Image.
    '''
    
    assert arr.dtype in ( float32, float64, float )
    return Image.fromarray( asarray( ( arr * 255 ).round(0).clip( 0, 255 ), dtype = uint8 ) )

def process_tiled_image_stack_from_filenames( process_image_stack, tile, filenames, size_mismatch_behavior = None, convert = None ):
    '''
    Given a function 'process_image_stack' that takes an image stack as would
    be returned from image_stack_from_filenames(),
    a 2-element 'tile' parameter specifying the row-and-column pixel dimensions
    into which to tile the image stack that would be returned from
    image_stack_from_filenames(),
    and optional parameters 'size_mismatch_behavior' and 'convert' to pass to
    image_stack_from_filenames(),
    returns the untiled result of process_image_stack() applied to the tiled image stack.
    
    NOTE: For convenience, if the 'tile' parameter is None, this function skips the tiling and untiling step.
    NOTE: For convenience, if the 'tile' parameter is 'auto', this function will assume square RGBA images
          and choose a tiling that uses less than 1GB ram.
    '''
    
    if tile is None:
        return process_image_stack( image_stack_from_filenames( filenames, size_mismatch_behavior = size_mismatch_behavior, convert = convert ) )
    if tile == 'auto':
        tile = tile_parameter_for_1GB( len( filenames ) )
    
    assert len( tile ) == 2
    tile = tuple( tile )
    assert tile[0] > 0
    assert tile[1] > 0
    
    tiles = [[]]
    row = 0
    col = 0
    while True:
        stack = image_stack_from_filenames( filenames, size_mismatch_behavior = size_mismatch_behavior, convert = convert, tile = (row,col) + tile )
        print 'row, col, stack.shape:', row, col, stack.shape
        ## We can't average here, because one of the shape entries might be 0.
        
        ## If we fell off the columns,
        ## move to the next row.
        if stack.shape[2] == 0:
            tiles.append( [] )
            row += 1
            col = 0
        
        ## If we fell off the rows, we're done.
        elif stack.shape[1] == 0:
            ## We will have added a final, unused row.
            assert len( tiles[-1] ) == 0
            del tiles[-1]
            break
        
        ## Otherwise, we found a good tile.
        else:
            processed = process_image_stack( stack )
            tiles[-1].append( processed )
            col += 1
    
    result = untile( tiles )
    return result

def untile( tiles ):
    '''
    Given a sequence of sequences of numpy.arrays 'tiles'
    representing a row-major 2D grid of tiles,
    where the arrays in each row of 'tiles' have the same number of rows,
    the arrays in each column of 'tiles' have the same number of columns,
    and every array has the same number of higher dimension (color channels)
    returns the arrays of the tile as a single, larger array composed of
    the tile arrays in a layout corresponding to their layour in 'tiles'.
    '''
    
    ## Copy the shape and modify the first two elements.
    shape = list( tiles[0][0].shape )
    rows = shape[0] = sum( [ tiles[row][0].shape[0] for row in xrange( len( tiles ) ) ] )
    cols = shape[1] = sum( [ tiles[0][col].shape[1] for col in xrange( len( tiles[0] ) ) ] )
    
    result = zeros( tuple( shape ), dtype = float )
    rowoff = 0
    coloff = 0
    for row in tiles:
        
        coloff = 0
        for tile in row:
            result[ rowoff : rowoff + tile.shape[0], coloff : coloff + tile.shape[1] ] = tile
            coloff += tile.shape[1]
        
        rowoff += tile.shape[0]
    
    return result

def tile_parameter_for_1GB( num_images ):
    ## Let's use a maximum of 1 GB of RAM for a stack.
    ## Let N be the number of images.
    ## Let M be the amount of memory each image should contribute: 1 GB / N.
    ## Assuming square floating-point-with-double-precision RGBA images (4*8 bytes per pixel),
    ## and the need to make a copy of all image data (another factor of 2),
    ## and the need for an additional 8*(4*N)^2 of memory,
    ## tiles' pixel edge lengths should be sqrt( 1 GB / (N*4*8) ).
    pixel_edge_length = max( int( sqrt( float( 1024*1024*1024 - 8*(4*num_images)**2 ) / ( num_images * 4*8 * 2 ) ) ), 1 )
    print 'Automatic tiling with tiles of size:', pixel_edge_length, 'by', pixel_edge_length
    tile = '%d/%d' % ( pixel_edge_length, pixel_edge_length )
    return tile

import Image
from numpy import *

def image_stack_from_filenames( filenames, error_on_size_mismatch = True, convert = 'L' ):
    assert len( filenames ) > 0
    
    stack = []
    for fname in filenames:
        print 'Loading "%s"' % ( fname, )
        img = Image.open( fname ).convert( convert )
        arr = asarray( img, dtype = uint8 ) / 255.
        
        stack.append( arr )
    
    shapes = [ arr.shape for arr in stack ]
    shape2count = {}
    for shape in shapes:
        shape2count.setdefault( shape, 0 )
        shape2count[ shape ] += 1
    
    if len( shape2count ) > 1:
        if error_on_size_mismatch:
            raise RuntimeError( 'Images have varying sizes.' )
        else:
            shape = max( [ ( count, shape ) for shape, count in shape2count.iteritems() ] )[1]
            
            drop = [ filename for arr, filename in zip( stack, filenames ) if arr.shape != shape ]
            print 'Images have different sizes.  Ignoring %d images: %s' % ( len( drop ), drop )
            
            stack = [ arr for arr in stack if arr.shape == shape ]
    
    stack = concatenate( [ arr[newaxis,...] for arr in stack ] ).astype( float )
    return stack

def arr2img( arr ):
    '''
    Given a numpy.array 'arr' representing a floating point image (one whose values are between 0 and 1),
    returns the conversion of 'arr' into a PIL Image.
    '''
    
    assert arr.dtype in ( float32, float64, float )
    return Image.fromarray( asarray( ( arr * 255 ).round(0).clip( 0, 255 ), dtype = uint8 ) )

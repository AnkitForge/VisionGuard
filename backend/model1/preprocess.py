import cv2
import numpy as np

def apply_frame_diff(frames):
    """
    Applies absolute difference between consecutive frames.
    Input: list of frames (grayscale, float32, normalized [0,1])
    Output: list of diff frames (same format)
    """
    diffs = []
    for i in range(1, len(frames)):
        diff = cv2.absdiff(frames[i], frames[i-1])
        diffs.append(diff)
    
    # If we only have 1 frame, or to maintain count, 
    # we can duplicate the first diff or add a zero frame.
    # But usually, we just return the diffs and let the 
    # caller handle the sequence length.
    if not diffs and frames:
        diffs.append(np.zeros_like(frames[0]))
        
    return diffs

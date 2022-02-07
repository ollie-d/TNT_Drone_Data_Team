# 6-class EMG paradigm
#
# 1. Fingers extended (relaxed)
# 2. Fingers clenched
# 3. L. Planar movement
# 4. R. Planar movement
# 5. U. Planar movement
# 6. D. Planar movement
#
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# !!! MAKE SURE refresh_rate IS SET TO YOUR MONITOR'S REFRESH RATE !!!
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#
# Created........: 04Feb2022 [ollie-d]
# Last Modified..: 04Feb2022 [ollie-d]



import time
import pylsl
import random
import numpy as np
import psychopy.event
import psychopy.visual
from itertools import chain
from math import atan2, degrees


# Global variables
win = None          # Global variable for window (Initialized in main)
mrkstream = None    # Global variable for LSL marker stream (Initialized in main)
photosensor = None  # Global variable for photosensor (Initialized in main)
triangle = None     # Global variable for stimulus (Initialized in main)
fixation = None     # Global variable for fixation cross (Initialized in main)

bg_color = [-1, -1, -1]
win_w = 1920
win_h = 1080
refresh_rate = 144. # Monitor refresh rate (CRITICAL FOR TIMING)


#========================================================
# High Level Functions
#========================================================
def Paradigm(n):
    global refresh_rate
    global win
    global photosensor
    global fixation
    global triangle
    global mrkstream
    global bg_color
    
    met_value = 0 # metronome value
    
    # Compute sequence of stimuli
    sequence = CreateSequence(n)
    
    # Initialize metronome, primary and secondary text
    met = psychopy.visual.TextStim(win, text = 'X', units = 'norm', alignText = 'center');
    met.setHeight(0.1);
    met.pos = (-0.1, 0)
    met.draw()
    
    # Initialize current instruction
    cur = psychopy.visual.TextStim(win, text = 'X', units = 'norm', alignText = 'center');
    cur.setHeight(0.1);
    cur.pos = (0, 0)
    cur.draw()
    
    # Initialize next instruction
    nxt = psychopy.visual.TextStim(win, text = 'X', units = 'norm', alignText = 'center', color = (0.05, 0.05, 0.05));
    nxt.setHeight(0.1);
    nxt.pos = (0, -0.1)
    nxt.draw()
    
    # set text to be appropriate sequences
    #cur.text = sequence[0]
    #nxt.text = sequence[1]

    #win.flip()
    
    # Iterate through remaining sequence
    for i in range(0, len(sequence)):
        # Set LSL marker with current stim
        mrk = pylsl.vectorstr([sequence[i]])
        # Update texts
        cur.text = sequence[i]
        if i < len(sequence)-1:
            nxt.text = sequence[i+1]
        else:
            nxt.text = 'O'
        
        # Cycle through 4 beats (120bpm) of the metronome. On final, change sequence
        # Make it 8 beats for rests
        nbeats = 4
        if sequence[i] == 'O':
            nbeats = 8
        for count in range(nbeats):
            # Set metronome
            met.text = f'{count + 1}'
            
            # Spend 1 beat (500ms) drawing text
            for frame in range(MsToFrames(500, refresh_rate)):
                if frame == 0 and count == 0:
                    mrkstream.push_sample(mrk);
                met.draw()
                nxt.draw()
                cur.draw()
                win.flip()
        

    
    '''
    for i, s in enumerate(sequence):
        # 250ms Bold fixation cross
        fixation.lineWidth = 1
        fixation.lineColor = [1, 1, 1]
        SetStimulus(fixation, 'on')
        for frame in range(MsToFrames(250, refresh_rate)):
            fixation.draw()
            win.flip()
            
        # 500ms Normal fixation cross
        fixation.lineColor = bg_color
        for frame in range(MsToFrames(500, refresh_rate)):
            fixation.draw()
            win.flip()
    
        # 500ms Stimulus presentation (w/ fixation)
        RotateTriangle(triangle, 180)   # <-- Standard (S)
        mrk = pylsl.vectorstr(['0'])
        if s == 'T':
            RotateTriangle(triangle, 0) # <-- Target (T)
            mrk = pylsl.vectorstr(['1'])
        SetStimulus(photosensor, 'on')
        for frame in range(MsToFrames(500, refresh_rate)):
            # Send LSL marker on first frame
            if frame == 0:
                mrkstream.push_sample(mrk);
            photosensor.draw()
            triangle.draw()
            fixation.draw()
            win.flip()
        
        # 1000ms darkness
        for frame in range(MsToFrames(1000, refresh_rate)):
            win.flip()
    '''
#========================================================
# Low Level Functions
#========================================================
def CreateSequence(n):
    # Create "n" of each movement type
    #
    # C is clenched
    # L is left
    # R is right
    # U is up
    # D is down
    # O is open (relaxed)
    #
    # Relaxed will always be between other movements

    seq = []
    for i in ['C', 'L', 'R', 'U', 'D']:
        seq.append([i for x in range(n)])
    seq = listFlatten(seq)
    random.seed()
    random.shuffle(seq) # shuffles in-place
    
    # Iterate through shuffled seq and add relaxed
    seq_ = []
    for s in seq:
        seq_.append('O')
        seq_.append(s)
        
    seq = None
    
    return seq_

def InitFixation(size=50):
    return psychopy.visual.ShapeStim(
                win=win,
                units='pix',
                size = size,
                fillColor=[1, 1, 1],
                lineColor=[1, 1, 1],
                lineWidth = 1,
                vertices = 'cross',
                name = 'off', # Used to determine state
                pos = [0, 0]
            )

def InitPhotosensor(size=50):
    # Create a circle in the lower right-hand corner
    # Will be size pixels large
    # Initiate as color of bg (off)
    return psychopy.visual.Circle(
            win=win,
            units="pix",
            radius=size,
            fillColor=bg_color,
            lineColor=bg_color,
            lineWidth = 1,
            edges = 32,
            name = 'off', # Used to determine state
            pos = ((win_w / 2) - size, -((win_h / 2) - size))
        )

def MsToFrames(ms, fs):
    dt = 1000 / fs;
    return np.round(ms / dt).astype(int);

def DegToPix(h, d, r, deg):
    # Source: https://osdoc.cogsci.nl/3.2/visualangle/
    deg_per_px = degrees(atan2(.5*h, d)) / (.5*r)
    size_in_px = deg / deg_per_px
    return size_in_px

def listFlatten(l):
    return list(chain.from_iterable(l))

def CreateMrkStream():
    info = pylsl.stream_info('EMG_Markers', 'Markers', 1, 0, pylsl.cf_string, 'unsampledStream');
    outlet = pylsl.stream_outlet(info, 1, 1)
    return outlet;

if __name__ == "__main__":
    # Create PsychoPy window
    win = psychopy.visual.Window(
        screen = 0,
        size=[win_w, win_h],
        units="pix",
        fullscr=True,
        color=bg_color,
        gammaErrorPolicy = "ignore"
    );
    
    # Initialize LSL marker stream
    mrkstream = CreateMrkStream();
    
    time.sleep(5)
    
    # Initialize photosensor
    #photosensor = InitPhotosensor(50)
    #fixation = InitFixation(30)

    # Run through paradigm
    Paradigm(10)
    
# Example python code for:
# - Animating live Python data
# - Reading LSL in real-time
# - Doing something with that LSL data in real-time
#   - ^ but also multi-threaded
#
# Intended demo uses synthetic stream + LSL output using OpenBCI GUI
# but it should work with any LSL stream (just make sure to set fs)
#
# Created......: 05May22 [ollie-d]
# Last Modified: 05May22 [ollie-d]

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np
from itertools import count
from collections import deque
import pylsl
import threading
import sys

# Global variables (set in main)
eeg_inlet = None
x = None
buffer = None
line = None
ax = None
last_sample = 0

def lsl_thread():
    global buffer
    global last_sample
    global eeg_inlet
    # All this will do is read from LSL and append to buffer when not empty
    ch = 0
    
    print('LSL thread awake'); sys.stdout.flush();
    
    # Read LSL
    while True:
        sample, times = eeg_inlet.pull_sample()
        
        # Append sample if exists (from single channel, ch) to buffer
        if len(sample) > 0:
            last_sample = sample[ch]
            buffer.append(last_sample)
    

def animate(i):
    global eeg_inlet
    global x
    global buffer
    global line
    ch = 3 # first channel
    
    # Read LSL, save only channel ch
    #sample, times = eeg_inlet.pull_sample()
    
    # Append sample to buffer if exists
    #if len(sample) > 0:
    #    buffer.append(sample[ch])

    # Set line's data rather than re-plotting
    line.set_ydata(buffer)
    return line,
    
    
def animate2(i):
    # This function will swap colors depending on polarity
    global eeg_inlet
    global x
    global buffer
    global ax
    global last_sample
    ch = 0 # first channel
    
    if last_sample >= 0:
        ax.set_facecolor('gray')
    else:
        ax.set_facecolor('white')


if __name__ == "__main__":
    # MAKE SURE YOU HAVE AN LSL STREAM RUNNING
    # (for this example I use synthetic data from OpenBCI GUI)

    # Sampling variables
    fs = 250.          # sampling rate (Hz)
    dt = 1. / fs       # time between samples (s)
    dt_ms = dt * 1000. # time between samples (ms)
    buffer_len = 250   # num samples to store in buffer
    buffer = deque(maxlen=buffer_len)
    
    # Fill buffer with 0s
    for i in range(buffer_len):
        buffer.append(0.)
    
    # Create an x-axis of spaced values in seconds
    x = np.linspace(0, buffer_len*dt_ms, num=buffer_len)
    
    # Initialize line / plot
    fig = plt.figure()
    ax = fig.add_subplot(1,1,1)
    ax.set_ylim([-200, 200])
    line, = ax.plot(x, np.zeros_like(x))

    # Initiate LSL streams and create inlets
    eeg_streams = pylsl.resolve_stream('type', 'EEG')
    eeg_inlet = pylsl.stream_inlet(eeg_streams[0], recover = False)
    print('Inlet Created'); sys.stdout.flush();
    
    # Launch LSL thread
    lsl = threading.Thread(target = lsl_thread, args = ())
    lsl.setDaemon(False)
    lsl.start()
    
    # Launch animation
    anim = FuncAnimation(fig, func=animate, interval=int(round(dt_ms)))
    plt.show()
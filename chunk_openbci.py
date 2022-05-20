# This is intended to be the main function for drone control.
# It will read in continuous packets from LSL, store them in a
# "buffer_len"-sample long buffer, and send a chunk of LSL data 
# every "send_every_n_samples" samples. 
# Processing can be done on the chunks before they are sent.
# It may be useful to apply a high pass filter to remove DC
# artifacts, but a lowpass filter is likely unnecessary.
# We'll have to see.
#
# Code was adapted from "live_lsl_anim.py" which should make
# learning this code easy if you took the time to learn and
# play around with that code!
#
# Created......: 20May22 [ollie-d]
# Last Modified: 20May22 [ollie-d]

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np
from itertools import count
from collections import deque
import pylsl
import threading
import sys
import copy

# Global variables (set in main)
eeg_inlet = None
emg_outlet = None
x = None
buffer = None
line = None
ax = None
last_sample = 0
send_every_n_samples = None
sample_counter = None
num_chans = None
send_chunk = False # Flag for lsl threads to communicate with

def read_lsl_thread():
    # Read and save multi-channel LSL stream
    global buffer
    global eeg_inlet
    global num_chans
    global send_chunk
    global sample_counter
    global send_every_n_samples

    print('Read LSL thread awake'); sys.stdout.flush();
    
    # Read LSL
    while True:
        samples, times = eeg_inlet.pull_sample()
        
        # Append samples if exists to buffer
        if len(samples) > 0:
            sample_counter = sample_counter + 1
            for i in range(num_chans):
                buffer[i].append(samples[i])
            if sample_counter == send_every_n_samples:
                send_chunk = True
                sample_counter = 0
    
def send_lsl_thread():
    # Process data and send in LSL chunk when appropriate
    global buffer
    global emg_outlet
    global send_chunk
    global sample_counter
    global send_every_n_samples
    
    print('Write LSL thread awake'); sys.stdout.flush();
     
    while True:
        if send_chunk:
            #print('Send chunk requested'); sys.stdout.flush();
            
            # First, copy/cast buffer to list
            buffer_ = [list(buffer[x]) for x in range(len(buffer))]
            #buffer_ = list(np.array(buffer_).T)
            
            time = pylsl.local_clock() # acquire LSL time
            
            # Send chunk and timestamp
            emg_outlet.push_chunk(buffer_, time)
            print(np.array(buffer_).shape)
            
            send_chunk = False # reset flag
            
if __name__ == "__main__":
    # MAKE SURE YOU HAVE AN LSL STREAM RUNNING
    # (for this example I use synthetic data from OpenBCI GUI)

    # Sampling variables
    num_chans = 3      # number of channels to save recordings (sequential)
    fs = 250.          # sampling rate (Hz)
    dt = 1. / fs       # time between samples (s)
    dt_ms = dt * 1000. # time between samples (ms)
    buffer_len = 150   # num samples to store in buffer
    
    # Create 2D array of deques (num_chans by buffer_len)
    buffer = [deque(maxlen=buffer_len) for x in range(num_chans)] 
    
    # Number of samples to wait before sending full buffer via chunk
    send_every_n_samples = 38 # ~152 ms at 250 Hz sampling rate
    sample_counter = 0        # keep track of samples for sending
    
    # Fill buffer with 0s
    for ch in range(num_chans):
        for i in range(buffer_len):
            buffer[ch].append(0.)
    
    # Initialize LSL inlet
    eeg_streams = pylsl.resolve_stream('type', 'EEG')
    eeg_inlet = pylsl.stream_inlet(eeg_streams[0], recover = False)
    print('Inlet Created'); sys.stdout.flush();
    
    # Initialize LSL outlet
    channel_names = ['EMG1', 'EMG2', 'EMG3']
    n_channels = len(channel_names)
    stream_type = 'EMG_chunk'
    srate = 0.0#int(round(send_every_n_samples * dt_ms))
    info = pylsl.StreamInfo('EMG_Chunk_Stream', stream_type, n_channels, srate, 'float32', 'tnt1337')
    
    # Add metadata
    chns = info.desc().append_child("channels")
    for chan_ix, label in enumerate(channel_names):
        ch = chns.append_child("channel")
        ch.append_child_value("label", label)
        ch.append_child_value("unit", "microvolts")
        ch.append_child_value("type", "EMG")
        ch.append_child_value("scaling_factor", "1")
    
    
    emg_outlet = pylsl.StreamOutlet(info, 
                                    chunk_size=buffer_len, 
                                    max_buffered=60)
    print('Outlet created'); sys.stdout.flush();
    
    # Launch LSL threads
    lsl_read = threading.Thread(target = read_lsl_thread, args = ())
    lsl_read.setDaemon(False)
    lsl_read.start()
    
    lsl_send = threading.Thread(target = send_lsl_thread, args = ())
    lsl_send.setDaemon(False)
    lsl_send.start()
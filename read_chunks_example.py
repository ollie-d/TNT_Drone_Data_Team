"""Example program to demonstrate how to read a multi-channel time-series
from LSL in a chunk-by-chunk manner (which is more efficient)."""

from pylsl import StreamInlet, resolve_stream
import numpy as np

chunk_size = 150 # 150 samples
sample_counter = 0
buffer = []

if __name__ == '__main__':
    # first resolve an EEG stream on the lab network
    print("looking for an EMG stream...")
    streams = resolve_stream('type', 'EMG_chunk')

    # create a new inlet to read from the stream
    inlet = StreamInlet(streams[0])

    while True:
        # get a new sample (you can also omit the timestamp part if you're not
        # interested in it)
        chunk, timestamps = inlet.pull_chunk()
        if timestamps:
            samples = np.array(chunk)
            sample_counter = sample_counter + samples.shape[0]
            buffer.append(samples)
            print(samples.shape)
        
        # Do something when buffer is full
        if sample_counter == chunk_size:
            # Concat list into single np array
            data = np.concatenate((buffer), axis=0)
            print(data.shape)
            print('=====================================')
            
            sample_counter = 0 # reset counter
            buffer = [] # reset buffer
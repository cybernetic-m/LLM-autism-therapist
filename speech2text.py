import pyaudio
import wave
import numpy as np
import pyaudio

def record_audio():
    

    """ Record audio from the microphone and save it to a WAV file.
    """

    # PyAudio initialization
    # PyAudio attends that the buffer (chunks) is filled with audio samples (amplitudes of the sound wave). 
    # When the chunks are filled, PyAudio transform each audio samples in 16-bit integers.
    # Each second the microphone captures 44100 samples (44.1 kHz).
    # The stereo modality means that the microphone captures two channels (left and right), it means 44100 samples for each channel. 
    p = pyaudio.PyAudio() # Create a PyAudio object
    chunk = 1024 # Buffer size (how many samples PyAudio process read at once)
    format_type = pyaudio.paInt16 # Audio format (each sample is a 16-bit integer)
    channels = 2 # Number of audio channels (1 for mono, 2 for stereo)
    rate = 44100 # Sample rate (samples per second) it means 44.1 kHz
    
    # Thresholds for silence detection
    threshold_silent_chunks = 200 # Number of silent chunks before stopping the recording
    threshold_volume = 100 # Volume threshold to consider the audio as silent

    filename = "audio.wav" # Output file name

    print("Recording... Speak now!")

    # Open the audio stream
    stream = p.open(format=format_type, 
                    channels=channels, rate=rate, 
                    frames_per_buffer=chunk, 
                    input=True
                    )
    
    frames = [] # List to store audio frames
    
    # Counter for silent chunks, if it reach a threshold, the recording stops
    silent_chunks = 0 
    
    # It will record audio until the user press Ctrl+C or the there is a long silence
    try:
        while True:
            # The data is a buffer-like object in exadecimal like b'\x0000\x0001\x0002...'
            data  = stream.read(chunk) # Read audio data from the stream (a chunk of audio samples)
            frames.append(data) # Append the audio data to the frames list

            # Convert the audio data to numpy array to analyze silence
            # In particular it converts from bytes string like b'\x0000\x0001\x0002...' to a numpy array of 16-bit integers [0, 1, 2, ...]
            audio_data_np = np.frombuffer(data, dtype=np.int16) # Convert the audio data from a buffer to a numpy array

            print (audio_data_np)
            # Compute the RMS (Root Mean Square) of the audio data to check if it is silent
            rms_audio = np.sqrt(np.mean(audio_data_np**2))

            # Increment the silent chunks counter if the audio is silent
            if rms_audio < threshold_volume:
                silent_chunks += 1
            else:
                silent_chunks = 0 #reset the silent chunks counter if the audio is not silent

            # If the number of silent chunks exceeds the threshold, stop recording
            if silent_chunks >= threshold_silent_chunks:
                print("Silence detected, stopping recording.")
                break

    except KeyboardInterrupt:
        print("Recording stopped by user.")

    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    p.terminate()

    # Save the recorded audio to a WAV file
    # Open a wave file in write binary mode
    with wave.open(filename, 'wb') as file:
        # Save the metadata of the wave file, go to the Header of the file
        file.setnchannels(channels) # Set the number of channels (1 for mono, 2 for stereo)
        file.setsampwidth(p.get_sample_size(format_type)) # Set the sample width (number of bytes per sample). The p.get_sample_size return "2" for 16-bit integers.
        file.setframerate(rate) # Set the sample rate (samples per second)
        
        # Save the payload of the wave file, go to the Data of the file
        # Write the frames to the file. In particular frames is a list of audio data chunks, each chunk is a bytes string like b'\x0000\x0001\x0002...'
        # frames = [b'\x0000\x0001\x0002...', b'\x0003\x0004\x0005...', ...]
        # The b''.join(frames) concatenate all the bytes strings in frames into a single bytes string like b'\x0000\x0001\x0002...\x0003\x000
        # data = [b'\x0000\x0001\x0002...\x0003\x0004\x0005...']
        # The b'' means that the delimiter is an empty string, so the bytes strings are concatenated without any separator.
        file.writeframes(b''.join(frames)) # Write the audio frames to the
    print(f"Recording saved to {filename}")

record_audio()  # Call the function to record audio
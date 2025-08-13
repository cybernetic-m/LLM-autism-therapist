import pyaudio
import wave
import numpy as np
#import whisper

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
    threshold_silent_chunks = 100 # Number of silent chunks before stopping the recording
    threshold_volume = 100 # Volume threshold to consider the audio as silent

    filename = "audio.wav" # Output file name

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
            audio_data_np = audio_data_np.astype(np.int32) # Convert the audio data to 32-bit integers beacuse squarring to compute the RMS requires 32-bit integers to avoid overflow and negative values

            # Compute the RMS (Root Mean Square) of the audio data to check if it is silent
            # If the audio data is empty, set the RMS to 0 
            audio_mean_square = np.mean(audio_data_np**2)  # Compute the mean of the audio data
            rms_audio = np.sqrt(audio_mean_square)

            # Increment the silent chunks counter if the audio is silent
            if rms_audio < threshold_volume:
                silent_chunks += 1
            else:
                silent_chunks = 0 #reset the silent chunks counter if the audio is not silent

            # If the number of silent chunks exceeds the threshold, stop recording
            if silent_chunks >= threshold_silent_chunks:
                print("\n---Silence detected, stopping recording---\n---Whisper is transcribing---")
                break

    except KeyboardInterrupt:
        print("\n---Stopped Recording---\n---Whisper is transcribing---")

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
    #print(f"Recording saved to {filename}")

def speech2text(audio_file_path, model, device="cpu"):

    """ Convert speech to text using Whisper model.
    Args:
        audio_file_path (str): Path to the audio file to transcribe.
        model_size (str): Size of the Whisper model to use (tiny, base, small, medium, large). We suggest to use 'medium' for a good balance between speed and accuracy.
    Outputs:
        result (dict): The transcription result containing the transcribed text.
    """
    
    #print(f"Transcribing audio with Whisper model {model_size}...")

    # Load the Whisper model
    #model = whisper.load_model(model_size, device=device)  

    # Transcribe the recorded audio. The model will process the audio file and return the transcription result dict. 
    # The dict is {'text': ' ciao', 'segments': [{'id': 0, 'seek': 0, 'start': 0.0, 'end': 2.0, 'text': ' ciao', 'tokens': [50364, 42860, 50464], 
    # 'temperature': 0.0, 'avg_logprob': -0.7956851124763489, 'compression_ratio': 0.3333333333333333, 'no_speech_prob': 0.3112330734729767}], 'language': 'it'}
    # We are interested in the 'text' key, which contains the transcribed text, discarding the rest of the information.
    result = model.transcribe(audio_file_path)  # Transcribe the audio file

    # Return only the transcribed text
    return result['text']  

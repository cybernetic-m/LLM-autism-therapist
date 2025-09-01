Inside this you can find:

1. 'benchmark.py': It is the python file that runs the functionality benchmarks (see 7.2 RBC Evaluation of 'report.pdf')
                
                   It has 3 arguments that can be passed '-audio' to test the TTS and STT, it will record a specifiable amount of samples that the tester should say to a wav file,
                   then transcribe it and save it to .txt file and then synthesize it and save it as a .mp3
                   '-attention' to the test the gaze, in particular it will save a frame per second with annotations on it to see what labels have been chose by the models 
                   and optionally '-audio_samples' + (int) to specify how many audio samples record, do the STT and TTS
                   (the last has a standard values of 100 audio samples)

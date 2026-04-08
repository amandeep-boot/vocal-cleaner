# Vocal Cleaner -(Python | webrtcvad | rnnoise)
This is a tool that takes any kind of vocal file. Processes it and gives a noise free enhanced audio file with clear vocal 

## Flow 
- `Ingest` standardize the vocal file in .wav format 
- `vad` detect the human vocal parts using webrtcvad 
- `trim` trim the unneccessary parts and blank intervals
- `denoise` remove the background noise(stationary - continuos noise)
- `rnnoise` remove the ambient noise(dynamic noise)
- `pipeline` connect all the steps sequentially 

Denoising needs improvements- currently working on it - other parts are functioning well.



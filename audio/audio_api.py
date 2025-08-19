import requests
import time

def audio_groq_api(api_key, model_name, audio_path):

    # This function sends a audio to a Groq-hosted API waiting for the response (using Whisper model)
    # Args: - api_key: the Groq API key you need to authorization
    #       - model_name: it is the model_name of whisper (Ex. 'large')
    #       - audio_path: the path to the audio.wav file
    # Output: - transcription: <str> the transcribed text returned by the Whisper model, or None if an error occurred

    url = "https://api.groq.com/openai/v1/audio/transcriptions"  # this is the url of the Groq API (same structure of OpenAI message!)

    # The header of the message contain the "Content-Type" (it say that the message structure will be json, a dict) and the "Authorization"
    # It is a string "Bearer gsk...." with the api_key in a Bearer Token type (Bearer means that the authorization is give with the api_key directly after)
    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    # This is the message content itself. It contain the "model_name", its "temperature"
    # the messages contain two dictionaries: the first one is the system prompt (the instructions for the model, like "You are a translator...")
    # and the second one is the user prompt (the input sentence to translate)
    with open (audio_path, 'rb') as audio_file: 
        files = {
            "file": (audio_path, audio_file, "audio/wav")
        }
        data = {
        "model": model_name,
        }

        while True:
            try:
                response = requests.post(url, headers=headers, files=files, data=data)  # send the request to the Groq API
                # Check for rate limiting (HTTP 429), wait 5 seconds and retry
                if response.status_code in [429, 500]:
                    # print(f"Received {response.status_code}. Retrying in 5s...")
                    time.sleep(5)
                    continue  # Retry after wait

                response.raise_for_status()  # Raise an exception for other HTTP errors like 400 or 500 (if one occurred)
                transcription = response.json()  # return the response in json format (a dict)

                # Translation is a dict with 'id' (a unique identifier for the request),  'created' (the timestamp of the request) ...
                # inside 'choices' there are different generated responses in general, we take the first one
                # inside 'choices there is the 'message' (translation) with the 'role' (user or assistant) and the 'content' (the translated sentence with the reasoning)
                return transcription["text"]

            except requests.exceptions.RequestException as e:
                print(f"Error: {e}")
                return None

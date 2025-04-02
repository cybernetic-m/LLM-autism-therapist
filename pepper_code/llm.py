import json 

# First of all you need to modify the config.json file based on yours specifications about the LLM:
# 'mode': it can be 'online' if you want to use api of online LLMs, or 'offline' if you want to use local gemma3b LLM
# 'api_key': your api_key
# 'online_model': the name of the online model
# 'local_model': the name of the local model
  
with open("config.json", "r") as f:
    config = json.load(f)

    mode = config['llm_mode']
    api_key = config['api_key']
    online_model = config['online_model']
    local_model = config['local_model']


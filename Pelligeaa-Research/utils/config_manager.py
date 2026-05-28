import json
import os

CONFIG_FILE = "config/saved_configs.json"



def save_config(name, config):
    os.makedirs("config", exist_ok=True)

    configs = {}

    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            configs = json.load(f)

    configs[name] = config

    with open(CONFIG_FILE, "w") as f:
        json.dump(configs, f, indent=4)



def load_configs():
    if not os.path.exists(CONFIG_FILE):
        return {}

    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

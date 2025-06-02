import os
import traceback
import toml

DEFAULT_CONFIG =  {}
USER_DATA_DIR = os.getenv("USER_DATA_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "user_data"))
FILES_DIR = os.path.join(USER_DATA_DIR, "files")

app_config = {}
class ConfigService:
    def __init__(self):
        self.root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.config_file = os.getenv("CONFIG_PATH", os.path.join(USER_DATA_DIR, "config.toml"))

    async def exists_config(self):
        return os.path.exists(self.config_file)

    def get_config(self):
        try:
            with open(self.config_file, 'r') as f:
                config = toml.load(f)
            
            # Mask API keys
            # if 'llm' in config and 'api_key' in config['llm']:
            #     config['llm']['api_key'] = '********'
            global app_config
            app_config = config
            return config
        except Exception as e:
            return DEFAULT_CONFIG

    async def update_config(self, data):
        try:
            # if not os.path.exists(self.config_file):
            #     config = DEFAULT_CONFIG
            # else:
            #     with open(self.config_file, 'r') as f:
            #         config = toml.load(f)
            # if 'llm' in data:
            #     llm_config = data['llm']
            #     for key in ['model', 'base_url', 'api_key', 'max_tokens', 'temperature']:
            #         if key in llm_config:
            #             config['llm'][key] = llm_config[key]
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                toml.dump(data, f)
            
            return {"status": "success", "message": "Configuration updated successfully"}
        except Exception as e:
            traceback.print_exc()
            return {"status": "error", "message": str(e)} 
        
config_service = ConfigService()

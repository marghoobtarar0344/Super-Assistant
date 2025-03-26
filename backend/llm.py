from groq import Groq
from config.config import Config

class GroqService:
    def __init__(self):
        self.client = Groq(api_key=Config.GROQ_API_KEY)
    
    def get_client(self):
        return self.client
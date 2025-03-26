class WeatherService:
    
    @staticmethod
    async def get_weather(city: str) -> dict:
        return {
            "temperature": "22°C", 
            "conditions": "Sunny",
            "city": city
        }

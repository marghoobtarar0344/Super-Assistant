import json
from typing import AsyncGenerator, Dict, Any, Optional
from llm import GroqService
from tools.weather import WeatherService
from tools.appointment import AppointmentService
from tools.dealership import DealershipService
from config.config import Config

class SSEService:
    def __init__(self):
        self.groq = GroqService()
        self.tools_appointment = AppointmentService()
        self.tools_dealer = DealershipService()
        self.tools_weather = WeatherService()
        self._define_all_tools()

    def _define_all_tools(self):
        self.TOOLS = [
            # get_weather
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Gets weather information for a city",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {"type": "string", "description": "The city name"}
                        },
                        "required": ["city"]
                    }
                }
            },
            # get_dealership_address
            {
                "type": "function",
                "function": {
                    "name": "get_dealership_address",
                    "description": "Returns address for a dealership",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "dealership_id": {"type": "string", "description": "Dealership ID"}
                        },
                        "required": ["dealership_id"]
                    }
                }
            },
            # check_appointment_availability
            {
                "type": "function",
                "function": {
                    "name": "check_appointment_availability",
                    "description": "Checks available test drive slots",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "dealership_id": {"type": "string"},
                            "date": {"type": "string", "format": "date"}
                        },
                        "required": ["dealership_id", "date"]
                    }
                }
            },
            # schedule_appointment
            {
                "type": "function",
                "function": {
                    "name": "schedule_appointment",
                    "description": "Books a test drive appointment",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {"type": "string"},
                            "dealership_id": {"type": "string"},
                            "date": {"type": "string", "format": "date"},
                            "time": {"type": "string"},
                            "car_model": {"type": "string"}
                        },
                        "required": ["user_id", "dealership_id", "date", "time", "car_model"]
                    }
                }
            }
        ]

    async def generate_response(self, query: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Handles complete SSE streaming with all tools"""
        try:
            # Initialize Groq stream 
            stream = self.groq.get_client().chat.completions.create(
                messages=[{"role": "user", "content": query}],
                model=Config.MODEL_NAME,
                tools=self.TOOLS,
                tool_choice="auto",
                stream=True
            )

            tool_calls = []
            
            # Process initial stream 
            for chunk in stream:
                processed = self._process_chunk(chunk, tool_calls)
                if processed is not None:
                    yield processed
            
            # Process tool calls 
            for tool in tool_calls:
                async for event in self._handle_tool_execution(tool, query):
                    yield event

        except Exception as e:
            yield {"event": "error", "data": str(e)}
        finally:
            yield {"event": "end", "data": ""}

    def _process_chunk(self, chunk, tool_calls: list) -> Optional[Dict[str, Any]]:
        """Processes a single stream chunk"""
        if not (chunk.choices and chunk.choices[0].delta):
            return None
            
        delta = chunk.choices[0].delta
        
        if delta.content:
            return {"event": "chunk", "data": delta.content}
        
        if delta.tool_calls:
            for tool_call in delta.tool_calls:
                if tool_call.function:
                    tool_calls.append({
                        "id": tool_call.id,
                        "name": tool_call.function.name,
                        "args": tool_call.function.arguments
                    })
                    return {
                        "event": "tool_use",
                        "data": json.dumps({
                            "name": tool_call.function.name,
                            "parameters": json.loads(tool_call.function.arguments)
                        })
                    }
        return None

    async def _handle_tool_execution(self, tool: Dict[str, Any], query: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Executes tool and streams follow-up response"""
        # Execute the tool
        result = await self._execute_tool(tool["name"], json.loads(tool["args"]))
        
        # Yield tool output
        yield {
            "event": "tool_output",
            "data": json.dumps({
                "name": tool["name"],
                "output": result
            })
        }
        
        # Get follow-up response (synchronous stream)
        follow_up = self.groq.get_client().chat.completions.create(
            messages=[
                {"role": "user", "content": query},
                {
                    "role": "tool",
                    "name": tool["name"],
                    "content": json.dumps(result),
                    "tool_call_id": tool["id"]
                }
            ],
            model=Config.MODEL_NAME,
            stream=True
        )
        
        # Process follow-up chunks 
        for chunk in follow_up:
            if chunk.choices and chunk.choices[0].delta.content:
                yield {"event": "chunk", "data": chunk.choices[0].delta.content}

    async def _execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Routes to the correct tool implementation"""
        tool_mapping = {
            "get_weather": self.tools_weather.get_weather,
            "get_dealership_address": self.tools_dealer.get_dealership_address,
            "check_appointment_availability": self.tools_appointment.check_appointment_availability,
            "schedule_appointment": self.tools_appointment.schedule_appointment
        }
        
        if tool_name not in tool_mapping:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        return await tool_mapping[tool_name](**params)

import json
from typing import AsyncGenerator, Dict, Any, Optional,Generator
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

    def _create_sse_event(self, event_type: str, data: Any) -> str:
        """Creates SSE events with guaranteed correct formatting"""
        event_type = event_type.strip() if event_type else "message"
        
        # Handle data formatting
        if isinstance(data, str):
            if data.startswith("{") and data.endswith("}"):
                try:
                    data = json.dumps(json.loads(data))
                except json.JSONDecodeError:
                    pass
        else:
            # Convert non-string data to JSON
            data = json.dumps(data)
        
        # Return clean SSE format (single newline at end)
        # print('here are event',f"event: {event_type}\ndata: {data} \n")
        return f"event: {event_type}\ndata: {data} \n".encode('utf-8')
    async def generate_response(self, query: str) -> AsyncGenerator[str, None]:
        try:
            # Initialize stream
            stream = self.groq.get_client().chat.completions.create(
                messages=[{"role": "user", "content": query}],
                model=Config.MODEL_NAME,
                tools=self.TOOLS,
                tool_choice="auto",
                stream=True
            )

            tool_calls = []
            
            # Process initial stream with raw output
            for chunk in stream:
                if not chunk.choices or not chunk.choices[0].delta:
                    continue
                    
                delta = chunk.choices[0].delta
                
                if delta.content:
                    content = delta.content.strip()
                    if content:
                        print('here is chunk 2',self._create_sse_event("chunk", content))
                        yield self._create_sse_event("chunk", content)
                
                elif delta.tool_calls:
                    for tool_call in delta.tool_calls:
                        if tool_call.function:
                            tool_calls.append({
                                "id": tool_call.id,
                                "name": tool_call.function.name,
                                "args": tool_call.function.arguments
                            })
                            yield self._create_sse_event("tool_use", {
                                "name": tool_call.function.name,
                                "parameters": str(json.loads(tool_call.function.arguments))
                            })
            
            # Process tool calls
            for tool in tool_calls:
                try:
                    result = await self._execute_tool(tool["name"], json.loads(tool["args"]))
                    # yield self._create_sse_event("tool_output", {
                    #     "name": tool["name"],
                    #     "output": result if isinstance(result, dict) else {"result": str(result)},
                    #     "success": True
                    # })
                    
                    # Get follow-up response
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
                    
                    for chunk in follow_up:
                        if chunk.choices and chunk.choices[0].delta.content:
                            content = chunk.choices[0].delta.content.strip()
                            if content:
                                yield self._create_sse_event("chunk", content)
                
                except Exception as tool_error:
                    yield self._create_sse_event("tool_output", {
                        "name": tool["name"],
                        "output": {"error": str(tool_error)},
                        "success": False
                    })

        except Exception as e:
            yield self._create_sse_event("error", {"message": str(e)})
        finally:
            yield self._create_sse_event("end", {})


    async def _execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Async tool execution"""
        tool_mapping = {
            "get_weather": self.tools_weather.get_weather,
            "get_dealership_address": self.tools_dealer.get_dealership_address,
            "check_appointment_availability": self.tools_appointment.check_appointment_availability,
            "schedule_appointment": self.tools_appointment.schedule_appointment
        }
        
        if tool_name not in tool_mapping:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        result = await tool_mapping[tool_name](**params)
        return result if isinstance(result, dict) else {"result": result}
    
    def _process_chunk(self, chunk, tool_calls: list) -> Optional[Dict[str, Any]]:
        """Processes synchronous stream chunks and prevents duplicate outputs."""
        if not (chunk.choices and chunk.choices[0].delta):
            return None

        delta = chunk.choices[0].delta

        if delta.content and delta.content.strip():
            processed_data = {"event": "chunk", "data": delta.content.strip()}
            print(f"DEBUG: _process_chunk - {processed_data}")  # 🔍 Debugging
            return processed_data

        if delta.tool_calls:
            for tool_call in delta.tool_calls:
                if tool_call.function:
                    tool_calls.append({
                        "id": tool_call.id,
                        "name": tool_call.function.name,
                        "args": tool_call.function.arguments
                    })
                    tool_use_data = {
                        "event": "tool_use",
                        "data": json.dumps({
                            "name": tool_call.function.name,
                            "parameters": str(json.loads(tool_call.function.arguments))
                        })
                    }
                    print(f"DEBUG: _process_chunk - {tool_use_data}")  # 🔍 Debugging
                    return tool_use_data

        return None  # Ignore empty chunks

    
    
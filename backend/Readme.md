# SuperCar Virtual Assistant API

FastAPI backend for AI-powered car dealership assistant with tool calling and SSE streaming.

## Features

- **4 Integrated Tools**:
  - `get_weather` - Fetch weather data
  - `get_dealership_address` - Get dealership locations
  - `check_appointment_availability` - View test drive slots
  - `schedule_appointment` - Book test drives

- **SSE Streaming** - Real-time response streaming
- **Groq Integration** - Powered by Llama 3 70B model
- **Modular Architecture** - Easy to extend

## Test Cases

### 1. Basic API Health Check
```bash
curl -X GET http://localhost:8000/
```
### 2. Weather Tool Test
```bash
 curl -X POST -N -H "Content-Type: application/json"   -d '{"query": "What'\''s the weather in Tokyo? ", "session_id": "test123"}'   http://localhost:8005/query
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100    67    0     0  100    67      0     52  0:00:01  0:00:01 --:--:--    52
```
#### output looks like
```bash
event: tool_use
data: {"name": "get_weather", "parameters": {"city": "Tokyo"}}

event: tool_output
data: {"name": "get_weather", "output": {"temperature": "22\u00b0C", "conditions": "Sunny", "city": "Tokyo"}}

event: chunk
data: The

100   310    0   243  100    67    106     29  0:00:02  0:00:02 --:--:--   135event: chunk
data:  weather

event: chunk
data:  in

event: chunk
data:  Tokyo

event: chunk
data:  is

event: chunk
data:

event: chunk
data: 22

event: chunk
data: °C

event: chunk
data:  and

event: chunk
data:  sunny

event: chunk
data: .

event: end
data:

```

**Verification:**
- Should return SSE events: tool_use → tool_output → chunk
- Weather data includes temperature and conditions





### 3. Dealership Location Test
```bash
 curl -X POST -N -H "Content-Type: application/json"   -d '{"query": "What is the address of dealer nyc?", "session_id": "test123"}'   http://localhost:8000/query

  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100    67    0     0  100    67      0     52  0:00:01  0:00:01 --:--:--    52
```
#### output looks like
```bash
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100    72    0     0  100    72      0     56  0:00:01  0:00:01 --:--:--    56event: tool_use
data: {"name": "get_dealership_address", "parameters": {"dealership_id": "nyc"}}

event: tool_output
data: {"name": "get_dealership_address", "output": {"name": "SuperCar NYC", "address": "123 Broadway, New York, NY"}}

event: chunk
data: The

100   341    0   269  100    72    137     36  0:00:02  0:00:01  0:00:01   173event: chunk
data:  address

event: chunk
data:  of

event: chunk
data:  the

event: chunk
data:  dealer

event: chunk
data:  "

event: chunk
data: Super

event: chunk
data: Car

event: chunk
data:  NYC

event: chunk
data: "

event: chunk
data:  is

event: chunk
data:

event: chunk
data: 123

event: chunk
data:  Broadway

event: chunk
data: ,

event: chunk
data:  New

event: chunk
data:  York

event: chunk
data: ,

event: chunk
data:  NY

event: chunk
data: .

event: end
data:


```

**Verification:**
-   Should return exact address for NYC location
-   Response includes get_dealership_address tool output





### 4. Appointment Booking Test
```bash
 curl -X POST -N -H "Content-Type: application/json"   -d '{"query": "Book me a test drive for Model X in NYC at 10:00 on 2023-12-15", "session_id": "user123"}'   http://localhost:8000/query

```
#### output looks like
```bash
data: {"name": "schedule_appointment", "parameters": {"car_model": "Model X", "date": "2023-12-15", "dealership_id": "NYC", "time": "10:00", "user_id": "your_id"}}

100   284    0   184  100   100    104     56  0:00:01  0:00:01 --:--:--   160event: tool_output
data: {"name": "schedule_appointment", "output": {"status": "failed", "message": "Time slot 10:00 not available"}}

event: chunk
data: I

100   447    0   347  100   100    145     41  0:00:02  0:00:02 --:--:--   187event: chunk
data:  apologize

event: chunk
data:  for

event: chunk
data:  the

event: chunk
data:  inconvenience

event: chunk
data: .

event: chunk
data:  Unfortunately

event: chunk
data: ,

event: chunk
data:  the

event: chunk
data:

event: chunk
data: 10

event: chunk
data: :

event: chunk
data: 00

event: chunk
data:  time

event: chunk
data:  slot

event: chunk
data:  on

event: chunk
data:  December

event: chunk
data:

event: chunk
data: 15

event: chunk
data: ,

event: chunk
data:

event: chunk
data: 202

event: chunk
data: 3

event: chunk
data: ,

event: chunk
data:  is

event: chunk
data:  not

event: chunk
data:  available

event: chunk
data:  for

event: chunk
data:  a

event: chunk
data:  test

event: chunk
data:  drive

event: chunk
data:  of

event: chunk
data:  the

event: chunk
data:  Model

event: chunk
data:  X

event: chunk
data:  in

event: chunk
data:  NYC

event: chunk
data: .

event: chunk
data:  Would

event: chunk
data:  you

event: chunk
data:  like

event: chunk
data:  me

event: chunk
data:  to

event: chunk
data:  suggest

event: chunk
data:  an

event: chunk
data:  alternative

event: chunk
data:  time

event: chunk
data:  slot

event: chunk
data:  or

event: chunk
data:  assist

event: chunk
data:  you

event: chunk
data:  in

event: chunk
data:  finding

event: chunk
data:  a

event: chunk
data:  different

event: chunk
data:  date

event: chunk
data: ?

event: end
data:

```

**Verification:**
-   Returns list of available time slots
-   Properly handles date parsing



### 5. Appointment Availibility Test
```bash
 curl -X POST -N -H "Content-Type: application/json"   -d '{"query": "What test drive slots are available in LA tomorrow?", "session_id": "user123"}'   http://localhost:8000/query

```


### 6. Update .env file
```bash
# Groq API Key (get from https://console.groq.com/keys)
GROQ_API_KEY="gsk_fu*****"

# Model Configuration
MODEL_NAME=llama3-70b-8192  # Llama 3.3 70B Versatile model

# Optional Configuration
DEBUG=false

```


### 7. Run Docker Compose
```bash
docker compose up --build

```

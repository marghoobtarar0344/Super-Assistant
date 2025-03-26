from models import  appointment_db, scheduled_appointments

class AppointmentService:
    
    @staticmethod
    async def check_appointment_availability(dealership_id: str, date: str) -> dict:
        return {
            "dealership": dealership_id,
            "date": date,
            "available_slots": appointment_db.get(dealership_id, {}).get(date, [])
        }

    @staticmethod
    async def schedule_appointment(
        user_id: str,
        dealership_id: str,
        date: str,
        time: str,
        car_model: str
    ) -> dict:
        available = appointment_db.get(dealership_id, {}).get(date, [])
        if time not in available:
            return {
                "status": "failed",
                "message": f"Time slot {time} not available"
            }
        
        appointment_id = f"apt-{len(scheduled_appointments)+1}"
        scheduled_appointments[appointment_id] = {
            "user_id": user_id,
            "dealership_id": dealership_id,
            "date": date,
            "time": time,
            "car_model": car_model,
            "status": "confirmed"
        }
        
        appointment_db[dealership_id][date].remove(time)
        return {
            "status": "success",
            "appointment_id": appointment_id,
            "details": scheduled_appointments[appointment_id]
        }
from models import dealerships

class DealershipService:
    
    @staticmethod
    async def get_dealership_address(dealership_id: str) -> dict:
        return dealerships.get(
            dealership_id.lower(),
            {"error": "Dealership not found"}
        )

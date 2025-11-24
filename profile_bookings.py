import cProfile
import pstats
from memory_profiler import profile
from bookings_service.app import app, db, Booking
import datetime

# 1. Function to Profile 
def simulation_run():
    with app.app_context():
        client = app.test_client()
        
        room_id = 999 
        user_id = 1
        
        base_time = datetime.datetime(2025, 12, 1, 8, 0, 0)
        
        for i in range(100):
            start = base_time + datetime.timedelta(hours=i)
            end = start + datetime.timedelta(hours=1)
            
            data = {
                "user_id": user_id,
                "room_id": room_id,
                "start_time": start.isoformat(),
                "end_time": end.isoformat()
            }
            client.post('/bookings', json=data)

# 2. Memory Profiling Wrapper
@profile
def memory_test():
    simulation_run()

if __name__ == "__main__":
    print("--- Starting Bookings Service Profiling ---")
    profiler = cProfile.Profile()
    profiler.enable()
    
    simulation_run()
    
    profiler.disable()
    stats = pstats.Stats(profiler).sort_stats('cumtime')
    stats.print_stats(15) 
    
    print("\n--- Starting Memory Profiling ---")
    memory_test()
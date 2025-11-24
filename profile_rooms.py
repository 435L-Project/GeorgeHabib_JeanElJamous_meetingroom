import cProfile
import pstats
from memory_profiler import profile
from rooms_service.app import app, db, Room


TEST_ROOM_DATA = {
    "name": "Profiling Room",
    "capacity": 10,
    "equipment": "Projector,Whiteboard",
    "location": "Building A"
}

# 1. Function to Profile 
def simulation_run():
    """Runs a sequence of Room Creations and Searches."""
    with app.app_context():
        client = app.test_client()

        for i in range(50):
            data = TEST_ROOM_DATA.copy()
            data['name'] = f"Profile Room {i}"
            client.post('/rooms', json=data)

        for _ in range(50):
            client.get('/rooms?capacity=5')

# 2. Memory Profiling Wrapper
@profile
def memory_test():
    simulation_run()

if __name__ == "__main__":
    print("--- Starting Rooms Service Profiling ---")
    profiler = cProfile.Profile()
    profiler.enable()
    
    simulation_run()
    
    profiler.disable()
    stats = pstats.Stats(profiler).sort_stats('cumtime')
    stats.print_stats(10)
    
    print("\n--- Starting Memory Profiling ---")
    memory_test()
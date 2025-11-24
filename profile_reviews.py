import cProfile
import pstats
from memory_profiler import profile
from reviews_service.app import app, db, Review

TEST_REVIEW_DATA = {
    "user_username": "prof_reviewer",
    "room_id": 101,
    "rating": 5,
    "comment": "This is a great room! <script>alert('xss')</script> <b>Bold</b>" 
}

# 1. Function to Profile
def simulation_run():
    with app.app_context():
        client = app.test_client()
        
        for _ in range(1000):
            client.post('/reviews', json=TEST_REVIEW_DATA)

# 2. Memory Profiling Wrapper
@profile
def memory_test():
    simulation_run()

if __name__ == "__main__":
    print("--- Starting Performance Profiling (cProfile) ---")
    # Run cProfile
    profiler = cProfile.Profile()
    profiler.enable()
    
    simulation_run()
    
    profiler.disable()
    stats = pstats.Stats(profiler).sort_stats('cumtime')
    stats.print_stats(15) 
    
    print("\n--- Starting Memory Profiling ---")
    memory_test()
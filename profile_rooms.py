import cProfile
import pstats
import time
import sys
import os


from memory_profiler import profile
from rooms_service.app import app, cache

TEST_ROOM_DATA = {
    "name": "Profiling Room",
    "capacity": 10,
    "equipment": "Projector,Whiteboard",
    "location": "Building A"
}

def simulation_run():
    with app.app_context():
        client = app.test_client()

        if cache:
            try:
                cache.flushdb()
                print("\n[RESET] Redis Cache Cleared")
            except Exception:
                pass

        # Setup the data
        print("--- 1. Creating Test Data ---")
        for i in range(5): 
            data = TEST_ROOM_DATA.copy()
            data['name'] = f"Profile Room {i}"
            client.post('/rooms', json=data)

       
        # Profiler 1: The reference (Cold Run)
        print("\n--- 2. STARTING REFERENCE PROFILE (Cold Run) ---")
        ref_profiler = cProfile.Profile()
        ref_profiler.enable()

        start_time = time.time()
        for i in range(5):
            client.get(f'/rooms?capacity={5+i}')
        
        ref_profiler.disable()
        print(f"Reference Time: {time.time() - start_time:.2f}s")
    
        # Profiler 2: The optimized (Warm Run)
        print("\n--- 3. STARTING OPTIMIZED PROFILE (Warm Run) ---")
        opt_profiler = cProfile.Profile()
        opt_profiler.enable()

        start_time = time.time()
        for i in range(5):
            client.get(f'/rooms?capacity={5+i}')
            
        opt_profiler.disable()
        print(f"Optimized Time: {time.time() - start_time:.2f}s")

        # Results        
        print("\n" + "="*50)
        print("   RESULT 1: REFERENCE (BEFORE OPTIMIZATION)")
        print("="*50)
        stats_ref = pstats.Stats(ref_profiler).sort_stats('cumtime')
        stats_ref.print_stats(10)

        print("\n" + "="*50)
        print("   RESULT 2: OPTIMIZED (AFTER OPTIMIZATION)")
        print("="*50)
        stats_opt = pstats.Stats(opt_profiler).sort_stats('cumtime')
        stats_opt.print_stats(10)
        

# Memory Profiling Wrapper
@profile
def memory_test():
    # We just run the logic, no need for cProfile here
    with app.app_context():
        client = app.test_client()
        # Reset again for memory test
        if cache: cache.flushdb() 
        
        # Setup
        for i in range(5): 
            data = TEST_ROOM_DATA.copy()
            data['name'] = f"Profile Room {i}"
            client.post('/rooms', json=data)

        # Cold Run
        for i in range(5): client.get(f'/rooms?capacity={5+i}')
        # Warm Run
        for i in range(5): client.get(f'/rooms?capacity={5+i}')

if __name__ == "__main__":
    simulation_run()
    
    print("\n--- Starting Memory Profiling ---")
    memory_test()
import cProfile
import pstats
from memory_profiler import profile
from users_service.app import app, db, User

TEST_USER_DATA = {
    "full_name": "Profiling User",
    "username": "prof_user",
    "email": "prof_user@test.com",
    "password": "password123",
    "role": "Student"
}

def cleanup_db():
    with app.app_context():
        user = User.query.filter_by(username=TEST_USER_DATA['username']).first()
        if user:
            db.session.delete(user)
            db.session.commit()

# 1. Function to Profile
def simulation_run():
    """Runs a sequence of Registration and Login to measure performance."""
    with app.app_context():
        client = app.test_client()

        cleanup_db()
        client.post('/users/register', json=TEST_USER_DATA)
        
        login_data = {
            "username": TEST_USER_DATA['username'],
            "password": TEST_USER_DATA['password']
        }

        for _ in range(100):
            client.post('/users/login', json=login_data)

# 2. Memory Profiling Wrapper
@profile
def memory_test():
    simulation_run()

if __name__ == "__main__":
    print("--- Starting Performance Profiling (cProfile) ---")
 
    profiler = cProfile.Profile()
    profiler.enable()
    
    simulation_run()
    
    profiler.disable()
    stats = pstats.Stats(profiler).sort_stats('cumtime')
    stats.print_stats(10) 
    
    print("\n--- Starting Memory Profiling ---")
    memory_test()
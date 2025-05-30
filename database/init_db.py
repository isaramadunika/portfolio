from database.models import Database

def init_database():
    db = Database()
    print("Database initialized successfully!")

if __name__ == "__main__":
    init_database() 
import os

class Config:
    def __init__(self):
        # Get the absolute path of the config.py file
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Navigate to the parent directory (backend)
        backend_dir = os.path.dirname(current_dir)

        # Build the path to the database file
        self.db_path = os.path.join(backend_dir, 'database', 'coach.db')

        # Convert to SQLite connection string if needed
        self.db_url = f"sqlite:///{self.db_path}"
        # For JDBC style URL:
        self.jdbc_url = f"jdbc:sqlite:{self.db_path}"

    def get_database_path(self):
        """Return the absolute path to the database file"""
        return self.db_path

    def get_database_url(self):
        """Return the SQLite URL for the database"""
        return self.db_url

    def get_jdbc_url(self):
        """Return the JDBC style URL for the database"""
        return self.jdbc_url

if __name__ == '__main__':
    print(Config().get_database_url())

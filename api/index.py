from flask import Flask
from app import app

# This is the main entry point for Vercel
# Export the Flask app instance
application = app

if __name__ == "__main__":
    app.run()

"""
Flask Backend Launcher
Project: IDENTIFY SLOW LEARNERS FOR REMEDIAL TEACHING AND CAPACITY BUILDING FOR INNOVATIVE METHODS
Run: python run_backend.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from backend.app import app

if __name__ == "__main__":
    print("=" * 55)
    print("  SLOW LEARNER DETECTION - Flask API v2.0")
    print("  http://127.0.0.1:5000")
    print("=" * 55)
    app.run(debug=True, host="0.0.0.0", port=5000)

"""
One-shot project setup.
Generates dataset, trains model, seeds default users.
Run: python setup.py
"""
import os, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

print("=" * 60)
print("  SLOW LEARNER DETECTION - PROJECT SETUP")
print("=" * 60)

# Step 1: Generate dataset
print("\n[1/3]  Generating student dataset ...")
from data.generate_dataset import generate_dataset
os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
df = generate_dataset(500)
csv_path = os.path.join(ROOT, "data", "students.csv")
df.to_csv(csv_path, index=False)
print(f"       Saved {len(df)} student records -> {csv_path}")
print(f"       Risk distribution:\n{df['risk_level'].value_counts().to_string()}")
print(f"       Faculty distribution:\n{df['faculty_id'].value_counts().to_string()}")

# Step 2: Train model
print("\n[2/3]  Training Random Forest classifier ...")
from ml.train_model import train_model
train_model()

# Step 3: Seed database and create default users
print("\n[3/3]  Seeding database and creating default users ...")
from backend.database import init_db, load_csv_to_db, create_default_users, create_student_users

init_db()
load_csv_to_db(csv_path)
create_default_users()
n = create_student_users()
print(f"       Default users created: admin, faculty1, faculty2")
print(f"       Student accounts created: {n}")

print("\n" + "=" * 60)
print("  SETUP COMPLETE")
print("=" * 60)
print("""
  Default Login Credentials:
  +-----------+------------+-------------+
  | Role      | Username   | Password    |
  +-----------+------------+-------------+
  | Admin     | admin      | admin123    |
  | Faculty   | faculty1   | faculty123  |
  | Faculty   | faculty2   | faculty123  |
  | Student   | stu0001    | student123  |
  | Student   | stu0002    | student123  |
  |  ...      | stu####    | student123  |
  +-----------+------------+-------------+

  Next steps:
    Terminal 1:  python run_backend.py
    Terminal 2:  streamlit run frontend/dashboard.py
    Browser:     http://localhost:8501
""")

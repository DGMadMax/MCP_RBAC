"""
Seed Employees Table
Populates the 'employees' table with dummy data for SQL tool testing.
"""
import random
from datetime import datetime, timedelta
from faker import Faker
from app.database import SessionLocal
from app.models import Employee

fake = Faker()

DEPARTMENTS = ["engineering", "sales", "marketing", "hr", "finance"]
ROLES = {
    "engineering": ["Software Engineer", "Senior Engineer", "DevOps Engineer", "Engineering Manager"],
    "sales": ["Sales Representative", "Account Executive", "Sales Manager"],
    "marketing": ["Marketing Specialist", "Content Writer", "Marketing Manager"],
    "hr": ["HR Specialist", "Recruiter", "HR Manager"],
    "finance": ["Accountant", "Financial Analyst", "Finance Manager"]
}

def seed_employees():
    db = SessionLocal()
    try:
        # Check if data exists
        if db.query(Employee).count() > 0:
            print("Employees table already has data. Skipping.")
            return

        print("Seeding employees...")
        employees = []
        
        for dept in DEPARTMENTS:
            for _ in range(10): # 10 employees per department
                role = random.choice(ROLES[dept])
                
                emp = Employee(
                    employee_id=f"EMP{random.randint(1000, 9999)}",
                    full_name=fake.name(),
                    role=role,
                    department=dept,
                    email=fake.email(),
                    location=random.choice(["New York", "London", "Remote", "San Francisco"]),
                    date_of_birth=fake.date_of_birth(minimum_age=22, maximum_age=60),
                    date_of_joining=fake.date_between(start_date='-5y', end_date='today'),
                    salary=random.randint(50000, 150000),
                    leave_balance=random.randint(0, 30),
                    leaves_taken=random.randint(0, 10),
                    attendance_pct=random.uniform(90.0, 100.0),
                    performance_rating=random.randint(1, 5),
                    last_review_date=fake.date_between(start_date='-1y', end_date='today')
                )
                db.add(emp)
                employees.append(emp)
        
        db.commit()
        print(f"Successfully seeded {len(employees)} employees across {len(DEPARTMENTS)} departments.")
        
    except Exception as e:
        print(f"Error seeding employees: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_employees()

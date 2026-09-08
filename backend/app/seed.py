"""Idempotent database seeder for development and demo environments.

Usage:
    python -m app.seed
"""

from seed_demo_data import seed_buyers

if __name__ == "__main__":
    print("🌱 Running database seed...")
    seed_buyers()

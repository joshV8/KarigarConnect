"""Demo Data Seeder for B2B Wholesale Buyers.

NOTE: All companies and contact profiles listed here are purely FICTIONAL demo data
created for hackathon evaluation and demonstration of market-linkage capabilities.
"""

from app.database import SessionLocal, engine, Base
import app.models
from app.models.buyer import Buyer

# Initialize tables if not already present
Base.metadata.create_all(bind=engine)

DEMO_BUYERS = [
    {
        "company": "EcoCraft Wholesale",
        "name": "Rajesh Sharma",
        "email": "procurement@ecocraft-demo.in",
        "phone": "+91-98200-11223",
        "location": "Mumbai",
        "category": "Home Decor",
        "description": "Large-scale distributor looking for sustainable bamboo, cane, and jute home decor items for retail chains.",
    },
    {
        "company": "Indian Handicraft Retail",
        "name": "Pooja Verma",
        "email": "buyers@indianhandicraft-demo.com",
        "phone": "+91-98111-44556",
        "location": "Delhi",
        "category": "Handicrafts",
        "description": "Procures handcrafted decorative items, traditional artifacts, and regional folk art for urban gift shops.",
    },
    {
        "company": "Sustainable Living Store",
        "name": "Ananya Iyer",
        "email": "orders@sustainableliving-demo.in",
        "phone": "+91-99800-77889",
        "location": "Bangalore",
        "category": "Eco-Friendly Lifestyle",
        "description": "Boutique retail chain sourcing zero-plastic, organic bamboo, terracotta kitchenware, and handloom home accessories.",
    },
    {
        "company": "Traditional Crafts Distributor",
        "name": "Vikram Rathore",
        "email": "contact@rajasthantradition-demo.com",
        "phone": "+91-94140-55667",
        "location": "Jaipur",
        "category": "Pottery & Terracotta",
        "description": "Wholesale exporter supplying Jaipur blue pottery, clay cookware, and brass artifacts to global hotel chains.",
    },
    {
        "company": "Home Decor Wholesale India",
        "name": "Mehul Patel",
        "email": "supply@homedecorwholesale-demo.in",
        "phone": "+91-98790-33445",
        "location": "Ahmedabad",
        "category": "Home Decor",
        "description": "Bulk procurement agency supplying woven storage baskets, wall hangings, and artisanal table lamps to interior designers.",
    },
    {
        "company": "Artisan Goods Marketplace",
        "name": "Debashis Sen",
        "email": "partners@artisangoods-demo.org",
        "phone": "+91-98300-66778",
        "location": "Kolkata",
        "category": "Textiles & Handloom",
        "description": "Federation sourcing hand-woven silk, cotton textiles, kantha embroidery, and clay pottery directly from craft clusters.",
    },
    {
        "company": "Eco Home Products",
        "name": "Snehal Kulkarni",
        "email": "procure@ecohome-demo.co.in",
        "phone": "+91-98220-88990",
        "location": "Pune",
        "category": "Bamboo & Wooden Craft",
        "description": "Specializes in high-volume orders for handcrafted bamboo storage, wooden cutlery, and eco-friendly office stationery.",
    },
    {
        "company": "Handmade Products Trading",
        "name": "Karthik Raman",
        "email": "trades@handmade-demo.com",
        "phone": "+91-98400-22334",
        "location": "Chennai",
        "category": "Metal & Brass Crafts",
        "description": "South Indian wholesale distributor for dokra brass craft, bell metal decor, and hand-carved stone artifacts.",
    },
]


def seed_buyers():
    """Seed the database with fictional demo B2B buyers in an idempotent manner."""
    db = SessionLocal()
    try:
        added_count = 0
        for data in DEMO_BUYERS:
            existing = (
                db.query(Buyer)
                .filter(Buyer.company == data["company"])
                .first()
            )
            if not existing:
                buyer = Buyer(**data)
                db.add(buyer)
                added_count += 1

        db.commit()
        total_count = db.query(Buyer).count()
        print(f"✓ Seed complete. Added {added_count} new buyers. Total in DB: {total_count}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_buyers()

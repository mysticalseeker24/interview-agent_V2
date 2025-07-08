"""
User Service Database Seeder
Pre-populate the database with initial users for testing and development.
"""
import asyncio
from app.core.database import AsyncSessionLocal, init_db
from app.models.user import User
from app.core.security import hash_password


async def seed_users():
    """Seed the database with initial users."""
    
    # Initialize database
    await init_db()
    
    # Pre-defined users
    users_data = [
        {
            "email": "saksham.mishra2402@gmail.com",
            "password": "12345678",
            "full_name": "Saksham Mishra",
            "is_admin": True  # Make first user admin
        },
        {
            "email": "georgidimitroviliev2002@gmail.com", 
            "password": "12345678",
            "full_name": "Georgi Dimitrov"
        },
        {
            "email": "george.iliev.24@ucl.ac.uk",
            "password": "12345678",
            "full_name": "George Iliev"
        },
        {
            "email": "sakshamm510@gmail.com",
            "password": "12345678", 
            "full_name": "Saksham M"
        }
    ]
    
    async with AsyncSessionLocal() as db:
        try:
            for user_data in users_data:
                # Check if user already exists
                from sqlalchemy import select
                result = await db.execute(select(User).where(User.email == user_data["email"]))
                existing_user = result.scalars().first()
                
                if existing_user:
                    print(f"User {user_data['email']} already exists, skipping...")
                    continue
                
                # Create new user
                hashed_password = hash_password(user_data["password"])
                new_user = User(
                    email=user_data["email"],
                    hashed_password=hashed_password,
                    full_name=user_data["full_name"],
                    is_admin=user_data.get("is_admin", False),
                    is_active=True
                )
                
                db.add(new_user)
                print(f"✅ Added user: {user_data['email']}")
            
            await db.commit()
            print("\n🎉 Database seeding completed successfully!")
            
        except Exception as e:
            await db.rollback()
            print(f"❌ Error seeding database: {e}")
            raise


async def list_users():
    """List all users in the database."""
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        result = await db.execute(select(User))
        users = result.scalars().all()
        
        print("\n📋 Current users in database:")
        print("-" * 80)
        for user in users:
            admin_flag = " (ADMIN)" if user.is_admin else ""
            active_flag = " (INACTIVE)" if not user.is_active else ""
            print(f"ID: {user.id} | Email: {user.email} | Name: {user.full_name}{admin_flag}{active_flag}")
        print("-" * 80)
        print(f"Total users: {len(users)}")


if __name__ == "__main__":
    print("🚀 TalentSync User Service - Database Seeder")
    print("=" * 50)
    
    # Run seeding
    asyncio.run(seed_users())
    
    # List all users
    asyncio.run(list_users())
    
    print("\n📝 Login credentials for testing:")
    print("Email: saksham.mishra2402@gmail.com | Password: 12345678 (Admin)")
    print("Email: georgidimitroviliev2002@gmail.com | Password: 12345678")
    print("Email: george.iliev.24@ucl.ac.uk | Password: 12345678") 
    print("Email: sakshamm510@gmail.com | Password: 12345678")

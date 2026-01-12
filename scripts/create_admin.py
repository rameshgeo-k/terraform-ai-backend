"""
Script to create initial admin user.
"""
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.admin import Admin
from app.core.security import get_password_hash
from app.core.config import settings


def create_initial_admin():
    """Create initial admin user if not exists."""
    db: Session = SessionLocal()
    
    try:
        # Check if admin exists
        existing_admin = db.query(Admin).filter(Admin.email == settings.ADMIN_EMAIL).first()
        
        if existing_admin:
            print(f"✓ Admin user already exists: {settings.ADMIN_EMAIL}")
            return
        
        # Create admin
        admin = Admin(
            email=settings.ADMIN_EMAIL,
            username="admin",
            hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
            full_name="System Administrator",
            is_active=True
        )
        
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        print(f"✓ Created admin user: {settings.ADMIN_EMAIL}")
        print(f"  Password: {settings.ADMIN_PASSWORD}")
        print("  ⚠️  Please change the password in production!")
        
    except Exception as e:
        print(f"✗ Error creating admin: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_initial_admin()

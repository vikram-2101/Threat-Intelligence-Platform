import asyncio
import uuid
from sqlalchemy import select, func
from app.db.session import AsyncSessionLocal
from app.models.user import User, Role, UserRole, RoleName
from app.core.security import get_password_hash

async def seed_data():
    async with AsyncSessionLocal() as db:
        async with db.begin():
            # 1. Seed Roles
            roles_data = [
                {"name": RoleName.ADMIN, "description": "Full system access", "permissions": {"all": True}},
                {"name": RoleName.ANALYST, "description": "Analyst access to indicators and notes", "permissions": {"read": True, "note": True, "adjust": True}},
                {"name": RoleName.API_CONSUMER, "description": "Internal or external API consumer", "permissions": {"read": True}},
            ]
            
            role_objs = {}
            for rd in roles_data:
                res = await db.execute(select(Role).where(Role.name == rd["name"]))
                role = res.scalar_one_or_none()
                if not role:
                    role = Role(**rd)
                    db.add(role)
                    await db.flush()
                role_objs[rd["name"]] = role

            # 2. Seed Default Admin User
            admin_username = "admin"
            res = await db.execute(select(User).where(User.username == admin_username))
            admin_user = res.scalar_one_or_none()
            
            if not admin_user:
                admin_user = User(
                    username=admin_username,
                    email="admin@tip.example.com",
                    password_hash=get_password_hash("admin123"),  # In production, this would be changed immediately
                    is_active=True
                )
                db.add(admin_user)
                await db.flush()
                
                # Assign Admin Role
                user_role = UserRole(
                    user_id=admin_user.id,
                    role_id=role_objs[RoleName.ADMIN].id,
                    granted_at=func.now(),
                    granted_by=admin_user.id  # Self-assigned for initial seed
                )
                db.add(user_role)

            # 3. Seed Default Analyst User
            analyst_username = "analyst"
            res = await db.execute(select(User).where(User.username == analyst_username))
            analyst_user = res.scalar_one_or_none()

            if not analyst_user:
                analyst_user = User(
                    username=analyst_username,
                    email="analyst@tip.example.com",
                    password_hash=get_password_hash("analyst123"),
                    is_active=True
                )
                db.add(analyst_user)
                await db.flush()

                # Assign Analyst Role
                user_role = UserRole(
                    user_id=analyst_user.id,
                    role_id=role_objs[RoleName.ANALYST].id,
                    granted_at=func.now(),
                    granted_by=admin_user.id
                )
                db.add(user_role)

            # 4. Seed Placeholder Sources
            from app.models.source import Source, SourceCategory, TrustTier
            source_name = "Community Intel"
            res = await db.execute(select(Source).where(Source.name == source_name))
            if not res.scalar_one_or_none():
                placeholder_source = Source(
                    name=source_name,
                    category=SourceCategory.community,
                    trust_tier=TrustTier.LOW,
                    default_weight=0.5,
                    pull_url="http://example.com/feed.txt",
                    is_active=False,
                    consecutive_failures=0
                )
                db.add(placeholder_source)

            print("Database seeding completed.")

if __name__ == "__main__":
    asyncio.run(seed_data())

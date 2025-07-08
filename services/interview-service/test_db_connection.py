import asyncio
import asyncpg

async def test_connection():
    try:
        conn = await asyncpg.connect(
            user='talentsync',
            password='secret123',
            database='talentsync',
            host='localhost',
            port=5432
        )
        result = await conn.fetchval('SELECT 1')
        await conn.close()
        print(f"Database connection successful! Result: {result}")
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

asyncio.run(test_connection())

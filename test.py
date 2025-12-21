import asyncio
from ai_client import classify_task

async def main():
    category = await classify_task("купить новые шторы на озоне")
    print("Категория:", category)

if __name__ == "__main__":
    asyncio.run(main())

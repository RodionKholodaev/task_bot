import ssl
import aiohttp
import asyncio

async def main():
    url = "https://api.telegram.org"
    print("Requesting:", url)

    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=20) as resp:
            print("Status:", resp.status)
            text = await resp.text()
            print("First 200 chars:", text[:200])

if __name__ == "__main__":
    asyncio.run(main())

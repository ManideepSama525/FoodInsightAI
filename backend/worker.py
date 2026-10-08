import asyncio
from app.jobs.runtime import settings, semaphore

async def main():
    print(f"FoodInsightAI worker ready: queue={settings.queue_name} concurrency={settings.concurrency}")
    async with semaphore:
        await asyncio.sleep(0)

if __name__ == "__main__":
    asyncio.run(main())

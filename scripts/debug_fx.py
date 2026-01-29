import asyncio
import sys
import os
import inspect

# Add current dir to path
sys.path.append(os.getcwd())

from backend.app.services.market import MarketDataService

async def test():
    try:
        print("Checking MarketDataService location...")
        print("Source File:", inspect.getfile(MarketDataService))
        
        m = MarketDataService()
        
        print("\nChecking get_live_prices property...")
        func = m.get_live_prices
        print("Is coroutine function?", asyncio.iscoroutinefunction(func))
        print("Signature:", inspect.signature(func))
        
        print("\nCalling get_live_prices directly with one symbol...")
        try:
            res = func(["USDCZK=X"])
            print("Return type:", type(res))
            if asyncio.iscoroutine(res):
                print("Result is coroutine, awaiting...")
                data = await res
                print("Data fetched successfully.")
            else:
                print("Result is NOT coroutine. Value:", res)
        except Exception as e:
            print("Error calling get_live_prices:", e)
            import traceback
            traceback.print_exc()

        print("\nCalling get_live_fx_rates...")
        try:
            fx = await m.get_live_fx_rates(["USD"], "CZK")
            print("FX Rates Result:", fx)
        except Exception as e:
            print("Error calling get_live_fx_rates:", e)
            import traceback
            traceback.print_exc()

    except Exception as e:
        print(f"Global Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test())

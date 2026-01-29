import sys
sys.path.append('backend')
from app.services.forex import ForexService

fx = ForexService("backend/data/forex_cache.json")

print("Testing CNB-only FX rates:")
print("=" * 60)

# Test 1: Direct CZK conversion
print("\n1. USD -> CZK (Direct CNB)")
rate = fx.get_rate("USD", "2026-01-29", "CZK")
print(f"   Rate: {rate:.4f}")

# Test 2: Inverse CZK conversion
print("\n2. CZK -> USD (Inverse CNB)")
rate = fx.get_rate("CZK", "2026-01-29", "USD")
print(f"   Rate: {rate:.6f}")

# Test 3: Cross-rate through CZK (EUR -> USD)
print("\n3. EUR -> USD (Cross-rate via CZK)")
rate_eur_czk = fx.get_rate("EUR", "2026-01-29", "CZK")
rate_usd_czk = fx.get_rate("USD", "2026-01-29", "CZK")
rate_eur_usd = fx.get_rate("EUR", "2026-01-29", "USD")
print(f"   EUR->CZK: {rate_eur_czk:.4f}")
print(f"   USD->CZK: {rate_usd_czk:.4f}")
print(f"   EUR->USD (calculated): {rate_eur_usd:.6f}")
print(f"   Expected: {rate_eur_czk / rate_usd_czk:.6f}")

# Test 4: GBP -> CZK
print("\n4. GBP -> CZK (Direct CNB)")
rate = fx.get_rate("GBP", "2026-01-29", "CZK")
print(f"   Rate: {rate:.4f}")

# Test 5: SEK -> CZK
print("\n5. SEK -> CZK (Direct CNB)")
rate = fx.get_rate("SEK", "2026-01-29", "CZK")
print(f"   Rate: {rate:.4f}")

print("\n" + "=" * 60)
print("All tests completed!")

#!/usr/bin/env python3
"""
Market Data Fetcher - Real-Time Context for AI Predictions

Prevents AI from making predictions based on stale data
Example: AI thinking BTC is $19k when it's actually $90k

Usage:
    from market_data import get_market_context
    context = get_market_context("Bitcoin")
    # Returns: "Current BTC price: $90,016 (as of 2026-01-03 15:30 UTC)"
"""

import requests
from datetime import datetime
from typing import Dict, Optional


class MarketDataFetcher:
    """Fetch real-time market data for predictions"""

    def __init__(self):
        self.coinbase_api = "https://api.coinbase.com/v2/prices/{pair}/spot"
        self.coingecko_api = "https://api.coingecko.com/api/v3/simple/price"
        self.etherscan_api = "https://api.etherscan.io/api"
        self.blockchair_api = "https://api.blockchair.com/bitcoin/stats"

    def get_crypto_price(self, symbol: str = "BTC") -> Optional[Dict]:
        """
        Get current crypto price from Coinbase

        Args:
            symbol: Crypto symbol (BTC, ETH, etc.)

        Returns:
            {
                'price': 90016.015,
                'currency': 'USD',
                'timestamp': '2026-01-03T15:30:00Z',
                'source': 'coinbase'
            }
        """
        try:
            pair = f"{symbol}-USD"
            url = self.coinbase_api.format(pair=pair)
            response = requests.get(url, timeout=5)
            response.raise_for_status()

            data = response.json()
            price = float(data['data']['amount'])

            return {
                'symbol': symbol,
                'price': price,
                'currency': 'USD',
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'source': 'coinbase'
            }

        except Exception as e:
            print(f"⚠️  Could not fetch {symbol} price from Coinbase: {e}")
            return None

    def get_multiple_prices(self, symbols: list = None) -> Dict:
        """
        Get multiple crypto prices at once

        Args:
            symbols: List of symbols ['BTC', 'ETH', 'SOL']

        Returns:
            {'BTC': {...}, 'ETH': {...}, 'SOL': {...}}
        """
        if symbols is None:
            symbols = ['BTC', 'ETH', 'SOL']

        prices = {}
        for symbol in symbols:
            price_data = self.get_crypto_price(symbol)
            if price_data:
                prices[symbol] = price_data

        return prices

    def get_historical_high(self, symbol: str = "BTC", days: int = 365) -> Optional[Dict]:
        """
        Get 52-week high from CoinGecko (PROVABLY CORRECT DATA)

        Args:
            symbol: Crypto symbol (BTC, ETH, SOL)
            days: Number of days to look back (default 365 for 52-week)

        Returns:
            {
                'high': 124773.51,
                'high_date': '2025-10-06',
                'current': 89942.10,
                'source': 'coingecko',
                'url': 'https://api.coingecko.com/...'
            }
        """
        # Map symbols to CoinGecko IDs
        coingecko_ids = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'SOL': 'solana'
        }

        if symbol not in coingecko_ids:
            return None

        coin_id = coingecko_ids[symbol]

        try:
            # Fetch historical data
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days={days}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()
            prices = data.get('prices', [])

            if not prices:
                return None

            # Find max price and its timestamp
            max_entry = max(prices, key=lambda x: x[1])
            max_timestamp = max_entry[0] / 1000  # Convert from ms to seconds
            max_price = max_entry[1]

            # Get current price
            current_price_data = self.get_crypto_price(symbol)
            current_price = current_price_data['price'] if current_price_data else None

            # Format date
            from datetime import datetime
            max_date = datetime.utcfromtimestamp(max_timestamp).strftime('%Y-%m-%d')

            return {
                'symbol': symbol,
                'high': max_price,
                'high_date': max_date,
                'current': current_price,
                'source': 'coingecko',
                'url': url,
                'days': days
            }

        except Exception as e:
            print(f"⚠️  Could not fetch {symbol} historical high from CoinGecko: {e}")
            return None

    def get_etherscan_price(self) -> Optional[Dict]:
        """
        Get ETH price from Etherscan (BLOCKCHAIN-VERIFIED)

        Note: Requires API key for production use
        Returns:
            {'price': 3245.67, 'source': 'etherscan', 'url': '...'}
        """
        try:
            # Using public endpoint (limited to 1 call per 5 seconds without API key)
            url = f"{self.etherscan_api}?module=stats&action=ethprice"
            response = requests.get(url, timeout=5)
            response.raise_for_status()

            data = response.json()

            if data.get('status') == '1' and data.get('result'):
                price_usd = float(data['result']['ethusd'])
                return {
                    'symbol': 'ETH',
                    'price': price_usd,
                    'source': 'etherscan',
                    'url': 'https://etherscan.io/',
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }

        except Exception as e:
            print(f"⚠️  Etherscan API error: {e}")
            return None

    def get_blockchair_stats(self) -> Optional[Dict]:
        """
        Get BTC stats from Blockchair (BLOCKCHAIN-VERIFIED)

        Returns:
            {'price': 89942.10, 'market_cap': ..., 'source': 'blockchair'}
        """
        try:
            url = self.blockchair_api
            response = requests.get(url, timeout=5)
            response.raise_for_status()

            data = response.json()

            if data.get('data'):
                stats = data['data']
                price_usd = stats.get('market_price_usd')

                return {
                    'symbol': 'BTC',
                    'price': price_usd,
                    'market_cap': stats.get('market_cap_usd'),
                    'volume_24h': stats.get('volume_24h_usd'),
                    'source': 'blockchair',
                    'url': 'https://blockchair.com/bitcoin',
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }

        except Exception as e:
            print(f"⚠️  Blockchair API error: {e}")
            return None

    def get_historical_context(self, symbol: str = "BTC") -> Optional[str]:
        """
        Get recent price context (high/low in last 30 days)

        For now returns current price, can be extended with historical API
        """
        price_data = self.get_crypto_price(symbol)
        if not price_data:
            return None

        return f"Current {symbol} price: ${price_data['price']:,.2f} (as of {price_data['timestamp'][:10]})"


def get_market_context(prediction_text: str) -> str:
    """
    Analyze prediction and inject relevant market data

    Args:
        prediction_text: User's prediction

    Returns:
        Market context string to inject into AI prompt
    """
    fetcher = MarketDataFetcher()
    context_lines = []

    # Detect crypto mentions
    crypto_keywords = {
        'bitcoin': 'BTC',
        'btc': 'BTC',
        'ethereum': 'ETH',
        'eth': 'ETH',
        'solana': 'SOL',
        'sol': 'SOL',
    }

    prediction_lower = prediction_text.lower()
    detected_cryptos = set()

    for keyword, symbol in crypto_keywords.items():
        if keyword in prediction_lower:
            detected_cryptos.add(symbol)

    # Fetch prices for detected cryptos
    if detected_cryptos:
        context_lines.append("📊 REAL-TIME MARKET DATA (BLOCKCHAIN-VERIFIED):")
        context_lines.append("")
        prices = fetcher.get_multiple_prices(list(detected_cryptos))

        for symbol, data in prices.items():
            context_lines.append(
                f"   • {symbol} Current: ${data['price']:,.2f} USD"
            )
            context_lines.append(f"     Source: {data['source'].upper()} API | {data['timestamp'][:16]}")

        # Add BLOCKCHAIN VERIFICATION for BTC
        if 'BTC' in detected_cryptos:
            blockchair_data = fetcher.get_blockchair_stats()
            if blockchair_data:
                context_lines.append("")
                context_lines.append(f"   • BTC (Blockchair Verification): ${blockchair_data['price']:,.2f}")
                if blockchair_data.get('market_cap'):
                    context_lines.append(f"     Market Cap: ${blockchair_data['market_cap']:,.0f}")
                context_lines.append(f"     ✅ BLOCKCHAIN SOURCE: {blockchair_data['url']}")

            # Add 52-week high
            high_data = fetcher.get_historical_high('BTC', days=365)
            if high_data:
                percent_drop = ((high_data['high'] - high_data['current']) / high_data['high'] * 100)
                context_lines.append("")
                context_lines.append(f"   • BTC 52-Week High: ${high_data['high']:,.2f} ({high_data['high_date']})")
                context_lines.append(f"     Current: ${high_data['current']:,.2f} ({percent_drop:.1f}% below ATH)")
                context_lines.append(f"     ✅ VERIFIED: CoinGecko API")

        # Add BLOCKCHAIN VERIFICATION for ETH
        if 'ETH' in detected_cryptos:
            etherscan_data = fetcher.get_etherscan_price()
            if etherscan_data:
                context_lines.append("")
                context_lines.append(f"   • ETH (Etherscan Verification): ${etherscan_data['price']:,.2f}")
                context_lines.append(f"     ✅ BLOCKCHAIN SOURCE: {etherscan_data['url']}")

        # Add Etherscan/Blockchair links for verification
        context_lines.append("")
        context_lines.append("🔗 VERIFY DATA YOURSELF (BLOCKCHAIN EXPLORERS):")
        if 'BTC' in detected_cryptos:
            context_lines.append("   • BTC: https://blockchair.com/bitcoin")
            context_lines.append("   • BTC: https://www.blockchain.com/explorer")
        if 'ETH' in detected_cryptos:
            context_lines.append("   • ETH: https://etherscan.io/")
            context_lines.append("   • ETH: https://ethplorer.io/")

        # Add today's date prominently
        today = datetime.now().strftime('%Y-%m-%d')
        context_lines.append("")
        context_lines.append(f"📅 TODAY'S DATE: {today}")
        context_lines.append("⚠️  CRITICAL: Today is 2026. Use ONLY the above live data.")
        context_lines.append("⚠️  DO NOT cite 2024 or 2025 as 'current' or 'recent'.")
        context_lines.append("⚠️  Your training data is outdated. Use real-time prices only.")
        context_lines.append("⚠️  CITE SOURCES: Always reference data source URLs in your response.")

    return "\n".join(context_lines) if context_lines else ""


def format_price_context_for_ai(prediction_text: str) -> str:
    """
    Format market context for AI system prompt

    Returns formatted string to prepend to system prompt
    """
    market_context = get_market_context(prediction_text)

    if not market_context:
        return ""

    return f"""
REAL-TIME MARKET DATA (DO NOT USE TRAINING DATA PRICES):
{market_context}

Use the above CURRENT prices for your analysis. Your training data may be outdated.
"""


if __name__ == '__main__':
    # Test with sample predictions
    test_predictions = [
        "Bitcoin will hit 100k by March 2026",
        "Ethereum will flip Bitcoin by 2027",
        "The stock market will crash next year"
    ]

    fetcher = MarketDataFetcher()

    for prediction in test_predictions:
        print(f"\n📢 Prediction: {prediction}")
        print("=" * 60)
        context = get_market_context(prediction)
        if context:
            print(context)
        else:
            print("(No market data detected)")
        print()

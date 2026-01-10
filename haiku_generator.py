#!/usr/bin/env python3
"""
Haiku Generator for Traffic Blackhole

Generates mysterious haikus about lost traffic, dying cookies, and the void.
"""

import random

TRAFFIC_HAIKUS = [
    # Cookie Death
    [
        "Your cookie arrived",
        "Now it fades into the void",
        "Traffic goes nowhere"
    ],
    [
        "Referrer unknown",
        "You emerged from nothingness",
        "Back you shall return"
    ],
    [
        "Cookies crumble here",
        "Like breadcrumbs in the forest",
        "No path leads back home"
    ],

    # Visitor Numbers
    [
        "Twenty-four lost souls",
        "Wandering this domain maze",
        "You are twenty-five"
    ],
    [
        "First one to arrive",
        "Or the millionth to be trapped",
        "Numbers mean nothing"
    ],
    [
        "Visitor counter",
        "Spins backward into the past",
        "Time has no meaning"
    ],

    # Traffic Mystery
    [
        "Where did you come from",
        "Where will this traffic end up",
        "Questions fade to black"
    ],
    [
        "Analytics show",
        "Traffic entering the void",
        "Exit data: null"
    ],
    [
        "Bandwidth consumed here",
        "Packets dissolve in the dark",
        "Nothing to report"
    ],

    # The Game
    [
        "You try to escape",
        "Each click leads deeper inward",
        "There is no way out"
    ],
    [
        "Leaderboard displays",
        "Your rank among the voided",
        "First place means you lose"
    ],
    [
        "The game has no rules",
        "Winning is impossible",
        "Still you must play on"
    ],

    # Domain Blackhole
    [
        "Soulfra dot com waits",
        "Hungry for your click data",
        "Feed the algorithm"
    ],
    [
        "Four domains orbit",
        "Around this central darkness",
        "Gravity pulls all"
    ],
    [
        "QR codes scatter",
        "Each one a portal inward",
        "Scan at your own risk"
    ],

    # Meta/Hilarious
    [
        "Server responds fast",
        "But where do responses go",
        "Into your browser"
    ],
    [
        "HTTPS secured",
        "Your data encrypted well",
        "Still we know you're here"
    ],
    [
        "Clear your cache now please",
        "Too late we've already seen",
        "Everything you clicked"
    ],
]

def get_random_haiku():
    """Get a random haiku as formatted text"""
    haiku = random.choice(TRAFFIC_HAIKUS)
    return '\n'.join(haiku)

def get_visitor_haiku(visitor_num):
    """Generate personalized haiku with visitor number"""
    templates = [
        [
            f"Visitor {visitor_num}",
            "Welcome to the endless void",
            "You cannot leave now"
        ],
        [
            f"{visitor_num} souls before",
            "All consumed by the blackhole",
            "Your turn has arrived"
        ],
        [
            "You are lost soul number",
            f"{visitor_num} in this dark maze",
            "Hope fades completely"
        ],
    ]
    haiku = random.choice(templates)
    return '\n'.join(haiku)

def get_referrer_haiku(referrer):
    """Generate haiku based on referrer"""
    if not referrer or referrer == "direct":
        return get_random_haiku()

    # Extract domain from referrer
    domain = referrer.split('/')[2] if '/' in referrer else referrer

    return f"""You came from {domain[:20]}
Now trapped in the traffic void
Referrer data lost"""

def get_cookie_death_haiku(cookie_count):
    """Haiku about dying cookies"""
    if cookie_count == 0:
        return """No cookies survived
All crumbled in the darkness
Sweet data is gone"""
    elif cookie_count == 1:
        return """One cookie remains
Clinging to life in the void
Soon it too shall fade"""
    else:
        return f"""  {cookie_count} cookies died here
Their crumbs scattered in the dark
Data graveyards fill"""

if __name__ == '__main__':
    print("=== Random Haiku ===")
    print(get_random_haiku())
    print("\n=== Visitor #42 Haiku ===")
    print(get_visitor_haiku(42))
    print("\n=== Referrer Haiku ===")
    print(get_referrer_haiku("https://google.com/search"))
    print("\n=== Cookie Death Haiku ===")
    print(get_cookie_death_haiku(7))

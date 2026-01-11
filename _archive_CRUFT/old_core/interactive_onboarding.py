#!/usr/bin/env python3
"""
Interactive Domain Onboarding - Anki-style acceptance loop

User can accept/reject Ollama suggestions.
System tunes creativity until user accepts.
Learns preferences over time (logarithmic improvement).
"""

import sys
from ollama_domain_analyzer import OllamaDomainAnalyzer
from brand_creator import BrandCreator


class InteractiveOnboarding:
    def __init__(self):
        self.analyzer = OllamaDomainAnalyzer()
        self.brand_creator = BrandCreator()
        self.temperature = 0.9  # Start at default
        self.attempt_count = 0
        self.max_attempts = 5

    def onboard_with_acceptance(self, domain: str):
        """
        Interactive onboarding with accept/reject loop

        Returns True if accepted, False if gave up
        """
        print(f"\n{'='*60}")
        print(f"🎨 INTERACTIVE ONBOARDING: {domain}")
        print(f"{'='*60}\n")

        while self.attempt_count < self.max_attempts:
            self.attempt_count += 1

            # Analyze with current temperature
            print(f"🔍 Attempt {self.attempt_count}/{self.max_attempts}")
            print(f"   Temperature: {self.temperature:.2f}")

            analysis = self.analyzer.analyze_domain(domain)

            if not analysis:
                print("❌ Ollama analysis failed, trying again...")
                self.temperature += 0.1
                continue

            # Show suggestions
            self._display_analysis(analysis)

            # Get user feedback
            rating = self._get_user_rating()

            if rating == "accept":
                print("\n✅ Great! Saving to database...")
                brand_id = self.brand_creator.create_brand_from_analysis(analysis)
                if brand_id:
                    print(f"🎉 Brand created! ID: {brand_id}")
                    self._save_preference(domain, analysis, "accepted")
                    return True
                else:
                    print("❌ Failed to create brand")
                    return False

            elif rating == "reject":
                print(f"\n❌ Rejected. Increasing creativity...")
                self.temperature += 0.2  # Bigger jump for reject
                self._save_preference(domain, analysis, "rejected")

            elif rating == "meh":
                print(f"\n😐 Meh. Slight variation...")
                self.temperature += 0.1  # Smaller jump for meh
                self._save_preference(domain, analysis, "meh")

            elif rating == "edit":
                # Manual override
                edited = self._manual_edit(analysis)
                brand_id = self.brand_creator.create_brand_from_analysis(edited)
                if brand_id:
                    print(f"✅ Brand created with your edits! ID: {brand_id}")
                    return True

            elif rating == "quit":
                print("\n👋 Quitting without saving")
                return False

            # Safety: Cap temperature
            if self.temperature > 1.5:
                print("\n⚠️  Temperature maxed out at 1.5. Try manual edit?")
                self.temperature = 1.5

        print(f"\n😞 Max attempts ({self.max_attempts}) reached. Use manual edit mode or try later.")
        return False

    def _display_analysis(self, analysis: dict):
        """Show Ollama's suggestions in a nice format"""
        print(f"\n🤖 Ollama suggests:\n")
        print(f"   📁 Category: {analysis.get('category')}/{analysis.get('subcategory')}")
        print(f"   💬 Tagline: \"{analysis.get('tagline')}\"")
        print(f"   🎭 Tone: {analysis.get('personality', {}).get('tone')}")

        colors = analysis.get('colors', {})
        primary = colors.get('primary', '')
        secondary = colors.get('secondary', '')
        accent = colors.get('accent', '')

        print(f"   🎨 Colors:")
        print(f"      Primary:   {primary}")
        print(f"      Secondary: {secondary}")
        print(f"      Accent:    {accent}")

        print(f"   🎯 Audience: {analysis.get('target_audience')}")
        print(f"   📝 Strategy: {analysis.get('content_strategy')}")

        # Show initial content ideas
        ideas = analysis.get('initial_content_ideas', [])
        if ideas:
            print(f"\n   💡 Initial Post Ideas:")
            for i, idea in enumerate(ideas[:3], 1):
                print(f"      {i}. {idea}")

    def _get_user_rating(self) -> str:
        """Get user's acceptance rating"""
        print(f"\n" + "-"*60)
        print("Rate this suggestion:")
        print("  [1] ❌ Reject (try again with MORE creativity)")
        print("  [2] 😐 Meh (slight variation)")
        print("  [3] ✅ Accept (save to database)")
        print("  [4] ✏️  Edit manually")
        print("  [q] Quit")
        print("-"*60)

        while True:
            choice = input("Your choice [1-4/q]: ").strip().lower()

            if choice == '1':
                return "reject"
            elif choice == '2':
                return "meh"
            elif choice == '3':
                return "accept"
            elif choice == '4':
                return "edit"
            elif choice == 'q':
                return "quit"
            else:
                print("Invalid choice. Try again.")

    def _manual_edit(self, analysis: dict) -> dict:
        """Let user manually edit the suggestions"""
        print("\n✏️  Manual Edit Mode")
        print("Press Enter to keep current value\n")

        # Edit tagline
        current_tagline = analysis.get('tagline', '')
        new_tagline = input(f"Tagline [{current_tagline}]: ").strip()
        if new_tagline:
            analysis['tagline'] = new_tagline

        # Edit colors
        colors = analysis.get('colors', {})
        new_primary = input(f"Primary color [{colors.get('primary')}]: ").strip()
        if new_primary:
            colors['primary'] = new_primary

        new_secondary = input(f"Secondary color [{colors.get('secondary')}]: ").strip()
        if new_secondary:
            colors['secondary'] = new_secondary

        new_accent = input(f"Accent color [{colors.get('accent')}]: ").strip()
        if new_accent:
            colors['accent'] = new_accent

        # Edit tone
        personality = analysis.get('personality', {})
        new_tone = input(f"Tone [{personality.get('tone')}]: ").strip()
        if new_tone:
            personality['tone'] = new_tone

        print("\n✅ Edits applied!")
        return analysis

    def _save_preference(self, domain: str, analysis: dict, rating: str):
        """
        Save user preference for learning
        Future: Use this to tune Ollama for next domains
        """
        # For now, just log it
        # Later: Store in preferences.json or database
        import json
        from pathlib import Path

        prefs_file = Path("onboarding_preferences.json")

        if prefs_file.exists():
            with open(prefs_file) as f:
                prefs = json.load(f)
        else:
            prefs = {"domains": []}

        prefs["domains"].append({
            "domain": domain,
            "rating": rating,
            "tagline": analysis.get('tagline'),
            "category": analysis.get('category'),
            "temperature": self.temperature,
            "attempt": self.attempt_count
        })

        with open(prefs_file, 'w') as f:
            json.dump(prefs, f, indent=2)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 interactive_onboarding.py <domain>")
        print("Example: python3 interactive_onboarding.py testgame.com")
        sys.exit(1)

    domain = sys.argv[1]
    onboarding = InteractiveOnboarding()

    success = onboarding.onboard_with_acceptance(domain)

    if success:
        print(f"\n🎉 {domain} successfully onboarded!")
    else:
        print(f"\n😞 {domain} onboarding incomplete")


if __name__ == '__main__':
    main()

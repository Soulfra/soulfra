#!/usr/bin/env python3
"""
Voice Advertising Mapper - Find Monetization Opportunities in Voice Recordings

Traditional Advertising: Manually research keywords → Bid on them → Hope for conversions
Voice Advertising: Speak naturally → Algorithm finds ad opportunities → Auto-generate campaigns

This tool analyzes voice recordings and maps them to:
- Google Ads keywords (with estimated CPC)
- Meta/Facebook Ads targeting parameters
- Affiliate marketing opportunities
- Sponsored content angles
- Display ad placements
- YouTube pre-roll opportunities
- Ad revenue estimates

Example:
    Transcript: "Ideas is about cringe proof. It's a game where you talk
                 about news articles and they get scraped from Google"

    Advertising Opportunities:
    ┌─────────────────────────────────────────────────────────────┐
    │ GOOGLE ADS KEYWORDS                                          │
    ├─────────────────────────────────────────────────────────────┤
    │ • "cringe proof game" - Est. CPC: $1.20                     │
    │ • "news scraper tool" - Est. CPC: $2.40                     │
    │ • "google news feeds" - Est. CPC: $0.80                     │
    │ • "talk about news" - Est. CPC: $0.60                       │
    ├─────────────────────────────────────────────────────────────┤
    │ META ADS TARGETING                                           │
    ├─────────────────────────────────────────────────────────────┤
    │ • Interests: Gaming, News Junkies, Tech Tools               │
    │ • Behaviors: Early Adopters, Content Creators                │
    │ • Demographics: 18-34, College Educated                      │
    ├─────────────────────────────────────────────────────────────┤
    │ AFFILIATE OPPORTUNITIES                                      │
    ├─────────────────────────────────────────────────────────────┤
    │ • News API services (10% commission)                         │
    │ • Web scraping tools (15-30% commission)                     │
    │ • Gaming platforms (5-20% commission)                        │
    ├─────────────────────────────────────────────────────────────┤
    │ REVENUE ESTIMATE                                             │
    ├─────────────────────────────────────────────────────────────┤
    │ • Google Ads: $50-200/month (1000 impressions)              │
    │ • Meta Ads: $30-150/month                                    │
    │ • Affiliate: $20-500/month (10 conversions)                  │
    │ • Total: $100-850/month potential                            │
    └─────────────────────────────────────────────────────────────┘

Usage:
    from voice_advertising_mapper import VoiceAdMapper

    mapper = VoiceAdMapper()
    opportunities = mapper.analyze_recording(recording_id=5)
    print(opportunities['revenue_estimate'])

CLI:
    python3 voice_advertising_mapper.py --recording 5
    python3 voice_advertising_mapper.py --user 1 --all
"""

import re
import json
import sys
from typing import Dict, List, Tuple
from database import get_db
from voice_seo_pattern_detector import VoiceSEODetector


class VoiceAdMapper:
    """Map voice recordings to advertising and monetization opportunities"""

    def __init__(self):
        self.db = get_db()
        self.seo_detector = VoiceSEODetector()

        # Estimated CPC (Cost Per Click) by keyword category
        # Based on typical Google Ads benchmarks
        self.cpc_estimates = {
            'game': 1.20,
            'tool': 2.40,
            'scraper': 3.50,
            'news': 0.80,
            'social': 1.50,
            'content': 1.80,
            'create': 2.10,
            'build': 2.30,
            'app': 2.80,
            'platform': 3.20,
            'default': 1.00
        }

        # Affiliate program categories with commission rates
        self.affiliate_categories = {
            'news': {'programs': ['NewsAPI', 'MediaStack'], 'commission': 0.10},
            'scraper': {'programs': ['ScrapingBee', 'ParseHub'], 'commission': 0.25},
            'game': {'programs': ['Steam', 'Unity Asset Store'], 'commission': 0.15},
            'tool': {'programs': ['AppSumo', 'ProductHunt'], 'commission': 0.20},
            'social': {'programs': ['Buffer', 'Hootsuite'], 'commission': 0.30},
            'content': {'programs': ['Grammarly', 'Canva'], 'commission': 0.25}
        }

    def analyze_recording(self, recording_id: int) -> Dict:
        """
        Analyze recording for advertising opportunities

        Returns:
            {
                'recording_id': int,
                'transcript': str,
                'google_ads': {
                    'keywords': [{'keyword': str, 'cpc': float, 'category': str}],
                    'estimated_monthly_revenue': float,
                    'recommended_budget': float
                },
                'meta_ads': {
                    'interests': [str],
                    'behaviors': [str],
                    'demographics': dict,
                    'estimated_monthly_revenue': float
                },
                'affiliate_opportunities': [
                    {'category': str, 'programs': [str], 'commission': float, 'potential_revenue': float}
                ],
                'sponsored_content': {
                    'angles': [str],
                    'potential_sponsors': [str]
                },
                'display_ads': {
                    'placements': [str],
                    'estimated_cpm': float,
                    'estimated_monthly_revenue': float
                },
                'total_revenue_estimate': {
                    'min_monthly': float,
                    'max_monthly': float,
                    'annual': float
                },
                'monetization_score': float (0-100)
            }
        """
        # Get recording
        rec = self.db.execute('''
            SELECT id, user_id, transcription, filename
            FROM simple_voice_recordings
            WHERE id = ?
        ''', (recording_id,)).fetchone()

        if not rec or not rec['transcription']:
            return {'error': 'No transcription found'}

        transcript = rec['transcription']

        # Get SEO patterns (reuse existing detector)
        seo_analysis = self.seo_detector.analyze_recording(recording_id)

        result = {
            'recording_id': recording_id,
            'transcript': transcript,
            'google_ads': {},
            'meta_ads': {},
            'affiliate_opportunities': [],
            'sponsored_content': {},
            'display_ads': {},
            'total_revenue_estimate': {},
            'monetization_score': 0
        }

        # Analyze Google Ads opportunities
        result['google_ads'] = self._analyze_google_ads(
            transcript,
            seo_analysis.get('patterns_detected', {})
        )

        # Analyze Meta Ads targeting
        result['meta_ads'] = self._analyze_meta_ads(
            transcript,
            seo_analysis.get('patterns_detected', {})
        )

        # Find affiliate opportunities
        result['affiliate_opportunities'] = self._find_affiliate_opportunities(
            transcript,
            seo_analysis.get('patterns_detected', {})
        )

        # Identify sponsored content angles
        result['sponsored_content'] = self._identify_sponsored_content(
            transcript,
            seo_analysis.get('patterns_detected', {})
        )

        # Estimate display ad revenue
        result['display_ads'] = self._estimate_display_ads(seo_analysis.get('seo_score', 0))

        # Calculate total revenue estimate
        result['total_revenue_estimate'] = self._calculate_total_revenue(result)

        # Calculate monetization score
        result['monetization_score'] = self._calculate_monetization_score(result)

        return result

    def _analyze_google_ads(self, transcript: str, seo_patterns: Dict) -> Dict:
        """Analyze Google Ads keyword opportunities"""
        keywords = []

        # Get long-tail keywords from SEO analysis
        long_tail = seo_patterns.get('long_tail_keywords', [])
        ad_targets = seo_patterns.get('advertising_targets', [])

        # Combine and estimate CPC for each keyword
        all_keywords = set(long_tail + ad_targets)

        for keyword in all_keywords:
            # Estimate CPC based on keyword content
            cpc = self._estimate_cpc(keyword)
            category = self._categorize_keyword(keyword)

            keywords.append({
                'keyword': keyword,
                'cpc': cpc,
                'category': category,
                'match_type': 'phrase'  # Default to phrase match
            })

        # Sort by CPC (highest first)
        keywords.sort(key=lambda x: x['cpc'], reverse=True)

        # Estimate monthly revenue (assume 1000 clicks/month at 2% CTR)
        avg_cpc = sum(k['cpc'] for k in keywords) / len(keywords) if keywords else 0
        estimated_clicks = 1000 * 0.02  # 1000 impressions * 2% CTR
        estimated_revenue = avg_cpc * estimated_clicks

        return {
            'keywords': keywords[:20],  # Top 20 keywords
            'estimated_monthly_revenue': round(estimated_revenue, 2),
            'recommended_budget': round(avg_cpc * 100, 2),  # Budget for 100 clicks/month
            'total_keywords': len(keywords)
        }

    def _analyze_meta_ads(self, transcript: str, seo_patterns: Dict) -> Dict:
        """Analyze Meta/Facebook Ads targeting opportunities"""
        interests = []
        behaviors = []
        demographics = {}

        # Extract interests from keywords
        keywords = seo_patterns.get('long_tail_keywords', [])

        # Map keywords to Meta interests
        interest_mapping = {
            'game': ['Gaming', 'Video games', 'Online gaming'],
            'news': ['News', 'Current events', 'Journalism'],
            'social': ['Social media', 'Social networking', 'Content creation'],
            'tech': ['Technology', 'Tech early adopters', 'Software'],
            'content': ['Content creators', 'Blogging', 'Digital media'],
            'scrape': ['Data analysis', 'Web development', 'Technology'],
            'cringe': ['Social commentary', 'Pop culture', 'Internet culture']
        }

        for keyword in keywords:
            for category, meta_interests in interest_mapping.items():
                if category in keyword.lower():
                    interests.extend(meta_interests)

        # Deduplicate interests
        interests = list(set(interests))

        # Infer behaviors
        behaviors = [
            'Early technology adopters',
            'Online shoppers',
            'Engaged shoppers',
            'Small business owners'
        ]

        # Infer demographics
        demographics = {
            'age_range': '18-45',
            'education': 'College educated',
            'interests_count': len(interests)
        }

        # Estimate Meta Ads revenue (typically lower CPC than Google)
        estimated_revenue = self._estimate_meta_revenue(len(interests))

        return {
            'interests': interests[:15],  # Top 15 interests
            'behaviors': behaviors,
            'demographics': demographics,
            'estimated_monthly_revenue': round(estimated_revenue, 2),
            'recommended_budget': 200  # $200/month starter budget
        }

    def _find_affiliate_opportunities(self, transcript: str, seo_patterns: Dict) -> List[Dict]:
        """Find affiliate marketing opportunities"""
        opportunities = []

        keywords = seo_patterns.get('long_tail_keywords', [])

        # Match keywords to affiliate categories
        for keyword in keywords:
            for category, info in self.affiliate_categories.items():
                if category in keyword.lower():
                    # Estimate potential revenue (assume 10 conversions/month)
                    conversions_per_month = 10
                    avg_sale_value = 50  # $50 average sale
                    potential_revenue = conversions_per_month * avg_sale_value * info['commission']

                    opportunities.append({
                        'category': category,
                        'keyword': keyword,
                        'programs': info['programs'],
                        'commission_rate': info['commission'],
                        'potential_monthly_revenue': round(potential_revenue, 2)
                    })

        # Deduplicate by category
        seen_categories = set()
        unique_opportunities = []
        for opp in opportunities:
            if opp['category'] not in seen_categories:
                unique_opportunities.append(opp)
                seen_categories.add(opp['category'])

        return unique_opportunities

    def _identify_sponsored_content(self, transcript: str, seo_patterns: Dict) -> Dict:
        """Identify potential sponsored content angles"""
        angles = []
        potential_sponsors = []

        keywords = seo_patterns.get('long_tail_keywords', [])

        # Sponsored content angle templates
        if any('game' in k for k in keywords):
            angles.append("Review: The Best Games for News Junkies")
            potential_sponsors.extend(['Steam', 'Epic Games', 'Indie game studios'])

        if any('news' in k for k in keywords):
            angles.append("How to Stay Informed: Best News Aggregator Tools")
            potential_sponsors.extend(['NewsAPI', 'Feedly', 'Flipboard'])

        if any('scrape' in k or 'scraper' in k for k in keywords):
            angles.append("Top Web Scraping Tools for Content Creators")
            potential_sponsors.extend(['ScrapingBee', 'ParseHub', 'Octoparse'])

        if any('social' in k for k in keywords):
            angles.append("Growing Your Audience: Social Media Management Tools")
            potential_sponsors.extend(['Buffer', 'Hootsuite', 'Later'])

        # Add generic angles
        if not angles:
            angles.append("Ultimate Guide to [Topic from Voice Recording]")

        return {
            'angles': angles,
            'potential_sponsors': list(set(potential_sponsors)),
            'estimated_per_post': 500  # $500 per sponsored post
        }

    def _estimate_display_ads(self, seo_score: float) -> Dict:
        """Estimate display ad revenue potential"""
        # CPM (Cost Per Mille / 1000 impressions) varies by content quality
        # Higher SEO score = higher quality content = higher CPM

        if seo_score >= 75:
            cpm = 8.0  # Premium content
        elif seo_score >= 50:
            cpm = 5.0  # Good content
        elif seo_score >= 25:
            cpm = 3.0  # Average content
        else:
            cpm = 1.5  # Low-quality content

        # Estimate monthly pageviews (assume 10,000 for established blog)
        monthly_pageviews = 10000
        estimated_revenue = (monthly_pageviews / 1000) * cpm

        return {
            'estimated_cpm': cpm,
            'placements': [
                'Header banner (728x90)',
                'Sidebar (300x250)',
                'In-content (responsive)',
                'Footer (728x90)'
            ],
            'estimated_monthly_pageviews': monthly_pageviews,
            'estimated_monthly_revenue': round(estimated_revenue, 2)
        }

    def _calculate_total_revenue(self, result: Dict) -> Dict:
        """Calculate total revenue estimate across all channels"""
        google_ads = result['google_ads'].get('estimated_monthly_revenue', 0)
        meta_ads = result['meta_ads'].get('estimated_monthly_revenue', 0)
        affiliate = sum(opp.get('potential_monthly_revenue', 0)
                       for opp in result['affiliate_opportunities'])
        display_ads = result['display_ads'].get('estimated_monthly_revenue', 0)

        total_min = google_ads * 0.5 + meta_ads * 0.5 + affiliate * 0.2 + display_ads
        total_max = google_ads * 1.5 + meta_ads * 1.5 + affiliate * 2.0 + display_ads * 1.5

        return {
            'min_monthly': round(total_min, 2),
            'max_monthly': round(total_max, 2),
            'annual_min': round(total_min * 12, 2),
            'annual_max': round(total_max * 12, 2),
            'breakdown': {
                'google_ads': google_ads,
                'meta_ads': meta_ads,
                'affiliate': round(affiliate, 2),
                'display_ads': display_ads
            }
        }

    def _calculate_monetization_score(self, result: Dict) -> float:
        """Calculate overall monetization potential (0-100)"""
        score = 0

        # Google Ads keywords (30 points max)
        keywords = len(result['google_ads'].get('keywords', []))
        score += min(keywords * 2, 30)

        # Meta Ads targeting (20 points max)
        interests = len(result['meta_ads'].get('interests', []))
        score += min(interests * 1.5, 20)

        # Affiliate opportunities (25 points max)
        affiliates = len(result['affiliate_opportunities'])
        score += min(affiliates * 5, 25)

        # Sponsored content (15 points max)
        sponsors = len(result['sponsored_content'].get('potential_sponsors', []))
        score += min(sponsors * 2, 15)

        # Display ads (10 points max)
        cpm = result['display_ads'].get('estimated_cpm', 0)
        score += min(cpm * 1.25, 10)

        return min(score, 100)

    def _estimate_cpc(self, keyword: str) -> float:
        """Estimate Cost Per Click for a keyword"""
        # Check keyword against CPC categories
        for category, cpc in self.cpc_estimates.items():
            if category in keyword.lower():
                return cpc

        return self.cpc_estimates['default']

    def _categorize_keyword(self, keyword: str) -> str:
        """Categorize keyword into ad category"""
        categories = {
            'gaming': ['game', 'play', 'gaming'],
            'technology': ['tool', 'app', 'software', 'tech'],
            'news': ['news', 'article', 'feed'],
            'social_media': ['social', 'post', 'content'],
            'development': ['scrape', 'build', 'create']
        }

        for category, terms in categories.items():
            if any(term in keyword.lower() for term in terms):
                return category

        return 'general'

    def _estimate_meta_revenue(self, interest_count: int) -> float:
        """Estimate Meta Ads revenue based on targeting precision"""
        # More interests = better targeting = higher revenue
        base_revenue = 30  # $30 base
        interest_bonus = interest_count * 5  # $5 per interest

        return min(base_revenue + interest_bonus, 150)  # Cap at $150

    def print_opportunities(self, analysis: Dict):
        """Print formatted advertising opportunities report"""
        if 'error' in analysis:
            print(f"\n❌ Error: {analysis['error']}\n")
            return

        rid = analysis['recording_id']
        score = analysis['monetization_score']

        print(f"\n{'='*70}")
        print(f"💰 Advertising Opportunities - Recording #{rid}")
        print(f"{'='*70}\n")

        print(f"Monetization Score: {score:.0f}/100")

        # Google Ads
        print(f"\n{'─'*70}")
        print("💵 GOOGLE ADS KEYWORDS")
        print(f"{'─'*70}")
        google_ads = analysis['google_ads']
        print(f"Total Keywords: {google_ads.get('total_keywords', 0)}")
        print(f"Estimated Revenue: ${google_ads.get('estimated_monthly_revenue', 0):.2f}/month")
        print(f"\nTop Keywords:")
        for kw in google_ads.get('keywords', [])[:10]:
            print(f"  • \"{kw['keyword']}\" - ${kw['cpc']:.2f} CPC ({kw['category']})")

        # Meta Ads
        print(f"\n{'─'*70}")
        print("📘 META/FACEBOOK ADS TARGETING")
        print(f"{'─'*70}")
        meta_ads = analysis['meta_ads']
        print(f"Estimated Revenue: ${meta_ads.get('estimated_monthly_revenue', 0):.2f}/month")
        print(f"\nInterests ({len(meta_ads.get('interests', []))}):")
        for interest in meta_ads.get('interests', [])[:10]:
            print(f"  • {interest}")
        print(f"\nBehaviors:")
        for behavior in meta_ads.get('behaviors', [])[:5]:
            print(f"  • {behavior}")

        # Affiliate
        print(f"\n{'─'*70}")
        print("🤝 AFFILIATE OPPORTUNITIES")
        print(f"{'─'*70}")
        for aff in analysis['affiliate_opportunities']:
            print(f"\n{aff['category'].upper()}")
            print(f"  Programs: {', '.join(aff['programs'])}")
            print(f"  Commission: {aff['commission_rate']*100:.0f}%")
            print(f"  Potential: ${aff['potential_monthly_revenue']:.2f}/month")

        # Sponsored Content
        print(f"\n{'─'*70}")
        print("📝 SPONSORED CONTENT")
        print(f"{'─'*70}")
        sponsored = analysis['sponsored_content']
        print(f"Angles:")
        for angle in sponsored.get('angles', []):
            print(f"  • {angle}")
        print(f"\nPotential Sponsors:")
        for sponsor in sponsored.get('potential_sponsors', [])[:10]:
            print(f"  • {sponsor}")

        # Total Revenue
        print(f"\n{'─'*70}")
        print("💰 TOTAL REVENUE ESTIMATE")
        print(f"{'─'*70}")
        revenue = analysis['total_revenue_estimate']
        print(f"Monthly: ${revenue.get('min_monthly', 0):.2f} - ${revenue.get('max_monthly', 0):.2f}")
        print(f"Annual: ${revenue.get('annual_min', 0):,.2f} - ${revenue.get('annual_max', 0):,.2f}")
        print(f"\nBreakdown:")
        breakdown = revenue.get('breakdown', {})
        print(f"  • Google Ads: ${breakdown.get('google_ads', 0):.2f}/month")
        print(f"  • Meta Ads: ${breakdown.get('meta_ads', 0):.2f}/month")
        print(f"  • Affiliate: ${breakdown.get('affiliate', 0):.2f}/month")
        print(f"  • Display Ads: ${breakdown.get('display_ads', 0):.2f}/month")

        print(f"\n{'='*70}\n")


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Voice Advertising Opportunity Mapper')
    parser.add_argument('--recording', type=int, help='Analyze specific recording ID')
    parser.add_argument('--user', type=int, help='Analyze all recordings for user')
    parser.add_argument('--all', action='store_true', help='Analyze all recordings for user')

    args = parser.parse_args()

    mapper = VoiceAdMapper()

    if args.recording:
        # Analyze single recording
        analysis = mapper.analyze_recording(args.recording)
        mapper.print_opportunities(analysis)

    elif args.user:
        # Analyze all recordings for user
        db = get_db()
        recordings = db.execute('''
            SELECT id FROM simple_voice_recordings
            WHERE user_id = ? AND transcription IS NOT NULL
            ORDER BY created_at DESC
        ''', (args.user,)).fetchall()

        print(f"\n💰 Analyzing {len(recordings)} recordings for user {args.user}...\n")

        for rec in recordings:
            analysis = mapper.analyze_recording(rec['id'])
            if 'error' not in analysis:
                mapper.print_opportunities(analysis)

    else:
        print("\nUsage:")
        print("  python3 voice_advertising_mapper.py --recording 5")
        print("  python3 voice_advertising_mapper.py --user 1 --all")
        print()
        sys.exit(1)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Couples Profile System - Location-Based Dating Profiles

Unlike Match.com's photo-first approach, this is VOICE-FIRST dating:
- Deep conversations about marriage, kids, values
- AI matching based on voice content
- Location-aware (encrypted GPS + zip code)
- No surface-level swiping

Database Schema:
    ALTER TABLE users ADD COLUMN zip_code TEXT;
    ALTER TABLE users ADD COLUMN location_encrypted_data BLOB;
    ALTER TABLE users ADD COLUMN location_encryption_key TEXT;
    ALTER TABLE users ADD COLUMN location_encryption_iv TEXT;
    ALTER TABLE users ADD COLUMN relationship_status TEXT;
    ALTER TABLE users ADD COLUMN looking_for TEXT;
    ALTER TABLE users ADD COLUMN distance_radius INTEGER DEFAULT 50;
    ALTER TABLE users ADD COLUMN age INTEGER;
    ALTER TABLE users ADD COLUMN gender TEXT;
    ALTER TABLE users ADD COLUMN seeking_gender TEXT;

Usage:
    from couples_profile_system import CouplesProfileSystem

    system = CouplesProfileSystem()

    # Create profile with location
    profile = system.create_profile(
        user_id=1,
        zip_code='10001',
        latitude=40.7589,
        longitude=-73.9851,
        age=28,
        gender='female',
        seeking_gender='male',
        relationship_status='single',
        looking_for='serious',
        distance_radius=50  # miles
    )

    # Get nearby profiles
    matches = system.get_nearby_profiles(user_id=1, max_distance=50)

CLI:
    python3 couples_profile_system.py --create-profile --user 1 --zip 10001 --lat 40.7589 --lon -73.9851
    python3 couples_profile_system.py --get-nearby --user 1 --radius 50
    python3 couples_profile_system.py --update-location --user 1 --zip 94102
"""

import sys
import json
from typing import Dict, List, Optional, Tuple
from database import get_db
from gps_encryption import encrypt_gps_for_database, decrypt_gps_from_database
import requests


class CouplesProfileSystem:
    """Manage dating profiles with encrypted location data"""

    def __init__(self):
        self.db = get_db()
        self._ensure_schema()

    def _ensure_schema(self):
        """Ensure couples profile columns exist in users table"""
        try:
            # Add new columns if they don't exist
            columns_to_add = [
                ('zip_code', 'TEXT'),
                ('location_encrypted_data', 'TEXT'),  # base64-encoded BLOB
                ('location_encryption_key', 'TEXT'),
                ('location_encryption_iv', 'TEXT'),
                ('relationship_status', 'TEXT'),  # 'single', 'dating', 'married'
                ('looking_for', 'TEXT'),  # 'serious', 'casual', 'friends'
                ('distance_radius', 'INTEGER DEFAULT 50'),
                ('age', 'INTEGER'),
                ('gender', 'TEXT'),  # 'male', 'female', 'non-binary', 'other'
                ('seeking_gender', 'TEXT'),  # 'male', 'female', 'any'
            ]

            for col_name, col_type in columns_to_add:
                try:
                    self.db.execute(f'ALTER TABLE users ADD COLUMN {col_name} {col_type}')
                except Exception as e:
                    # Column already exists or other error - continue
                    pass

            self.db.commit()

        except Exception as e:
            print(f"Schema update warning: {e}")

    def create_profile(
        self,
        user_id: int,
        zip_code: str,
        latitude: float,
        longitude: float,
        age: int,
        gender: str,
        seeking_gender: str = 'any',
        relationship_status: str = 'single',
        looking_for: str = 'serious',
        distance_radius: int = 50
    ) -> Dict:
        """
        Create or update couples profile with encrypted location

        Args:
            user_id: User ID
            zip_code: 5-digit US zip code
            latitude: GPS latitude
            longitude: GPS longitude
            age: User's age
            gender: 'male', 'female', 'non-binary', 'other'
            seeking_gender: 'male', 'female', 'any'
            relationship_status: 'single', 'dating', 'married'
            looking_for: 'serious', 'casual', 'friends'
            distance_radius: Maximum distance for matches (miles)

        Returns:
            dict with profile data
        """
        # Validate inputs
        if not zip_code or len(zip_code) != 5:
            raise ValueError(f"Invalid zip code: {zip_code}")

        if not (13 <= age <= 120):
            raise ValueError(f"Invalid age: {age}")

        if gender not in ['male', 'female', 'non-binary', 'other']:
            raise ValueError(f"Invalid gender: {gender}")

        if seeking_gender not in ['male', 'female', 'any']:
            raise ValueError(f"Invalid seeking_gender: {seeking_gender}")

        # Encrypt GPS coordinates
        encrypted_location = encrypt_gps_for_database(latitude, longitude)

        # Update user profile
        self.db.execute('''
            UPDATE users
            SET zip_code = ?,
                location_encrypted_data = ?,
                location_encryption_key = ?,
                location_encryption_iv = ?,
                age = ?,
                gender = ?,
                seeking_gender = ?,
                relationship_status = ?,
                looking_for = ?,
                distance_radius = ?
            WHERE id = ?
        ''', (
            zip_code,
            encrypted_location['location_encrypted_data'],
            encrypted_location['location_encryption_key'],
            encrypted_location['location_encryption_iv'],
            age,
            gender,
            seeking_gender,
            relationship_status,
            looking_for,
            distance_radius,
            user_id
        ))

        self.db.commit()

        print(f"✅ Profile created for user {user_id}")
        print(f"   Location: {zip_code} (GPS encrypted)")
        print(f"   Age: {age}, Gender: {gender}")
        print(f"   Looking for: {looking_for} ({seeking_gender})")
        print(f"   Search radius: {distance_radius} miles")

        return {
            'user_id': user_id,
            'zip_code': zip_code,
            'age': age,
            'gender': gender,
            'seeking_gender': seeking_gender,
            'relationship_status': relationship_status,
            'looking_for': looking_for,
            'distance_radius': distance_radius,
            'latitude': latitude,  # Only returned, not stored in plaintext
            'longitude': longitude
        }

    def get_profile(self, user_id: int, decrypt_location: bool = False) -> Optional[Dict]:
        """
        Get user's couples profile

        Args:
            user_id: User ID
            decrypt_location: If True, decrypt GPS coordinates

        Returns:
            Profile dict or None
        """
        row = self.db.execute('''
            SELECT id, username, zip_code, age, gender, seeking_gender,
                   relationship_status, looking_for, distance_radius,
                   location_encrypted_data, location_encryption_key, location_encryption_iv
            FROM users
            WHERE id = ?
        ''', (user_id,)).fetchone()

        if not row:
            return None

        profile = dict(row)

        # Decrypt location if requested
        if decrypt_location and row['location_encrypted_data']:
            try:
                lat, lon = decrypt_gps_from_database(dict(row))
                profile['latitude'] = lat
                profile['longitude'] = lon
            except Exception as e:
                print(f"⚠️  Failed to decrypt location for user {user_id}: {e}")
                profile['latitude'] = None
                profile['longitude'] = None

        return profile

    def get_nearby_profiles(
        self,
        user_id: int,
        max_distance: Optional[int] = None,
        min_age: Optional[int] = None,
        max_age: Optional[int] = None
    ) -> List[Dict]:
        """
        Get profiles within distance radius

        Args:
            user_id: User ID
            max_distance: Maximum distance in miles (defaults to user's distance_radius)
            min_age: Minimum age filter
            max_age: Maximum age filter

        Returns:
            List of nearby profiles with distances
        """
        # Get user's profile
        user_profile = self.get_profile(user_id, decrypt_location=True)

        if not user_profile:
            return []

        if not user_profile.get('latitude'):
            print(f"⚠️  User {user_id} has no location data")
            return []

        # Use user's distance radius if not specified
        if max_distance is None:
            max_distance = user_profile.get('distance_radius', 50)

        # Get all other users with location data
        all_users = self.db.execute('''
            SELECT id, username, age, gender, zip_code,
                   location_encrypted_data, location_encryption_key, location_encryption_iv,
                   relationship_status, looking_for
            FROM users
            WHERE id != ?
              AND location_encrypted_data IS NOT NULL
              AND gender = ?  -- Match seeking gender
        ''', (user_id, user_profile['seeking_gender'])).fetchall()

        nearby_profiles = []

        for other_user in all_users:
            # Decrypt their location
            try:
                other_lat, other_lon = decrypt_gps_from_database(dict(other_user))
            except Exception as e:
                continue  # Skip if can't decrypt

            # Calculate distance
            distance = self._haversine_distance(
                user_profile['latitude'],
                user_profile['longitude'],
                other_lat,
                other_lon
            )

            # Filter by distance
            if distance > max_distance:
                continue

            # Filter by age
            if min_age and other_user['age'] < min_age:
                continue
            if max_age and other_user['age'] > max_age:
                continue

            nearby_profiles.append({
                'user_id': other_user['id'],
                'username': other_user['username'],
                'age': other_user['age'],
                'gender': other_user['gender'],
                'zip_code': other_user['zip_code'],
                'distance_miles': round(distance, 1),
                'relationship_status': other_user['relationship_status'],
                'looking_for': other_user['looking_for']
            })

        # Sort by distance
        nearby_profiles.sort(key=lambda x: x['distance_miles'])

        return nearby_profiles

    def update_location(self, user_id: int, zip_code: str, latitude: float, longitude: float) -> bool:
        """Update user's location"""
        encrypted_location = encrypt_gps_for_database(latitude, longitude)

        self.db.execute('''
            UPDATE users
            SET zip_code = ?,
                location_encrypted_data = ?,
                location_encryption_key = ?,
                location_encryption_iv = ?
            WHERE id = ?
        ''', (
            zip_code,
            encrypted_location['location_encrypted_data'],
            encrypted_location['location_encryption_key'],
            encrypted_location['location_encryption_iv'],
            user_id
        ))

        self.db.commit()

        print(f"✅ Location updated for user {user_id}: {zip_code}")
        return True

    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two GPS coordinates in miles

        Uses Haversine formula:
        https://en.wikipedia.org/wiki/Haversine_formula
        """
        import math

        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = (math.sin(dlat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2)

        c = 2 * math.asin(math.sqrt(a))

        # Earth radius in miles
        radius_miles = 3959

        distance = radius_miles * c

        return distance

    def geocode_zip(self, zip_code: str) -> Optional[Tuple[float, float]]:
        """
        Convert zip code to GPS coordinates using free geocoding API

        Uses zippopotam.us (free, no API key needed)

        Returns:
            (latitude, longitude) or None
        """
        try:
            url = f"http://api.zippopotam.us/us/{zip_code}"
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                data = response.json()
                lat = float(data['places'][0]['latitude'])
                lon = float(data['places'][0]['longitude'])
                return (lat, lon)
            else:
                print(f"⚠️  Zip code {zip_code} not found")
                return None

        except Exception as e:
            print(f"⚠️  Geocoding failed: {e}")
            return None

    def print_profile_summary(self, user_id: int):
        """Print formatted profile summary"""
        profile = self.get_profile(user_id, decrypt_location=True)

        if not profile:
            print(f"\n❌ Profile not found for user {user_id}\n")
            return

        print(f"\n{'='*70}")
        print(f"👤 Couples Profile - User #{user_id}")
        print(f"{'='*70}")

        print(f"\nUsername: {profile.get('username', 'N/A')}")
        print(f"Age: {profile.get('age', 'N/A')}")
        print(f"Gender: {profile.get('gender', 'N/A')}")
        print(f"Seeking: {profile.get('seeking_gender', 'N/A')}")

        print(f"\nRelationship Status: {profile.get('relationship_status', 'N/A')}")
        print(f"Looking For: {profile.get('looking_for', 'N/A')}")

        print(f"\nLocation:")
        print(f"  Zip Code: {profile.get('zip_code', 'N/A')}")
        if profile.get('latitude'):
            print(f"  GPS: {profile['latitude']:.4f}, {profile['longitude']:.4f} (encrypted)")
        print(f"  Search Radius: {profile.get('distance_radius', 50)} miles")

        print(f"\n{'='*70}\n")


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Couples Profile System')

    # Create profile
    parser.add_argument('--create-profile', action='store_true', help='Create couples profile')
    parser.add_argument('--user', type=int, help='User ID')
    parser.add_argument('--zip', type=str, help='Zip code')
    parser.add_argument('--lat', type=float, help='Latitude (optional if zip provided)')
    parser.add_argument('--lon', type=float, help='Longitude (optional if zip provided)')
    parser.add_argument('--age', type=int, help='Age')
    parser.add_argument('--gender', type=str, choices=['male', 'female', 'non-binary', 'other'], help='Gender')
    parser.add_argument('--seeking', type=str, choices=['male', 'female', 'any'], help='Seeking gender')
    parser.add_argument('--status', type=str, default='single', help='Relationship status')
    parser.add_argument('--looking-for', type=str, default='serious', help='Looking for')
    parser.add_argument('--radius', type=int, default=50, help='Search radius in miles')

    # Get profile
    parser.add_argument('--get-profile', action='store_true', help='Get profile')

    # Get nearby
    parser.add_argument('--get-nearby', action='store_true', help='Get nearby profiles')

    # Update location
    parser.add_argument('--update-location', action='store_true', help='Update location')

    args = parser.parse_args()

    system = CouplesProfileSystem()

    if args.create_profile:
        if not all([args.user, args.zip, args.age, args.gender]):
            print("Error: --create-profile requires --user, --zip, --age, --gender")
            sys.exit(1)

        # Get GPS from zip if not provided
        if not args.lat or not args.lon:
            coords = system.geocode_zip(args.zip)
            if coords:
                lat, lon = coords
            else:
                print("Error: Could not geocode zip code. Provide --lat and --lon manually.")
                sys.exit(1)
        else:
            lat, lon = args.lat, args.lon

        system.create_profile(
            user_id=args.user,
            zip_code=args.zip,
            latitude=lat,
            longitude=lon,
            age=args.age,
            gender=args.gender,
            seeking_gender=args.seeking or 'any',
            relationship_status=args.status,
            looking_for=args.looking_for,
            distance_radius=args.radius
        )

    elif args.get_profile:
        if not args.user:
            print("Error: --get-profile requires --user")
            sys.exit(1)

        system.print_profile_summary(args.user)

    elif args.get_nearby:
        if not args.user:
            print("Error: --get-nearby requires --user")
            sys.exit(1)

        nearby = system.get_nearby_profiles(args.user, max_distance=args.radius)

        print(f"\n{'='*70}")
        print(f"📍 Nearby Profiles for User #{args.user}")
        print(f"{'='*70}\n")

        if not nearby:
            print("No nearby profiles found.\n")
        else:
            for profile in nearby:
                print(f"👤 {profile['username']} (ID: {profile['user_id']})")
                print(f"   {profile['age']} • {profile['gender']} • {profile['zip_code']}")
                print(f"   {profile['distance_miles']} miles away")
                print(f"   Looking for: {profile['looking_for']}")
                print()

    elif args.update_location:
        if not all([args.user, args.zip]):
            print("Error: --update-location requires --user and --zip")
            sys.exit(1)

        # Geocode zip
        coords = system.geocode_zip(args.zip)
        if not coords:
            print("Error: Could not geocode zip code")
            sys.exit(1)

        lat, lon = coords
        system.update_location(args.user, args.zip, lat, lon)

    else:
        print("\nUsage:")
        print("  python3 couples_profile_system.py --create-profile --user 1 --zip 10001 --age 28 --gender female --seeking male")
        print("  python3 couples_profile_system.py --get-profile --user 1")
        print("  python3 couples_profile_system.py --get-nearby --user 1 --radius 50")
        print("  python3 couples_profile_system.py --update-location --user 1 --zip 94102")
        print()
        sys.exit(1)


if __name__ == '__main__':
    main()

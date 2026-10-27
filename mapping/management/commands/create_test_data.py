"""
Management command to create test data for EvacuaLink system.
Generates realistic sample data for testing all features.

Usage: python manage.py create_test_data
"""

import os
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import random
import json
from shapely.geometry import Point, shape

from mapping.models import BarangayBoundary, HazardZone, SafeZone, MapLocation
from evacuation_centers.models import EvacuationCenter
from families.models import Family
from evacuees.models import Evacuee
from emergency.models import EmergencyHelpRequest, EmergencyIncident

User = get_user_model()


class Command(BaseCommand):
    help = 'Create test data for EvacuaLink system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force-insecure',
            action='store_true',
            help='Allow running in production / non-debug mode (NOT recommended)',
        )

    def handle(self, *args, **options):
        if not settings.DEBUG and not options.get('force_insecure'):
            raise CommandError(
                "Creating test data with default sample credentials is blocked when DEBUG=False. "
                "Do not run this command on production servers."
            )

        self.stdout.write(self.style.WARNING(
            "⚠️  SECURITY NOTICE: Generating sample users for local development only. "
            "Never use default passwords in production!"
        ))
        self.stdout.write(self.style.SUCCESS('Starting test data creation...'))

        # Create users
        self.create_users()

        # Get Barangay boundary for geographic validation
        try:
            boundary = BarangayBoundary.objects.first()
            if not boundary:
                self.stdout.write(self.style.ERROR('Barangay boundary not found. Please load it first.'))
                return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error loading boundary: {e}'))
            return

        # Create evacuation centers
        self.create_evacuation_centers(boundary)

        # Create hazard zones
        self.create_hazard_zones(boundary)

        # Create safe zones
        self.create_safe_zones(boundary)

        # Create families and evacuees
        self.create_families_and_evacuees(boundary)

        # Create help requests
        self.create_help_requests(boundary)

        # Create incidents
        self.create_incidents()

        self.stdout.write(self.style.SUCCESS('Test data created successfully!'))

    def create_users(self):
        """Create test users with different roles"""
        self.stdout.write('Creating test users...')

        users = [
            {
                'username': 'techadmin',
                'email': 'techadmin@evacualink.local',
                'password': 'techadmin123',
                'first_name': 'Technical',
                'last_name': 'Admin',
                'role': 'TECHNICAL_ADMIN',
            },
            {
                'username': 'admin',
                'email': 'admin@evacualink.local',
                'password': 'admin123',
                'first_name': 'Emergency',
                'last_name': 'Admin',
                'role': 'ADMIN',
            },
            {
                'username': 'staff',
                'email': 'staff@evacualink.local',
                'password': 'staff123',
                'first_name': 'Pedro',
                'last_name': 'Staff',
                'role': 'STAFF',
            },
        ]

        for user_data in users:
            username = user_data['username']
            user = User.objects.filter(username=username).first()
            if user is None:
                user = User.objects.create_user(
                    username=user_data['username'],
                    email=user_data['email'],
                    password=user_data['password'],
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    role=user_data['role'],
                )
                self.stdout.write(self.style.SUCCESS(f"  Created user: {username}"))
            else:
                user.email = user_data['email']
                user.first_name = user_data['first_name']
                user.last_name = user_data['last_name']
                user.role = user_data['role']
                user.set_password(user_data['password'])
                user.save()
                self.stdout.write(self.style.SUCCESS(f"  Refreshed user: {username}"))

    def generate_random_point_in_boundary(self, boundary):
        """Generate random coordinates within Barangay boundary"""
        try:
            polygon = shape(boundary.geometry)
            while True:
                # Generate random point within bounding box
                minx, miny, maxx, maxy = polygon.bounds
                random_point = Point(
                    random.uniform(minx, maxx),
                    random.uniform(miny, maxy)
                )
                # Check if point is within polygon
                if polygon.contains(random_point):
                    return Decimal(str(random_point.y)), Decimal(str(random_point.x))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error generating point: {e}'))
            return None, None

    def create_evacuation_centers(self, boundary):
        """Create test evacuation centers"""
        self.stdout.write('Creating evacuation centers...')

        center_names = [
            'Alicante Elementary School',
            'Barangay Hall',
            'Catholic Church',
            'Sports Complex',
            'Community Center',
        ]

        for i, name in enumerate(center_names, 1):
            if not EvacuationCenter.objects.filter(name=name).exists():
                lat, lon = self.generate_random_point_in_boundary(boundary)
                if lat and lon:
                    center = EvacuationCenter.objects.create(
                        name=name,
                        address=f'{i}00 Main Street, Alicante, EB Magalona',
                        capacity=random.randint(50, 200),
                        current_occupancy=random.randint(0, 150),
                        latitude=lat,
                        longitude=lon,
                        status=random.choice(['OPEN', 'OPEN', 'FULL']),
                    )
                    self.stdout.write(self.style.SUCCESS(f"  Created center: {name}"))

    def create_hazard_zones(self, boundary):
        """Create test hazard zones"""
        self.stdout.write('Creating hazard zones...')

        hazard_zones = [
            {
                'name': 'Low-lying Area - North',
                'hazard_type': 'FLOOD',
                'risk_level': 'HIGH',
                'description': 'Area prone to flooding during heavy rains',
            },
            {
                'name': 'Coastal Evacuation Zone',
                'hazard_type': 'FLOOD',
                'risk_level': 'CRITICAL',
                'description': 'Critical flood risk zone near coast',
            },
            {
                'name': 'Old Town - Fire Risk',
                'hazard_type': 'FIRE',
                'risk_level': 'MODERATE',
                'description': 'Historic area with old structures, fire hazard',
            },
            {
                'name': 'Hillside Area',
                'hazard_type': 'LANDSLIDE',
                'risk_level': 'MODERATE',
                'description': 'Steep terrain prone to landslides during rain',
            },
        ]

        for zone_data in hazard_zones:
            if not HazardZone.objects.filter(name=zone_data['name']).exists():
                lat, lon = self.generate_random_point_in_boundary(boundary)
                if lat and lon:
                    zone = HazardZone.objects.create(
                        name=zone_data['name'],
                        hazard_type=zone_data['hazard_type'],
                        risk_level=zone_data['risk_level'],
                        description=zone_data['description'],
                        latitude=lat,
                        longitude=lon,
                    )
                    self.stdout.write(self.style.SUCCESS(f"  Created hazard zone: {zone_data['name']}"))

    def create_safe_zones(self, boundary):
        """Create test safe zones"""
        self.stdout.write('Creating safe zones...')

        safe_zones = [
            {
                'name': 'Highland Park - Safe Area',
                'description': 'Elevated area safe from flooding',
            },
            {
                'name': 'Central Plaza - Safe Gathering Point',
                'description': 'Open area safe from fire and flooding',
            },
            {
                'name': 'Hospital Complex - Medical Facility',
                'description': 'Medical facility and safe zone',
            },
        ]

        for zone_data in safe_zones:
            if not SafeZone.objects.filter(name=zone_data['name']).exists():
                lat, lon = self.generate_random_point_in_boundary(boundary)
                if lat and lon:
                    zone = SafeZone.objects.create(
                        name=zone_data['name'],
                        description=zone_data['description'],
                        latitude=lat,
                        longitude=lon,
                    )
                    self.stdout.write(self.style.SUCCESS(f"  Created safe zone: {zone_data['name']}"))

    def create_families_and_evacuees(self, boundary):
        """Create test families and evacuees"""
        self.stdout.write('Creating families and evacuees...')

        family_names = ['Santos', 'Cruz', 'Garcia', 'Lopez', 'Torres', 'Reyes', 'Fernandez']
        first_names = ['Juan', 'Maria', 'Jose', 'Rosa', 'Carlos', 'Ana', 'Miguel']
        last_names = ['Santos', 'Cruz', 'Garcia', 'Lopez', 'Torres']

        centers = EvacuationCenter.objects.all()
        if not centers.exists():
            self.stdout.write(self.style.ERROR('  No evacuation centers found'))
            return

        for i in range(6):
            family_name = f'{family_names[i % len(family_names)]} Family'
            if not Family.objects.filter(family_name=family_name).exists():
                family = Family.objects.create(
                    family_name=family_name,
                    family_code=f'FAM-{2024}-{i+1:03d}',
                    contact_person=f'{first_names[i % len(first_names)]} {last_names[i % len(last_names)]}',
                    contact_number=f'555-{1000 + i}',
                    reunification_status=random.choice(['PENDING', 'PARTIAL', 'REUNIFIED']),
                )
                self.stdout.write(self.style.SUCCESS(f"  Created family: {family_name}"))

                # Create evacuees for this family
                num_evacuees = random.randint(2, 5)
                for j in range(num_evacuees):
                    first_name = first_names[random.randint(0, len(first_names) - 1)]
                    last_name = last_names[random.randint(0, len(last_names) - 1)]

                    has_special_needs = random.choice([True, False])
                    special_needs_desc = 'Requires medical attention' if has_special_needs else ''

                    evacuee = Evacuee.objects.create(
                        first_name=first_name,
                        last_name=last_name,
                        age=random.randint(5, 80),
                        gender=random.choice(['MALE', 'FEMALE', 'OTHER']),
                        family=family,
                        evacuation_center=random.choice(centers),
                        status=random.choice(['REGISTERED', 'CHECKED_IN', 'REUNITED']),
                        special_needs=has_special_needs,
                        special_needs_description=special_needs_desc,
                        medical_condition='Hypertension' if random.choice([True, False]) else '',
                    )
                    self.stdout.write(f"    Created evacuee: {evacuee.full_name}")

    def create_help_requests(self, boundary):
        """Create test help requests"""
        self.stdout.write('Creating help requests...')

        help_messages = [
            'Medical emergency - need ambulance',
            'Family member missing - need help searching',
            'Need food and water supplies',
            'Shelter not adequate - family of 8',
        ]

        for i, message in enumerate(help_messages):
            lat, lon = self.generate_random_point_in_boundary(boundary)
            if lat and lon:
                request = EmergencyHelpRequest.objects.create(
                    requester_name=f'Person {i+1}',
                    contact_number=f'555-{2000 + i}',
                    location_description=f'Location {i+1}, Alicante',
                    message=message,
                    latitude=lat,
                    longitude=lon,
                    status=random.choice(['PENDING', 'IN_PROGRESS', 'RESOLVED']),
                )
                self.stdout.write(self.style.SUCCESS(f"  Created help request: {message[:40]}..."))

    def create_incidents(self):
        """Create test emergency incidents"""
        self.stdout.write('Creating emergency incidents...')

        incidents = [
            {
                'title': 'Structure Damage - Center A',
                'description': 'Roof damage at evacuation center',
                'location': 'Alicante Elementary School',
                'severity': 'HIGH',
                'status': 'OPEN',
            },
            {
                'title': 'Water Supply Interrupted',
                'description': 'Main water line damaged',
                'location': 'Barangay Hall',
                'severity': 'CRITICAL',
                'status': 'RESOLVED',
            },
            {
                'title': 'Medical Emergency',
                'description': 'Evacuee in critical condition',
                'location': 'Community Center',
                'severity': 'CRITICAL',
                'status': 'RESOLVED',
            },
        ]

        user = User.objects.filter(role='STAFF').first() or User.objects.filter(role='ADMIN').first()

        for incident_data in incidents:
            if not EmergencyIncident.objects.filter(title=incident_data['title']).exists():
                incident = EmergencyIncident.objects.create(
                    title=incident_data['title'],
                    description=incident_data['description'],
                    location=incident_data['location'],
                    severity=incident_data['severity'],
                    status=incident_data['status'],
                    reported_by=user,
                )
                self.stdout.write(self.style.SUCCESS(f"  Created incident: {incident_data['title']}"))

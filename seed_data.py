import os
import django
import random
from datetime import timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evacualink.settings')
django.setup()

from families.models import Family
from evacuees.models import Evacuee
from evacuation_centers.models import EvacuationCenter
from emergency.models import EmergencyHelpRequest, EmergencyIncident
from users.models import User

def run():
    print("Clearing old data...")
    EmergencyHelpRequest.objects.all().delete()
    EmergencyIncident.objects.all().delete()
    Evacuee.objects.all().delete()
    Family.objects.all().delete()

    print("Fetching active evacuation centers...")
    centers = list(EvacuationCenter.objects.filter(status='OPEN'))
    if not centers:
        print("Error: No open evacuation centers found. Please ensure there are open centers.")
        return

    # Reset occupancy
    for c in EvacuationCenter.objects.all():
        c.current_occupancy = 0
        c.save()

    print("Generating Families and Evacuees...")
    family_surnames = ["Dela Cruz", "Santos", "Garcia", "Reyes", "Padernal", "Lopez", "Torres", "Bautista", "Villanueva", "Gonzales"]
    first_names_m = ["Juan", "Pedro", "Miguel", "Jose", "Carlos", "Luis", "Antonio", "Eduardo", "Francisco", "Manuel"]
    first_names_f = ["Maria", "Ana", "Rosa", "Luz", "Teresa", "Elena", "Carmen", "Pilar", "Isabel", "Josefina"]

    staff_user = User.objects.filter(is_staff=True).first()

    for i, surname in enumerate(family_surnames):
        # Create Evacuees first
        num_members = random.randint(2, 5)
        family_members = []
        center = random.choice(centers)
        
        # Father
        father = Evacuee.objects.create(
            first_name=random.choice(first_names_m),
            last_name=surname,
            age=random.randint(35, 60),
            gender="MALE",
            status="CHECKED_IN",
            evacuation_center=center
        )
        family_members.append(father)
        
        # Mother
        mother = Evacuee.objects.create(
            first_name=random.choice(first_names_f),
            last_name=surname,
            age=random.randint(33, 55),
            gender="FEMALE",
            status="CHECKED_IN",
            evacuation_center=center
        )
        family_members.append(mother)

        # Children
        for j in range(num_members - 2):
            is_male = random.choice([True, False])
            child = Evacuee.objects.create(
                first_name=random.choice(first_names_m) if is_male else random.choice(first_names_f),
                last_name=surname,
                age=random.randint(1, 18),
                gender="MALE" if is_male else "FEMALE",
                status="CHECKED_IN",
                evacuation_center=center
            )
            family_members.append(child)
            
        # Create Family
        family = Family(
            family_name=f"{surname} Family",
            contact_person=father,
            contact_number=f"+6391234567{i:02d}",
            reunification_status="REUNIFIED"
        )
        family.save() # Auto-generates family_code
        
        # Assign family to evacuees
        for member in family_members:
            member.family = family
            member.save()

    print("Generating separated family for testing...")
    # Add one family that is split up
    split_surname = "Mendoza"
    father2 = Evacuee.objects.create(
        first_name="Ricardo", last_name=split_surname, age=45, gender="MALE", 
        status="CHECKED_IN", evacuation_center=centers[0]
    )
    mother2 = Evacuee.objects.create(
        first_name="Linda", last_name=split_surname, age=42, gender="FEMALE", 
        status="CHECKED_IN", evacuation_center=centers[-1] if len(centers) > 1 else centers[0]
    )
    child2 = Evacuee.objects.create(
        first_name="Ben", last_name=split_surname, age=12, gender="MALE", 
        status="MISSING"
    )
    
    split_family = Family(
        family_name=f"{split_surname} Family",
        contact_person=father2,
        contact_number="+639998887777",
        reunification_status="PENDING"
    )
    split_family.save()
    father2.family = split_family
    father2.save()
    mother2.family = split_family
    mother2.save()
    child2.family = split_family
    child2.save()

    print("Generating Incidents and Help Requests...")
    EmergencyIncident.objects.create(
        title="Flooding in Alicante Proper",
        description="Water levels rising rapidly near the river.",
        severity="HIGH",
        status="OPEN",
        location="Alicante River Bank",
        reported_by=staff_user,
        reported_at=timezone.now() - timedelta(hours=2)
    )
    EmergencyIncident.objects.create(
        title="Fallen Tree Blocking Road",
        description="Large mahogany tree fell, blocking the main highway.",
        severity="MODERATE",
        status="OPEN",
        location="Highway crossing",
        reported_by=staff_user,
        reported_at=timezone.now() - timedelta(minutes=30)
    )
    
    EmergencyHelpRequest.objects.create(
        requester_name="Juan Dela Cruz",
        contact_number="+639112223333",
        location_description="Zone 3, Near Chapel",
        message="Trapped on the second floor due to flood.",
        latitude=10.7588,
        longitude=122.9801,
        status="PENDING",
        priority="HIGH"
    )
    EmergencyHelpRequest.objects.create(
        requester_name="Maria Santos",
        contact_number="+639554443333",
        location_description="Zone 1",
        message="Elderly woman needs insulin and high blood meds.",
        latitude=10.7600,
        longitude=122.9810,
        status="IN_PROGRESS",
        priority="HIGH",
        assigned_to=staff_user
    )

    print("Recalculating Occupancy...")
    for center in EvacuationCenter.objects.all():
        count = Evacuee.objects.filter(evacuation_center=center, status="CHECKED_IN").count()
        center.current_occupancy = count
        center.save()
        print(f"Center {center.name}: {count}/{center.capacity}")

    print("Data seeding complete!")

if __name__ == '__main__':
    run()

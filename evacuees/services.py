from evacuation_centers.models import EvacuationCenter
from evacuees.models import Evacuee


OCCUPANCY_STATUSES = [Evacuee.Status.CHECKED_IN, Evacuee.Status.TRANSFERRED]


def recalculate_center_occupancy(center):
    if not center:
        return

    center.current_occupancy = Evacuee.objects.filter(
        evacuation_center=center,
        status__in=OCCUPANCY_STATUSES,
    ).count()

    if center.current_occupancy >= center.capacity:
        center.status = EvacuationCenter.Status.FULL
    elif center.status == EvacuationCenter.Status.FULL:
        center.status = EvacuationCenter.Status.OPEN

    center.save(update_fields=["current_occupancy", "status", "updated_at"])


def recalculate_centers_occupancy(*centers):
    seen = set()
    for center in centers:
        if center and center.pk not in seen:
            recalculate_center_occupancy(center)
            seen.add(center.pk)

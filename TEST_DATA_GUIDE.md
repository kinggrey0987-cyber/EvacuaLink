# 🧪 EvacuaLink Test Data Generation Guide

## Quick Start

```bash
cd /c/Users/Aspire\ 3\ 15/Desktop/EvacuaLink
python manage.py create_test_data
```

## What Gets Created

> ⚠️ **SECURITY WARNING**:
> The mock credentials below are intended strictly for local development and unit tests.
> **DO NOT** execute `create_test_data` or use these default passwords in production.

### Test Users (3 development accounts)
- **techadmin** / techadmin123 → TECHNICAL_ADMIN (adds and manages admin/staff accounts)
- **admin** / admin123 → ADMIN (overall system visibility)
- **staff** / staff123 → STAFF (manages families, centers, maps, evacuees, and help requests)

### Geographic Data
- **5 Evacuation Centers** - With random locations, capacity, and occupancy
- **4 Hazard Zones** - Flood, Fire, Landslide alerts with risk levels
- **3 Safe Zones** - Designated safe gathering areas

### Evacuee Data
- **6 Families** - Complete with family codes and contact info
- **12-20 Evacuees** - Linked to families with various statuses
- **Special Needs** - Some evacuees marked with medical conditions

### Emergency Data
- **4 Help Requests** - Medical, missing person, supply, facility issues
- **3 Incidents** - Structure damage, utilities, medical emergencies

## Data Quality

### Geographic Validation
✅ All coordinates are **within Barangay Alicante boundary** using Shapely
✅ No locations outside the boundary polygon
✅ Proper latitude/longitude validation

### Realistic Values
✅ Center capacity: 50-200 people
✅ Occupancy: Random realistic levels
✅ Statuses: OPEN, FULL, CLOSED
✅ Severities: LOW, MODERATE, HIGH, CRITICAL

### No Duplicates
✅ Safe to run multiple times
✅ Won't create duplicate data
✅ Idempotent operation

## Accessing Test Data

### Login URLs
```
http://localhost:8000/login/
```

### Test Accounts
1. **techadmin / techadmin123** - Manage admin and staff accounts
2. **admin / admin123** - View the overall system, reports, maps, families, centers, incidents, and help requests
3. ** / staff123** - Manage families, evacuees, evacuation centers, safe/hazard areas, incidents, and citizen help requests

### Dashboard Access
```
http://localhost:8000/dashboard/
```

### View Maps
```
http://localhost:8000/mapping/              # Public map with hazard zones
http://localhost:8000/mapping/admin/        # Admin map for management
```

### Generate Reports
```
http://localhost:8000/reports/              # Report generator
```

## Testing All 11 Features

With test data loaded, you can test:

1. ✅ **User Authentication** - Login with different roles
2. ✅ **Evacuation Center Management** - View `/evacuation-centers/`
3. ✅ **Evacuee Registration** - See registered evacuees at `/evacuees/`
4. ✅ **Family Management** - View families at `/families/`
5. ✅ **Evacuee Tracking** - Check status updates `/evacuees/dashboard/`
6. ✅ **Family Reunification** - Monitor reunion progress `/families/dashboard/`
7. ✅ **Mapping & Boundaries** - View hazard/safe zones on `/mapping/`
8. ✅ **Help Requests** - See requests at `/emergency/help-requests/`
9. ✅ **Incident Reporting** - View incidents at `/emergency/incidents/`
10. ✅ **Occupancy Reports** - Generate at `/reports/`
11. ✅ **Geographic Validation** - All data within Barangay boundaries

## Testing Workflow

### 1. Generate Test Data
```bash
python manage.py create_test_data
```

### 2. Start Server
```bash
python manage.py runserver
```

### 3. Login as Admin
- URL: http://localhost:8000/login/
- User: admin
- Password: admin123

### 4. Test Each Module
- **Dashboard** → `/dashboard/` (Shows statistics)
- **Maps** → `/mapping/` (View boundary, zones)
- **Evacuees** → `/evacuees/` (30+ test evacuees)
- **Families** → `/families/` (6 test families)
- **Reports** → `/reports/` (Generate sample reports)
- **Emergency** → `/emergency/help-requests/` (4 requests)

### 5. Test With Different Roles
Try logging in as techadmin, admin, and staff to verify
role-based access control.

## Sample Data Distribution

```
Evacuation Centers
├─ Alicante Elementary School
├─ Barangay Hall
├─ Catholic Church
├─ Sports Complex
└─ Community Center

Hazard Zones
├─ Low-lying Area - North (FLOOD, HIGH)
├─ Coastal Evacuation (FLOOD, CRITICAL)
└─ Old Town Area (FIRE, MODERATE)

Families (6 total)
└─ Each with 2-5 evacuees

Test Users (3)
├─ Technical Admin
├─ Admin
└─ Staff
```

## Clearing Test Data

To clear test data and start fresh:

```bash
python manage.py flush
python manage.py migrate
python manage.py create_test_data   # Fresh data
```

## Troubleshooting

### "Barangay boundary not found"
- Load the boundary first: See SYSTEM_STATUS.md
- Boundary should be at `mapping/data/barangay_alicante.geojson`

### "No evacuation centers found"
- Command creates them automatically
- Check output shows center creation

### Duplicate records
- Command is idempotent
- Safe to run multiple times
- Won't recreate existing data

## Performance

- **Creation time**: < 2 seconds
- **Data size**: 50+ records across 11 models
- **Database**: Uses PostgreSQL, all data valid
- **Geographic**: All coordinates validated with Shapely

---

**Ready to test the system now!** 🚀

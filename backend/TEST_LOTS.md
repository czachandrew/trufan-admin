# Test Parking Lots

This document contains information about test parking lots created for development and testing.

## Greenfield Plaza Parking (Wisconsin)

**Location:** 5300 W Layton Ave, Greenfield, WI 53220
**Coordinates:** 42.9614, -88.0126
**Lot ID:** `b218fc80-646d-418e-8515-df9b61266e9d`

### Pricing
- Base Rate: $5.00
- Hourly Rate: $3.00/hour
- Max Daily Rate: $30.00
- Dynamic Multiplier: 1.0x

### Spaces (50 total)
- **Section A** (A-001 to A-030): 30 Standard spaces
- **Section B** (B-001 to B-005): 5 Handicap spaces
- **Section C** (C-001 to C-010): 10 EV charging spaces
- **Section D** (D-001 to D-005): 5 Valet spaces

### QR Codes for Testing
- **Lot-level parking:** `trufan://parking/lot/b218fc80-646d-418e-8515-df9b61266e9d`
- **Specific space (A-001):** `trufan://parking/lot/b218fc80-646d-418e-8515-df9b61266e9d/space/A-001`
- **EV space (C-005):** `trufan://parking/lot/b218fc80-646d-418e-8515-df9b61266e9d/space/C-005`

---

## Seven Mile Beach Parking (Grand Cayman)

**Location:** West Bay Road, Seven Mile Beach, Grand Cayman
**Coordinates:** 19.2866, -81.3744
**Lot ID:** `62ce8421-7725-4553-8c98-850db404bbb1`

### Pricing
- Base Rate: CI$8.00
- Hourly Rate: CI$5.00/hour
- Max Daily Rate: CI$50.00
- Dynamic Multiplier: 1.2x (premium beachfront location)

### Spaces (75 total)
- **Beach Level** (BEACH-001 to BEACH-040): 40 Standard spaces
- **Upper Level** (UPPER-001 to UPPER-020): 20 Standard spaces
- **Handicap** (HC-001 to HC-005): 5 Handicap spaces
- **Premium** (PREMIUM-001 to PREMIUM-010): 10 Premium beachfront spaces

### QR Codes for Testing
- **Lot-level parking:** `trufan://parking/lot/62ce8421-7725-4553-8c98-850db404bbb1`
- **Beach-level space:** `trufan://parking/lot/62ce8421-7725-4553-8c98-850db404bbb1/space/BEACH-001`
- **Premium space:** `trufan://parking/lot/62ce8421-7725-4553-8c98-850db404bbb1/space/PREMIUM-005`

---

## API Endpoints

### Get All Lots
```bash
curl http://localhost:8000/api/v1/parking/lots
```

### Get Specific Lot
```bash
# Greenfield
curl http://localhost:8000/api/v1/parking/lots/b218fc80-646d-418e-8515-df9b61266e9d

# Grand Cayman
curl http://localhost:8000/api/v1/parking/lots/62ce8421-7725-4553-8c98-850db404bbb1
```

### Create a Test Session
```bash
curl -X POST http://localhost:8000/api/v1/parking/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "lot_id": "b218fc80-646d-418e-8515-df9b61266e9d",
    "vehicle_plate": "TEST123",
    "vehicle_make": "Toyota",
    "vehicle_model": "Camry",
    "vehicle_color": "Silver",
    "duration_hours": 2.0,
    "contact_email": "test@example.com",
    "contact_phone": "+1-555-0100"
  }'
```

---

## Re-seeding Data

To recreate the test lots, run:

```bash
docker-compose exec api python -m scripts.seed_test_lots
```

**Note:** The script will refuse to run if lots with the same names already exist. Delete them manually from the database first if you need to recreate them.

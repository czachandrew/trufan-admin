# TruFan Parking - Mobile Client Development Prompt

## Project Overview

Build a cross-platform mobile application (iOS & Android) for TruFan Parking that allows users to find parking, create parking sessions, manage active sessions, and extend parking time - all without requiring user registration.

---

## Technical Requirements

### Technology Stack

**Framework:** React Native with Expo
- Expo SDK 49+
- React Native 0.72+
- TypeScript for type safety

**Key Libraries:**
- **Navigation:** React Navigation 6.x (stack + bottom tabs)
- **State Management:** React Context API + AsyncStorage
- **HTTP Client:** Axios with interceptors
- **QR Scanner:** expo-camera or expo-barcode-scanner
- **Maps:** react-native-maps with Google Maps/Apple Maps
- **Forms:** React Hook Form
- **Date/Time:** date-fns
- **Storage:** expo-secure-store for access codes
- **Deep Linking:** expo-linking
- **Notifications:** expo-notifications (for local reminders)

### API Integration

**Base URL:** `http://localhost:8000/api/v1` (development)
**Documentation:** See `MOBILE_CLIENT_API.md`
**Authentication:** None required (public API)
**Rate Limiting:** Handle 429 responses with exponential backoff

---

## Features & Screens

### 1. Home Screen (Tab: Home)

**Purpose:** Entry point for new parking sessions

**Layout:**
```
┌─────────────────────────────┐
│  TruFan Parking     [≡]     │
├─────────────────────────────┤
│                             │
│    [QR Scanner Button]      │
│    Large, centered          │
│    "Scan to Park"           │
│                             │
│    ─────── OR ──────        │
│                             │
│    [Browse Lots]            │
│    Secondary button         │
│                             │
│    ──────────────────       │
│                             │
│    Recent Sessions:         │
│    ┌─────────────────────┐ │
│    │ Downtown Garage     │ │
│    │ Space A-101         │ │
│    │ Expires: 2:30 PM    │ │
│    │ [View] [Extend]     │ │
│    └─────────────────────┘ │
│                             │
└─────────────────────────────┘
```

**Features:**
- Large "Scan QR Code" button (primary action)
- "Browse Nearby Lots" button
- List of active parking sessions from stored access codes
- Pull-to-refresh to update session statuses
- Quick actions: View Details, Extend Time

**API Calls:**
- Load saved access codes from SecureStore
- `GET /api/v1/parking/sessions/{access_code}` for each saved code
- Filter and display active sessions

**Implementation Notes:**
```typescript
// types.ts
interface ParkingSession {
  id: string;
  lot_id: string;
  lot_name: string;
  space_number?: string;
  vehicle_plate: string;
  start_time: string;
  expires_at: string;
  end_time?: string;
  base_price: string;
  actual_price?: string;
  status: SessionStatus;
  access_code: string;
  created_at: string;
}

type SessionStatus =
  | 'pending_payment'
  | 'active'
  | 'expiring_soon'
  | 'expired'
  | 'completed'
  | 'payment_failed';

// HomeScreen.tsx
const HomeScreen = () => {
  const [activeSessions, setActiveSessions] = useState<ParkingSession[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadActiveSessions();
  }, []);

  const loadActiveSessions = async () => {
    const codes = await getStoredAccessCodes();
    const sessions = await Promise.all(
      codes.map(code => fetchSession(code))
    );
    setActiveSessions(
      sessions.filter(s => s && ['active', 'expiring_soon'].includes(s.status))
    );
    setLoading(false);
  };

  return (
    <ScrollView>
      <Button onPress={handleScanQR}>Scan to Park</Button>
      <Button onPress={handleBrowseLots}>Browse Nearby Lots</Button>
      <SessionList sessions={activeSessions} />
    </ScrollView>
  );
};
```

---

### 2. QR Scanner Screen

**Purpose:** Scan lot or space QR codes

**Layout:**
```
┌─────────────────────────────┐
│ [<]  Scan QR Code           │
├─────────────────────────────┤
│                             │
│   ┌─────────────────────┐   │
│   │                     │   │
│   │   Camera View       │   │
│   │   with overlay      │   │
│   │   [- - - - - - -]   │   │
│   │                     │   │
│   └─────────────────────┘   │
│                             │
│  "Point camera at QR code"  │
│  "on parking sign"          │
│                             │
│  [Toggle Flash] [Gallery]   │
│                             │
└─────────────────────────────┘
```

**Features:**
- Full-screen camera view with QR overlay
- Auto-focus and scan on detection
- Toggle flashlight for dark parking garages
- Scan from gallery (photo of QR code)
- Haptic feedback on successful scan
- Parse `trufan://parking/...` URLs

**QR Code Formats:**
- Lot: `trufan://parking/lot/{lot_id}`
- Space: `trufan://parking/lot/{lot_id}/space/{space_number}`

**Implementation:**
```typescript
import { BarCodeScanner } from 'expo-barcode-scanner';

const QRScannerScreen = ({ navigation }) => {
  const [hasPermission, setHasPermission] = useState(null);
  const [scanned, setScanned] = useState(false);

  useEffect(() => {
    (async () => {
      const { status } = await BarCodeScanner.requestPermissionsAsync();
      setHasPermission(status === 'granted');
    })();
  }, []);

  const handleBarCodeScanned = ({ data }) => {
    if (scanned) return;
    setScanned(true);

    try {
      const url = new URL(data);

      if (url.protocol !== 'trufan:') {
        Alert.alert('Invalid QR Code', 'Please scan a TruFan parking QR code');
        setScanned(false);
        return;
      }

      const pathParts = url.pathname.split('/');
      const lotId = pathParts[3];
      const spaceNumber = pathParts[5] || null;

      // Navigate to lot details
      navigation.navigate('LotDetails', { lotId, spaceNumber });
    } catch (error) {
      Alert.alert('Error', 'Invalid QR code format');
      setScanned(false);
    }
  };

  return (
    <View style={styles.container}>
      <BarCodeScanner
        onBarCodeScanned={scanned ? undefined : handleBarCodeScanned}
        style={StyleSheet.absoluteFillObject}
      />
      <View style={styles.overlay}>
        <View style={styles.scanBox} />
      </View>
    </View>
  );
};
```

---

### 3. Lot Details Screen

**Purpose:** Show parking lot information and pricing

**Layout:**
```
┌─────────────────────────────┐
│ [<]  Downtown Garage        │
├─────────────────────────────┤
│                             │
│  📍 123 Main St            │
│  🚗 45 / 100 spaces         │
│                             │
│  ─────────────────────      │
│                             │
│  Pricing:                   │
│  • Base Rate: $10.00        │
│  • Hourly: $5.00/hr         │
│  • Max Daily: $50.00        │
│                             │
│  ─────────────────────      │
│                             │
│  Duration (hours):          │
│  [- 0.5  2.0  +]            │
│                             │
│  Estimated Cost: $20.00     │
│                             │
│  ─────────────────────      │
│                             │
│  [Continue to Details]      │
│                             │
└─────────────────────────────┘
```

**Features:**
- Display lot name, address, availability
- Show pricing breakdown
- Duration picker (0.5 hour increments, or custom)
- Real-time price calculation
- "Continue" button to parking form

**API Calls:**
- `GET /api/v1/parking/lots/{lot_id}`

**Implementation:**
```typescript
const LotDetailsScreen = ({ route, navigation }) => {
  const { lotId, spaceNumber } = route.params;
  const [lot, setLot] = useState<ParkingLot>(null);
  const [duration, setDuration] = useState(2.0);

  useEffect(() => {
    fetchLotDetails();
  }, [lotId]);

  const fetchLotDetails = async () => {
    const response = await api.get(`/parking/lots/${lotId}`);
    setLot(response.data);
  };

  const calculatePrice = () => {
    const baseRate = parseFloat(lot.base_rate);
    const hourlyRate = parseFloat(lot.hourly_rate);
    const maxDaily = parseFloat(lot.max_daily_rate);
    const multiplier = parseFloat(lot.dynamic_multiplier);

    let price = (baseRate + hourlyRate * duration) * multiplier;
    return Math.min(price, maxDaily).toFixed(2);
  };

  const handleContinue = () => {
    navigation.navigate('ParkingForm', {
      lot,
      spaceNumber,
      duration,
      estimatedPrice: calculatePrice()
    });
  };

  return (
    <ScrollView>
      <Text style={styles.title}>{lot?.name}</Text>
      <Text>{lot?.location_address}</Text>
      <Text>{lot?.available_spaces} / {lot?.total_spaces} spaces available</Text>

      <View style={styles.pricing}>
        <Text>Base Rate: ${lot?.base_rate}</Text>
        <Text>Hourly: ${lot?.hourly_rate}/hr</Text>
        <Text>Max Daily: ${lot?.max_daily_rate}</Text>
      </View>

      <DurationPicker value={duration} onChange={setDuration} />

      <Text style={styles.estimate}>Estimated Cost: ${calculatePrice()}</Text>

      <Button onPress={handleContinue}>Continue to Details</Button>
    </ScrollView>
  );
};
```

---

### 4. Parking Form Screen

**Purpose:** Collect vehicle info and contact details

**Layout:**
```
┌─────────────────────────────┐
│ [<]  Parking Details        │
├─────────────────────────────┤
│                             │
│  Vehicle Information:       │
│                             │
│  License Plate *            │
│  [ABC123____________]       │
│                             │
│  Make (optional)            │
│  [Toyota____________]       │
│                             │
│  Model (optional)           │
│  [Camry_____________]       │
│                             │
│  Color (optional)           │
│  [Blue______________]       │
│                             │
│  ─────────────────────      │
│                             │
│  Contact (required):        │
│                             │
│  ( ) Email                  │
│  [user@example.com__]       │
│                             │
│  ( ) Phone                  │
│  [+1 (555) 123-4567]        │
│                             │
│  ─────────────────────      │
│                             │
│  Duration: 2.0 hours        │
│  Price: $20.00              │
│                             │
│  [Create Parking Session]   │
│                             │
└─────────────────────────────┘
```

**Features:**
- Form with validation (React Hook Form)
- Required: license plate, duration, one contact method
- Optional: make, model, color
- Auto-format license plate (uppercase, no spaces)
- Auto-format phone number
- Email validation
- Summary of duration and price
- Loading state during submission

**API Calls:**
- `POST /api/v1/parking/sessions`

**Implementation:**
```typescript
import { useForm, Controller } from 'react-hook-form';

interface ParkingFormData {
  vehicle_plate: string;
  vehicle_make?: string;
  vehicle_model?: string;
  vehicle_color?: string;
  contact_email?: string;
  contact_phone?: string;
}

const ParkingFormScreen = ({ route, navigation }) => {
  const { lot, spaceNumber, duration, estimatedPrice } = route.params;
  const { control, handleSubmit, formState: { errors } } = useForm<ParkingFormData>();
  const [loading, setLoading] = useState(false);

  const onSubmit = async (data: ParkingFormData) => {
    // Validate at least one contact method
    if (!data.contact_email && !data.contact_phone) {
      Alert.alert('Error', 'Please provide email or phone number');
      return;
    }

    setLoading(true);

    try {
      const sessionData = {
        lot_id: lot.id,
        space_number: spaceNumber,
        duration_hours: duration,
        ...data
      };

      const response = await api.post('/parking/sessions', sessionData);
      const session = response.data;

      // Save access code
      await saveAccessCode(session.access_code);

      // Navigate to payment
      navigation.navigate('Payment', { session });
    } catch (error) {
      Alert.alert('Error', error.response?.data?.error?.message || 'Failed to create session');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView>
      <Text style={styles.sectionTitle}>Vehicle Information</Text>

      <Controller
        control={control}
        name="vehicle_plate"
        rules={{ required: 'License plate is required' }}
        render={({ field }) => (
          <TextInput
            {...field}
            placeholder="License Plate *"
            autoCapitalize="characters"
            onChangeText={(text) => field.onChange(text.toUpperCase().replace(/\s/g, ''))}
          />
        )}
      />
      {errors.vehicle_plate && <Text style={styles.error}>{errors.vehicle_plate.message}</Text>}

      <Controller
        control={control}
        name="contact_email"
        rules={{ pattern: { value: /^\S+@\S+$/, message: 'Invalid email' } }}
        render={({ field }) => (
          <TextInput
            {...field}
            placeholder="Email"
            keyboardType="email-address"
            autoCapitalize="none"
          />
        )}
      />

      <Text style={styles.summary}>Duration: {duration} hours</Text>
      <Text style={styles.summary}>Price: ${estimatedPrice}</Text>

      <Button
        onPress={handleSubmit(onSubmit)}
        loading={loading}
        disabled={loading}
      >
        Create Parking Session
      </Button>
    </ScrollView>
  );
};
```

---

### 5. Payment Screen

**Purpose:** Process simulated payment

**Layout:**
```
┌─────────────────────────────┐
│ [<]  Payment                │
├─────────────────────────────┤
│                             │
│  ✓ Session Created          │
│                             │
│  Access Code:               │
│  ABC12345                   │
│  (Saved automatically)      │
│                             │
│  ─────────────────────      │
│                             │
│  Summary:                   │
│  Downtown Garage            │
│  Space: A-101               │
│  Vehicle: ABC123            │
│                             │
│  Duration: 2.0 hours        │
│  Expires: 2:30 PM           │
│                             │
│  ─────────────────────      │
│                             │
│  Amount Due: $20.00         │
│                             │
│  [Pay Now]                  │
│  (Simulated)                │
│                             │
└─────────────────────────────┘
```

**Features:**
- Show session details and access code
- Display amount due
- "Pay Now" button (simulated payment)
- Success/failure handling
- Navigate to confirmation on success

**API Calls:**
- `POST /api/v1/parking/payments/simulate`

**Implementation:**
```typescript
const PaymentScreen = ({ route, navigation }) => {
  const { session } = route.params;
  const [processing, setProcessing] = useState(false);

  const handlePayment = async () => {
    setProcessing(true);

    try {
      const paymentData = {
        session_id: session.id,
        amount: session.base_price,
        should_succeed: true  // Always succeed for now
      };

      const response = await api.post('/parking/payments/simulate', paymentData);

      if (response.data.status === 'completed') {
        navigation.replace('PaymentSuccess', { session, payment: response.data });
      } else {
        Alert.alert('Payment Failed', 'Please try again');
      }
    } catch (error) {
      Alert.alert('Error', 'Payment processing failed');
    } finally {
      setProcessing(false);
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>✓ Session Created</Text>

      <View style={styles.accessCode}>
        <Text>Access Code:</Text>
        <Text style={styles.code}>{session.access_code}</Text>
        <Text style={styles.hint}>(Saved automatically)</Text>
      </View>

      <View style={styles.summary}>
        <Text>{session.lot_name}</Text>
        {session.space_number && <Text>Space: {session.space_number}</Text>}
        <Text>Vehicle: {session.vehicle_plate}</Text>
        <Text>Duration: {formatDuration(session.expires_at, session.start_time)}</Text>
        <Text>Expires: {formatTime(session.expires_at)}</Text>
      </View>

      <Text style={styles.amount}>Amount Due: ${session.base_price}</Text>

      <Button
        onPress={handlePayment}
        loading={processing}
        disabled={processing}
      >
        {processing ? 'Processing...' : 'Pay Now (Simulated)'}
      </Button>
    </ScrollView>
  );
};
```

---

### 6. Payment Success Screen

**Purpose:** Confirm successful payment

**Layout:**
```
┌─────────────────────────────┐
│          Success!           │
├─────────────────────────────┤
│                             │
│         [✓]                 │
│     (Large checkmark)       │
│                             │
│  Payment Successful         │
│  Your parking is active     │
│                             │
│  ─────────────────────      │
│                             │
│  Downtown Garage            │
│  Space: A-101               │
│  Expires: 2:30 PM           │
│                             │
│  Access Code: ABC12345      │
│                             │
│  ─────────────────────      │
│                             │
│  [View Active Sessions]     │
│  [Done]                     │
│                             │
└─────────────────────────────┘
```

**Features:**
- Success animation/icon
- Display session details
- Show access code (with copy button)
- Navigate to active sessions or home

---

### 7. My Sessions Screen (Tab: Sessions)

**Purpose:** View and manage all parking sessions

**Layout:**
```
┌─────────────────────────────┐
│  My Sessions        [+]     │
├─────────────────────────────┤
│                             │
│  Active (2)                 │
│  ┌─────────────────────────┐│
│  │ Downtown Garage         ││
│  │ Space: A-101            ││
│  │ 🚗 ABC123              ││
│  │                         ││
│  │ Expires in: 1h 23m      ││
│  │ [Extend] [End]          ││
│  └─────────────────────────┘│
│                             │
│  Completed (5)              │
│  [Show All]                 │
│                             │
│  ┌─────────────────────────┐│
│  │ City Center Lot         ││
│  │ Oct 28, 2:00 PM         ││
│  │ Duration: 2.0 hours     ││
│  │ Cost: $15.00            ││
│  └─────────────────────────┘│
│                             │
└─────────────────────────────┘
```

**Features:**
- Tabs: Active / Completed
- Active sessions with countdown timer
- Quick actions: Extend, End
- Session history
- Pull-to-refresh
- Add session manually (enter access code)

**Implementation:**
```typescript
const MySessionsScreen = () => {
  const [sessions, setSessions] = useState<ParkingSession[]>([]);
  const [activeTab, setActiveTab] = useState<'active' | 'completed'>('active');

  useEffect(() => {
    loadSessions();

    // Refresh every minute to update time remaining
    const interval = setInterval(loadSessions, 60000);
    return () => clearInterval(interval);
  }, []);

  const loadSessions = async () => {
    const codes = await getStoredAccessCodes();
    const allSessions = await Promise.all(
      codes.map(code => fetchSession(code))
    );
    setSessions(allSessions.filter(Boolean));
  };

  const activeSessions = sessions.filter(s =>
    ['active', 'expiring_soon'].includes(s.status)
  );

  const completedSessions = sessions.filter(s =>
    ['completed', 'expired'].includes(s.status)
  );

  return (
    <View>
      <SegmentedControl
        values={['Active', 'Completed']}
        selectedIndex={activeTab === 'active' ? 0 : 1}
        onChange={(index) => setActiveTab(index === 0 ? 'active' : 'completed')}
      />

      {activeTab === 'active' ? (
        <SessionList
          sessions={activeSessions}
          showActions
          onExtend={handleExtend}
          onEnd={handleEnd}
        />
      ) : (
        <SessionList sessions={completedSessions} />
      )}
    </View>
  );
};
```

---

### 8. Session Details Screen

**Purpose:** View complete session information

**Layout:**
```
┌─────────────────────────────┐
│ [<]  Session Details        │
├─────────────────────────────┤
│                             │
│  Status: Active 🟢          │
│                             │
│  ─────────────────────      │
│                             │
│  Parking Information:       │
│  • Lot: Downtown Garage     │
│  • Space: A-101             │
│  • Address: 123 Main St     │
│                             │
│  ─────────────────────      │
│                             │
│  Vehicle:                   │
│  • Plate: ABC123            │
│  • Make: Toyota Camry       │
│  • Color: Blue              │
│                             │
│  ─────────────────────      │
│                             │
│  Timing:                    │
│  • Started: 12:00 PM        │
│  • Expires: 2:00 PM         │
│  • Remaining: 1h 23m        │
│                             │
│  ─────────────────────      │
│                             │
│  Pricing:                   │
│  • Duration: 2.0 hours      │
│  • Cost: $20.00             │
│                             │
│  ─────────────────────      │
│                             │
│  Access Code: ABC12345      │
│  [Copy]                     │
│                             │
│  ─────────────────────      │
│                             │
│  [Extend Time]              │
│  [End Session]              │
│                             │
└─────────────────────────────┘
```

**Features:**
- Complete session details
- Status badge with color
- Time remaining with live update
- Copy access code
- Extend/End actions

---

### 9. Extend Session Screen

**Purpose:** Add more time to parking

**Layout:**
```
┌─────────────────────────────┐
│ [<]  Extend Parking         │
├─────────────────────────────┤
│                             │
│  Current Session:           │
│  Downtown Garage (A-101)    │
│  Expires: 2:00 PM           │
│                             │
│  ─────────────────────      │
│                             │
│  Add Time:                  │
│                             │
│  [0.5h] [1h] [2h] [Custom]  │
│                             │
│  Selected: 1.0 hours        │
│                             │
│  ─────────────────────      │
│                             │
│  New expiration: 3:00 PM    │
│  Additional cost: $5.00     │
│                             │
│  ─────────────────────      │
│                             │
│  [Confirm Extension]        │
│                             │
└─────────────────────────────┘
```

**Features:**
- Quick select buttons (0.5h, 1h, 2h)
- Custom duration input
- Calculate new expiration time
- Show additional cost
- Process payment for extension

**API Calls:**
- `POST /api/v1/parking/sessions/{access_code}/extend`

---

### 10. Map View Screen (Tab: Map)

**Purpose:** Browse parking lots on map

**Layout:**
```
┌─────────────────────────────┐
│  Nearby Parking     [List]  │
├─────────────────────────────┤
│                             │
│     [Map View]              │
│                             │
│     📍 Downtown Garage      │
│        45 spaces available  │
│                             │
│     📍 City Center          │
│        12 spaces available  │
│                             │
│                             │
│  [Bottom Sheet]             │
│  ┌─────────────────────────┐│
│  │ Downtown Garage         ││
│  │ 123 Main St             ││
│  │ 45 spaces • $10 base    ││
│  │ [View Details]          ││
│  └─────────────────────────┘│
└─────────────────────────────┘
```

**Features:**
- Interactive map with lot markers
- Marker color based on availability (green/yellow/red)
- Bottom sheet with lot details
- Toggle between map and list view
- Current location marker
- Tap marker to view details

**API Calls:**
- `GET /api/v1/parking/lots` (all active lots)

---

### 11. Settings Screen (Tab: Profile)

**Purpose:** App settings and preferences

**Layout:**
```
┌─────────────────────────────┐
│  Settings           [×]     │
├─────────────────────────────┤
│                             │
│  Saved Vehicles             │
│  ┌─────────────────────────┐│
│  │ ABC123 - Toyota Camry   ││
│  │ [Edit] [Delete]         ││
│  └─────────────────────────┘│
│  [+ Add Vehicle]            │
│                             │
│  ─────────────────────      │
│                             │
│  Notifications              │
│  • Expiration Reminders ✓   │
│  • 30 min before        ✓   │
│  • 15 min before        ✓   │
│                             │
│  ─────────────────────      │
│                             │
│  Contact Preferences        │
│  • Default Email:           │
│    user@example.com         │
│  • Default Phone:           │
│    +1 (555) 123-4567        │
│                             │
│  ─────────────────────      │
│                             │
│  About                      │
│  • Version: 1.0.0           │
│  • API Docs                 │
│  • Privacy Policy           │
│  • Terms of Service         │
│                             │
└─────────────────────────────┘
```

**Features:**
- Save vehicle info for quick reuse
- Notification preferences
- Default contact info
- App version and links

---

## State Management

### Context Structure

```typescript
// contexts/ParkingContext.tsx
interface ParkingContextType {
  activeSessions: ParkingSession[];
  completedSessions: ParkingSession[];
  loading: boolean;
  error: string | null;

  // Actions
  loadSessions: () => Promise<void>;
  createSession: (data: SessionCreateData) => Promise<ParkingSession>;
  extendSession: (accessCode: string, hours: number) => Promise<ParkingSession>;
  endSession: (accessCode: string) => Promise<ParkingSession>;
  addManualSession: (accessCode: string) => Promise<void>;
}

export const ParkingProvider = ({ children }) => {
  const [activeSessions, setActiveSessions] = useState<ParkingSession[]>([]);
  const [completedSessions, setCompletedSessions] = useState<ParkingSession[]>([]);

  const loadSessions = async () => {
    const codes = await getStoredAccessCodes();
    // ... fetch and categorize sessions
  };

  return (
    <ParkingContext.Provider value={{...}}>
      {children}
    </ParkingContext.Provider>
  );
};
```

---

## Utilities & Helpers

### API Client

```typescript
// services/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use((config) => {
  // Add correlation ID for debugging
  config.headers['X-Request-ID'] = uuid.v4();
  return config;
});

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 429) {
      // Handle rate limiting
      Alert.alert('Too Many Requests', 'Please wait a moment and try again');
    }
    return Promise.reject(error);
  }
);

export default api;
```

### Storage Service

```typescript
// services/storage.ts
import * as SecureStore from 'expo-secure-store';

const ACCESS_CODES_KEY = 'parking_access_codes';

export const getStoredAccessCodes = async (): Promise<string[]> => {
  const stored = await SecureStore.getItemAsync(ACCESS_CODES_KEY);
  return stored ? JSON.parse(stored) : [];
};

export const saveAccessCode = async (code: string): Promise<void> => {
  const codes = await getStoredAccessCodes();
  if (!codes.includes(code)) {
    codes.push(code);
    await SecureStore.setItemAsync(ACCESS_CODES_KEY, JSON.stringify(codes));
  }
};

export const removeAccessCode = async (code: string): Promise<void> => {
  let codes = await getStoredAccessCodes();
  codes = codes.filter(c => c !== code);
  await SecureStore.setItemAsync(ACCESS_CODES_KEY, JSON.stringify(codes));
};
```

### Date/Time Helpers

```typescript
// utils/time.ts
import { format, formatDistanceToNow } from 'date-fns';

export const formatTime = (dateString: string): string => {
  return format(new Date(dateString), 'h:mm a');
};

export const formatDate = (dateString: string): string => {
  return format(new Date(dateString), 'MMM d, yyyy');
};

export const getTimeRemaining = (expiresAt: string): string => {
  const now = new Date();
  const expires = new Date(expiresAt);
  const diff = expires.getTime() - now.getTime();

  if (diff <= 0) return 'Expired';

  const hours = Math.floor(diff / (1000 * 60 * 60));
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
};

export const formatDuration = (startTime: string, expiresAt: string): string => {
  const start = new Date(startTime);
  const end = new Date(expiresAt);
  const hours = (end.getTime() - start.getTime()) / (1000 * 60 * 60);
  return `${hours.toFixed(1)} hours`;
};
```

---

## Styling Guidelines

### Theme

```typescript
// theme.ts
export const theme = {
  colors: {
    primary: '#007AFF',
    secondary: '#5856D6',
    success: '#34C759',
    warning: '#FF9500',
    danger: '#FF3B30',
    background: '#F2F2F7',
    card: '#FFFFFF',
    text: '#000000',
    textSecondary: '#8E8E93',
    border: '#C6C6C8',
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
  },
  borderRadius: {
    sm: 8,
    md: 12,
    lg: 16,
  },
  typography: {
    title: {
      fontSize: 28,
      fontWeight: '700',
    },
    heading: {
      fontSize: 20,
      fontWeight: '600',
    },
    body: {
      fontSize: 16,
      fontWeight: '400',
    },
    caption: {
      fontSize: 14,
      fontWeight: '400',
    },
  },
};
```

---

## Testing

### Unit Tests
- Utility functions (time formatting, price calculation)
- API service methods
- Context reducers

### Integration Tests
- Complete user flows (create session, extend, end)
- QR code parsing
- Error handling

### E2E Tests (Detox)
- Scan QR → Create Session → Payment → Success
- Browse Lots → Create Session
- View Sessions → Extend Session

---

## Deployment

### iOS
- Expo build service or EAS Build
- App Store submission
- TestFlight for beta testing

### Android
- Expo build service or EAS Build
- Google Play Store submission
- Internal testing track

---

## Future Enhancements

1. **User Accounts** - Optional login for payment methods, history
2. **Real Stripe Integration** - Replace simulated payments
3. **Push Notifications** - Server-sent expiration reminders
4. **Favorites** - Save frequently used lots
5. **Parking History** - Detailed history with receipts
6. **Multiple Vehicles** - Manage fleet
7. **Valet Mode** - Special flow for valet parking
8. **Offline Mode** - Cache data, sync when online

---

## Development Checklist

- [ ] Project setup with Expo
- [ ] Navigation structure (stack + tabs)
- [ ] API client with interceptors
- [ ] State management (Context API)
- [ ] Secure storage for access codes
- [ ] Home screen with active sessions
- [ ] QR scanner with camera permissions
- [ ] Lot details screen
- [ ] Parking form with validation
- [ ] Payment simulation
- [ ] Session management (extend, end)
- [ ] Map view with markers
- [ ] Settings screen
- [ ] Deep linking configuration
- [ ] Error handling throughout
- [ ] Loading states
- [ ] Pull-to-refresh
- [ ] Time formatting and countdown
- [ ] Unit tests
- [ ] E2E tests
- [ ] iOS build and testing
- [ ] Android build and testing
- [ ] App store submission

---

## Example Project Structure

```
mobile/
├── src/
│   ├── screens/
│   │   ├── HomeScreen.tsx
│   │   ├── QRScannerScreen.tsx
│   │   ├── LotDetailsScreen.tsx
│   │   ├── ParkingFormScreen.tsx
│   │   ├── PaymentScreen.tsx
│   │   ├── PaymentSuccessScreen.tsx
│   │   ├── MySessionsScreen.tsx
│   │   ├── SessionDetailsScreen.tsx
│   │   ├── ExtendSessionScreen.tsx
│   │   ├── MapViewScreen.tsx
│   │   └── SettingsScreen.tsx
│   ├── navigation/
│   │   ├── AppNavigator.tsx
│   │   └── types.ts
│   ├── components/
│   │   ├── SessionCard.tsx
│   │   ├── SessionList.tsx
│   │   ├── DurationPicker.tsx
│   │   ├── Button.tsx
│   │   └── LoadingSpinner.tsx
│   ├── contexts/
│   │   └── ParkingContext.tsx
│   ├── services/
│   │   ├── api.ts
│   │   ├── storage.ts
│   │   └── notifications.ts
│   ├── utils/
│   │   ├── time.ts
│   │   ├── qr.ts
│   │   └── validation.ts
│   ├── types/
│   │   └── index.ts
│   ├── theme.ts
│   └── App.tsx
├── assets/
├── app.json
├── package.json
└── tsconfig.json
```

---

## Getting Started

```bash
# Create new Expo project
npx create-expo-app trufan-mobile --template

# Install dependencies
cd trufan-mobile
npm install @react-navigation/native @react-navigation/stack @react-navigation/bottom-tabs
npm install axios react-hook-form date-fns
npm install expo-camera expo-barcode-scanner expo-secure-store expo-linking
npm install react-native-maps

# Start development
npm start
```

---

This prompt provides everything needed to build a fully functional mobile client for TruFan Parking. Follow the screens, features, and implementation examples to create a polished, user-friendly parking app.

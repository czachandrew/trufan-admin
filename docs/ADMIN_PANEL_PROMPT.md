# TruFan Parking - Admin Panel Development Prompt

## Project Overview

Build a modern web-based admin panel for managing the TruFan Parking system. The panel provides comprehensive tools for parking lot management, session monitoring, customer support, analytics, and system configuration.

---

## Technical Requirements

### Technology Stack

**Framework:** React 18+ with TypeScript
**Build Tool:** Vite
**Routing:** React Router v6
**State Management:** Zustand or Redux Toolkit
**HTTP Client:** Axios with interceptors
**UI Framework:** Material-UI (MUI) v5 or Ant Design
**Forms:** React Hook Form with Yup validation
**Charts:** Recharts or Chart.js
**Tables:** TanStack Table (React Table v8)
**Date/Time:** date-fns
**Authentication:** JWT with refresh tokens
**Icons:** Material Icons or Ant Design Icons

### Key Libraries

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "zustand": "^4.4.0",
    "@mui/material": "^5.14.0",
    "@mui/icons-material": "^5.14.0",
    "@emotion/react": "^11.11.0",
    "@emotion/styled": "^11.11.0",
    "axios": "^1.6.0",
    "react-hook-form": "^7.48.0",
    "yup": "^1.3.0",
    "@tanstack/react-table": "^8.10.0",
    "recharts": "^2.10.0",
    "date-fns": "^2.30.0",
    "react-toastify": "^9.1.0",
    "qrcode.react": "^3.1.0"
  }
}
```

---

## Features & Pages

### 1. Login Page

**Route:** `/login`
**Auth:** Public

**Layout:**
```
┌─────────────────────────────────┐
│                                 │
│         TruFan Parking          │
│         Admin Portal            │
│                                 │
│   ┌─────────────────────────┐   │
│   │ Email                   │   │
│   │ [________________]      │   │
│   │                         │   │
│   │ Password                │   │
│   │ [________________]      │   │
│   │                         │   │
│   │ [ ] Remember me         │   │
│   │                         │   │
│   │ [Login Button]          │   │
│   │                         │   │
│   │ Forgot password?        │   │
│   └─────────────────────────┘   │
│                                 │
└─────────────────────────────────┘
```

**Features:**
- Email + password authentication
- "Remember me" checkbox (stores refresh token)
- Forgot password link
- Form validation
- Loading state
- Error messages
- Redirect to dashboard on success

**Implementation:**
```typescript
import { useForm } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';

const loginSchema = yup.object({
  email: yup.string().email().required(),
  password: yup.string().required(),
  remember: yup.boolean()
});

type LoginForm = yup.InferType<typeof loginSchema>;

const LoginPage = () => {
  const navigate = useNavigate();
  const { register, handleSubmit, formState: { errors } } = useForm<LoginForm>({
    resolver: yupResolver(loginSchema)
  });

  const onSubmit = async (data: LoginForm) => {
    try {
      const response = await api.post('/auth/login', {
        email: data.email,
        password: data.password
      });

      // Store tokens
      localStorage.setItem('access_token', response.data.access_token);
      if (data.remember) {
        localStorage.setItem('refresh_token', response.data.refresh_token);
      }

      // Check if admin/staff role
      if (!['admin', 'staff'].includes(response.data.user.role)) {
        throw new Error('Insufficient permissions');
      }

      // Redirect to dashboard
      navigate('/dashboard');
    } catch (error) {
      toast.error(error.message);
    }
  };

  return (
    <Container>
      <Paper>
        <Typography variant="h4">TruFan Parking Admin</Typography>
        <form onSubmit={handleSubmit(onSubmit)}>
          <TextField
            {...register('email')}
            label="Email"
            error={!!errors.email}
            helperText={errors.email?.message}
          />
          <TextField
            {...register('password')}
            type="password"
            label="Password"
            error={!!errors.password}
            helperText={errors.password?.message}
          />
          <FormControlLabel
            control={<Checkbox {...register('remember')} />}
            label="Remember me"
          />
          <Button type="submit">Login</Button>
        </form>
      </Paper>
    </Container>
  );
};
```

---

### 2. Dashboard Page

**Route:** `/dashboard`
**Auth:** Required (admin/staff)

**Layout:**
```
┌──────────────────────────────────────────────┐
│ TruFan Admin   [Bell] [User Menu]           │
├──────┬───────────────────────────────────────┤
│      │                                       │
│ Lots │  Dashboard                            │
│      │                                       │
│ Sess │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐│
│ ions │  │ 150  │ │  45  │ │ $3.2K│ │ 75% ││
│      │  │Sess. │ │Active│ │ Rev. │ │ Occ. ││
│ Anal │  └──────┘ └──────┘ └──────┘ └──────┘│
│ ytics│                                       │
│      │  Revenue Trend (7 days)              │
│ Users│  ┌─────────────────────────────────┐ │
│      │  │      📊 Line Chart              │ │
│ QR   │  │                                 │ │
│ Codes│  │                                 │ │
│      │  └─────────────────────────────────┘ │
│ Sett │                                       │
│ ings│  Active Sessions by Lot              │
│      │  ┌─────────────────────────────────┐ │
│      │  │ Downtown: 30 (75%)              │ │
│      │  │ City Center: 15 (60%)           │ │
│      │  └─────────────────────────────────┘ │
└──────┴───────────────────────────────────────┘
```

**Features:**
- Key metrics cards (sessions, revenue, occupancy)
- Revenue trend chart (last 7 days)
- Active sessions by lot
- Quick actions (Add Lot, View Sessions)
- Real-time data refresh

**Implementation:**
```typescript
interface DashboardMetrics {
  total_sessions: number;
  active_sessions: number;
  total_revenue: string;
  occupancy_rate: number;
}

const DashboardPage = () => {
  const [metrics, setMetrics] = useState<DashboardMetrics>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();

    // Refresh every 30 seconds
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    const response = await api.get('/admin/analytics/dashboard');
    setMetrics(response.data.summary);
    setLoading(false);
  };

  return (
    <Box>
      <Typography variant="h4">Dashboard</Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Total Sessions"
            value={metrics?.total_sessions}
            icon={<DirectionsCar />}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Active Now"
            value={metrics?.active_sessions}
            icon={<LocalParking />}
            color="success"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Revenue Today"
            value={`$${metrics?.total_revenue}`}
            icon={<AttachMoney />}
            color="primary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Occupancy"
            value={`${(metrics?.occupancy_rate * 100).toFixed(0)}%`}
            icon={<Speed />}
            color="warning"
          />
        </Grid>
      </Grid>

      <RevenueTrendChart />
      <ActiveSessionsList />
    </Box>
  );
};
```

---

### 3. Parking Lots Page

**Route:** `/lots`
**Auth:** Required (admin/staff)

**Layout:**
```
┌──────────────────────────────────────────────┐
│ Parking Lots                    [+ New Lot]  │
├──────────────────────────────────────────────┤
│                                              │
│ Search: [_________]  Status: [All▼]         │
│                                              │
│ ┌────────────────────────────────────────┐   │
│ │ Name         Spaces  Occupancy  Actions│   │
│ ├────────────────────────────────────────┤   │
│ │ Downtown     45/100   75%      [Edit]  │   │
│ │ City Center  12/50    60%      [Edit]  │   │
│ │ Airport      80/200   40%      [Edit]  │   │
│ └────────────────────────────────────────┘   │
│                                              │
│ Showing 1-3 of 3  [< 1 >]                    │
└──────────────────────────────────────────────┘
```

**Features:**
- Data table with sorting, filtering, pagination
- Search by name/address
- Filter by active status
- Real-time occupancy display
- Color-coded occupancy (green/yellow/red)
- Quick actions: Edit, View Details, Generate QR
- Create new lot button

**Implementation:**
```typescript
const ParkingLotsPage = () => {
  const [lots, setLots] = useState<ParkingLot[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all');

  useEffect(() => {
    fetchLots();
  }, [page, search, statusFilter]);

  const fetchLots = async () => {
    const params = {
      page,
      limit: 20,
      ...(search && { search }),
      ...(statusFilter !== 'all' && { is_active: statusFilter === 'active' })
    };

    const response = await api.get('/admin/parking/lots', { params });
    setLots(response.data.items);
    setLoading(false);
  };

  const columns = useMemo(() => [
    {
      Header: 'Name',
      accessor: 'name',
      Cell: ({ row }) => (
        <Box>
          <Typography>{row.original.name}</Typography>
          <Typography variant="caption" color="textSecondary">
            {row.original.location_address}
          </Typography>
        </Box>
      )
    },
    {
      Header: 'Spaces',
      accessor: 'available_spaces',
      Cell: ({ row }) => (
        `${row.original.available_spaces} / ${row.original.total_spaces}`
      )
    },
    {
      Header: 'Occupancy',
      accessor: 'occupancy',
      Cell: ({ row }) => {
        const rate = (row.original.total_spaces - row.original.available_spaces) /
                     row.original.total_spaces;
        return (
          <Box display="flex" alignItems="center">
            <LinearProgress
              variant="determinate"
              value={rate * 100}
              sx={{ width: 100, mr: 1 }}
              color={rate > 0.8 ? 'error' : rate > 0.6 ? 'warning' : 'success'}
            />
            <Typography>{(rate * 100).toFixed(0)}%</Typography>
          </Box>
        );
      }
    },
    {
      Header: 'Actions',
      Cell: ({ row }) => (
        <IconButton onClick={() => navigate(`/lots/${row.original.id}`)}>
          <Edit />
        </IconButton>
      )
    }
  ], []);

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" mb={3}>
        <Typography variant="h4">Parking Lots</Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => navigate('/lots/new')}
        >
          New Lot
        </Button>
      </Box>

      <Paper>
        <Box p={2} display="flex" gap={2}>
          <TextField
            placeholder="Search lots..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            InputProps={{
              startAdornment: <Search />
            }}
          />
          <Select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <MenuItem value="all">All Status</MenuItem>
            <MenuItem value="active">Active</MenuItem>
            <MenuItem value="inactive">Inactive</MenuItem>
          </Select>
        </Box>

        <DataTable columns={columns} data={lots} loading={loading} />

        <Pagination count={10} page={page} onChange={(e, p) => setPage(p)} />
      </Paper>
    </Box>
  );
};
```

---

### 4. Lot Details / Edit Page

**Route:** `/lots/:id`
**Auth:** Required (admin/staff)

**Layout:**
```
┌──────────────────────────────────────────────┐
│ [<] Downtown Garage                  [Save]  │
├──────────────────────────────────────────────┤
│                                              │
│ ┌─ Basic Information ────────────────────┐  │
│ │ Name: [Downtown Garage___________]    │  │
│ │ Description: [Multi-level parking__]  │  │
│ │ Address: [123 Main St, NY_________]   │  │
│ │ Lat/Lng: [40.7128]  [-74.0060]        │  │
│ └────────────────────────────────────────┘  │
│                                              │
│ ┌─ Capacity ──────────────────────────────┐│
│ │ Total Spaces: [100]                    ││
│ │ Available: 45 (auto-calculated)        ││
│ │ Status: [✓] Active                     ││
│ └────────────────────────────────────────┘ │
│                                              │
│ ┌─ Pricing Configuration ────────────────┐  │
│ │ Base Rate: [$10.00]                    │  │
│ │ Hourly Rate: [$5.00]                   │  │
│ │ Max Daily: [$50.00]                    │  │
│ │ Min Duration: [15] minutes             │  │
│ │ Max Duration: [24] hours               │  │
│ │ Dynamic Multiplier: [1.0]              │  │
│ └────────────────────────────────────────┘  │
│                                              │
│ ┌─ Parking Spaces ───────────────────────┐  │
│ │ [+ Add Space]  [+ Bulk Create]        │  │
│ │                                        │  │
│ │ A-101 (Standard)  [Edit] [Delete]     │  │
│ │ A-102 (Standard)  [Edit] [Delete]     │  │
│ │ A-103 (Handicap)  [Edit] [Delete]     │  │
│ │                                        │  │
│ │ Showing 3 of 100  [View All]          │  │
│ └────────────────────────────────────────┘  │
│                                              │
│ ┌─ QR Codes ─────────────────────────────┐  │
│ │ [Generate Lot QR]                      │  │
│ │ [Generate All Space QRs (PDF)]         │  │
│ └────────────────────────────────────────┘  │
└──────────────────────────────────────────────┘
```

**Features:**
- Editable form with validation
- Map picker for lat/lng
- Pricing configuration
- Space management (add, edit, delete)
- Bulk space creation
- QR code generation
- Save/cancel buttons

---

### 5. Sessions Page

**Route:** `/sessions`
**Auth:** Required (admin/staff)

**Layout:**
```
┌──────────────────────────────────────────────┐
│ Parking Sessions                             │
├──────────────────────────────────────────────┤
│                                              │
│ Search: [________]  Status: [Active▼]       │
│ Lot: [All▼]  Date: [Today▼]                 │
│                                              │
│ ┌────────────────────────────────────────┐   │
│ │Plate  Lot      Space  Start   Expires  │   │
│ ├────────────────────────────────────────┤   │
│ │ABC123 Downtown A-101  10:00   12:00 PM│   │
│ │       🟢 Active  |1h 23m| [Extend][End]│   │
│ │                                        │   │
│ │XYZ789 City Ctr  B-205  09:00   11:00 AM│  │
│ │       🟡 Expiring |12m|  [Extend][End] │   │
│ └────────────────────────────────────────┘   │
│                                              │
│ Showing 1-2 of 45  [< 1 2 3 >]               │
└──────────────────────────────────────────────┘
```

**Features:**
- Real-time session list
- Filter by status, lot, date range
- Search by license plate or access code
- Status badges with colors
- Time remaining countdown
- Quick actions: Extend, End
- Click row for details
- Export to CSV

**Implementation:**
```typescript
const SessionsPage = () => {
  const [sessions, setSessions] = useState<ParkingSession[]>([]);
  const [filters, setFilters] = useState({
    status: 'active',
    lot_id: null,
    date_range: 'today'
  });

  const statusColors = {
    active: 'success',
    expiring_soon: 'warning',
    expired: 'error',
    completed: 'info',
    pending_payment: 'default'
  };

  const columns = [
    {
      Header: 'Vehicle',
      accessor: 'vehicle_plate',
      Cell: ({ row }) => (
        <Box>
          <Typography variant="body2" fontWeight="bold">
            {row.original.vehicle_plate}
          </Typography>
          {row.original.vehicle_make && (
            <Typography variant="caption" color="textSecondary">
              {row.original.vehicle_make} {row.original.vehicle_model}
            </Typography>
          )}
        </Box>
      )
    },
    {
      Header: 'Location',
      Cell: ({ row }) => (
        <Box>
          <Typography variant="body2">{row.original.lot_name}</Typography>
          {row.original.space_number && (
            <Typography variant="caption">Space {row.original.space_number}</Typography>
          )}
        </Box>
      )
    },
    {
      Header: 'Status',
      accessor: 'status',
      Cell: ({ value }) => (
        <Chip
          label={value.replace('_', ' ')}
          size="small"
          color={statusColors[value]}
        />
      )
    },
    {
      Header: 'Time Remaining',
      Cell: ({ row }) => {
        const remaining = getTimeRemaining(row.original.expires_at);
        return (
          <Typography variant="body2" color={remaining.includes('Expired') ? 'error' : 'inherit'}>
            {remaining}
          </Typography>
        );
      }
    },
    {
      Header: 'Actions',
      Cell: ({ row }) => (
        <Box>
          {['active', 'expiring_soon'].includes(row.original.status) && (
            <>
              <IconButton size="small" onClick={() => handleExtend(row.original.id)}>
                <AddCircle />
              </IconButton>
              <IconButton size="small" onClick={() => handleEnd(row.original.id)}>
                <Cancel />
              </IconButton>
            </>
          )}
        </Box>
      )
    }
  ];

  return (
    <Box>
      <Typography variant="h4">Parking Sessions</Typography>

      <SessionFilters filters={filters} onChange={setFilters} />

      <DataTable columns={columns} data={sessions} />
    </Box>
  );
};
```

---

### 6. Session Details Modal/Page

**Route:** `/sessions/:id` or Modal
**Auth:** Required (admin/staff)

**Features:**
- Complete session information
- Vehicle details
- Timing and duration
- Pricing breakdown
- Contact information
- Admin actions (extend, end, cancel)
- Activity log

---

### 7. Analytics Page

**Route:** `/analytics`
**Auth:** Required (admin/staff, revenue view for admin only)

**Layout:**
```
┌──────────────────────────────────────────────┐
│ Analytics                                    │
├──────────────────────────────────────────────┤
│                                              │
│ Date Range: [Last 7 days▼]  [Custom]        │
│                                              │
│ ┌─ Revenue ────────────────────────────────┐ │
│ │ Total: $15,000                           │ │
│ │ Average per session: $20                 │ │
│ │                                          │ │
│ │ Revenue Trend                            │ │
│ │ ┌──────────────────────────────────────┐││
│ │ │      📊 Bar Chart                    │││
│ │ │                                      │││
│ │ └──────────────────────────────────────┘││
│ └──────────────────────────────────────────┘ │
│                                              │
│ ┌─ Occupancy ──────────────────────────────┐│
│ │ Current: 65%                             ││
│ │ Peak today: 90% (1:00 PM)                ││
│ │                                          ││
│ │ Occupancy by Hour                        ││
│ │ ┌──────────────────────────────────────┐││
│ │ │      📊 Line Chart                   │││
│ │ └──────────────────────────────────────┘││
│ └──────────────────────────────────────────┘│
│                                              │
│ ┌─ Session Duration ───────────────────────┐│
│ │ Average: 2.5 hours                       ││
│ │ Median: 2.0 hours                        ││
│ │                                          ││
│ │ Duration Distribution                    ││
│ │ ┌──────────────────────────────────────┐││
│ │ │      📊 Pie Chart                    │││
│ │ └──────────────────────────────────────┘││
│ └──────────────────────────────────────────┘│
└──────────────────────────────────────────────┘
```

**Features:**
- Revenue metrics and trends
- Occupancy analysis
- Session duration analysis
- Peak hours identification
- Lot comparison
- Export reports (CSV, PDF)

---

### 8. QR Code Generator Page

**Route:** `/qr-codes`
**Auth:** Required (admin/staff)

**Layout:**
```
┌──────────────────────────────────────────────┐
│ QR Code Generator                            │
├──────────────────────────────────────────────┤
│                                              │
│ ┌─ Generate QR Codes ──────────────────────┐│
│ │                                          ││
│ │ Type:                                    ││
│ │ ( ) Lot-Level (any space)                ││
│ │ (•) Space-Specific                       ││
│ │                                          ││
│ │ Select Lot: [Downtown Garage▼]          ││
│ │                                          ││
│ │ Spaces: [Select All] [Select None]      ││
│ │ [✓] A-101  [✓] A-102  [ ] A-103         ││
│ │                                          ││
│ │ Format:                                  ││
│ │ (•) Individual PNGs                      ││
│ │ ( ) Single PDF (4x4 grid)                ││
│ │ ( ) SVG (vector)                         ││
│ │                                          ││
│ │ Size: [512px▼]                           ││
│ │                                          ││
│ │ Options:                                 ││
│ │ [✓] Include space number on label        ││
│ │ [✓] Include QR data text                 ││
│ │ [✓] Add TruFan branding                  ││
│ │                                          ││
│ │ [Generate QR Codes]                      ││
│ └──────────────────────────────────────────┘│
│                                              │
│ ┌─ Generated Codes ────────────────────────┐│
│ │                                          ││
│ │ ┌────────┐ ┌────────┐ ┌────────┐        ││
│ │ │ A-101  │ │ A-102  │ │ A-103  │        ││
│ │ │ [QR]   │ │ [QR]   │ │ [QR]   │        ││
│ │ │[Download]│[Download]│[Download]│       ││
│ │ └────────┘ └────────┘ └────────┘        ││
│ │                                          ││
│ │ [Download All as ZIP]                    ││
│ └──────────────────────────────────────────┘│
└──────────────────────────────────────────────┘
```

**Features:**
- Generate lot-level or space-specific QR codes
- Multiple format options (PNG, SVG, PDF)
- Customizable size
- Batch generation
- Preview before download
- Download individual or bulk

**Implementation:**
```typescript
import QRCode from 'qrcode.react';

const QRCodeGeneratorPage = () => {
  const [type, setType] = useState<'lot' | 'space'>('space');
  const [selectedLot, setSelectedLot] = useState<ParkingLot>(null);
  const [selectedSpaces, setSelectedSpaces] = useState<string[]>([]);
  const [format, setFormat] = useState<'png' | 'pdf' | 'svg'>('png');
  const [generated, setGenerated] = useState<GeneratedQR[]>([]);

  const generateQRCodes = async () => {
    if (type === 'lot') {
      const qrData = `trufan://parking/lot/${selectedLot.id}`;
      // Generate single QR code
    } else {
      // Generate QR code for each selected space
      const codes = selectedSpaces.map(spaceNumber => ({
        space_number: spaceNumber,
        qr_data: `trufan://parking/lot/${selectedLot.id}/space/${spaceNumber}`
      }));
      setGenerated(codes);
    }
  };

  return (
    <Box>
      <Typography variant="h4">QR Code Generator</Typography>

      <Paper sx={{ p: 3, mb: 3 }}>
        <FormControl>
          <FormLabel>Type</FormLabel>
          <RadioGroup value={type} onChange={(e) => setType(e.target.value)}>
            <FormControlLabel value="lot" control={<Radio />} label="Lot-Level" />
            <FormControlLabel value="space" control={<Radio />} label="Space-Specific" />
          </RadioGroup>
        </FormControl>

        <LotSelect value={selectedLot} onChange={setSelectedLot} />

        {type === 'space' && (
          <SpaceSelector
            lotId={selectedLot?.id}
            selected={selectedSpaces}
            onChange={setSelectedSpaces}
          />
        )}

        <Button onClick={generateQRCodes}>Generate QR Codes</Button>
      </Paper>

      {generated.length > 0 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6">Generated Codes</Typography>
          <Grid container spacing={2}>
            {generated.map(code => (
              <Grid item xs={12} sm={6} md={4} key={code.space_number}>
                <Card>
                  <CardContent>
                    <Typography>{code.space_number}</Typography>
                    <QRCode value={code.qr_data} size={200} />
                    <Button onClick={() => downloadQR(code)}>Download</Button>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Paper>
      )}
    </Box>
  );
};
```

---

### 9. User Management Page

**Route:** `/users`
**Auth:** Required (admin only)

**Features:**
- List all users
- Filter by role
- Update user roles
- Deactivate users
- View user activity

---

### 10. Settings Page

**Route:** `/settings`
**Auth:** Required (admin/staff)

**Features:**
- System configuration
- Email/SMS settings (future)
- Notification preferences
- API keys (future)
- Audit logs

---

## Layout & Navigation

### App Shell Structure

```typescript
const AppLayout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <Box sx={{ display: 'flex' }}>
      {/* App Bar */}
      <AppBar position="fixed">
        <Toolbar>
          <IconButton onClick={() => setSidebarOpen(!sidebarOpen)}>
            <Menu />
          </IconButton>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            TruFan Admin
          </Typography>
          <IconButton>
            <Notifications />
          </IconButton>
          <UserMenu />
        </Toolbar>
      </AppBar>

      {/* Sidebar */}
      <Drawer open={sidebarOpen} variant="persistent">
        <List>
          <ListItem button component={Link} to="/dashboard">
            <ListItemIcon><Dashboard /></ListItemIcon>
            <ListItemText>Dashboard</ListItemText>
          </ListItem>
          <ListItem button component={Link} to="/lots">
            <ListItemIcon><LocalParking /></ListItemIcon>
            <ListItemText>Parking Lots</ListItemText>
          </ListItem>
          <ListItem button component={Link} to="/sessions">
            <ListItemIcon><DirectionsCar /></ListItemIcon>
            <ListItemText>Sessions</ListItemText>
          </ListItem>
          <ListItem button component={Link} to="/analytics">
            <ListItemIcon><BarChart /></ListItemIcon>
            <ListItemText>Analytics</ListItemText>
          </ListItem>
          <ListItem button component={Link} to="/qr-codes">
            <ListItemIcon><QrCode2 /></ListItemIcon>
            <ListItemText>QR Codes</ListItemText>
          </ListItem>
          <ListItem button component={Link} to="/users">
            <ListItemIcon><People /></ListItemIcon>
            <ListItemText>Users</ListItemText>
          </ListItem>
          <ListItem button component={Link} to="/settings">
            <ListItemIcon><Settings /></ListItemIcon>
            <ListItemText>Settings</ListItemText>
          </ListItem>
        </List>
      </Drawer>

      {/* Main Content */}
      <Box component="main" sx={{ flexGrow: 1, p: 3, mt: 8 }}>
        <Outlet />
      </Box>
    </Box>
  );
};
```

---

## State Management

### Auth Store (Zustand)

```typescript
interface AuthState {
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;

  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  accessToken: localStorage.getItem('access_token'),
  isAuthenticated: !!localStorage.getItem('access_token'),

  login: async (email, password) => {
    const response = await api.post('/auth/login', { email, password });
    localStorage.setItem('access_token', response.data.access_token);
    localStorage.setItem('refresh_token', response.data.refresh_token);
    set({ user: response.data.user, accessToken: response.data.access_token, isAuthenticated: true });
  },

  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    set({ user: null, accessToken: null, isAuthenticated: false });
  },

  refreshToken: async () => {
    const refreshToken = localStorage.getItem('refresh_token');
    const response = await api.post('/auth/refresh', { refresh_token: refreshToken });
    localStorage.setItem('access_token', response.data.access_token);
    set({ accessToken: response.data.access_token });
  }
}));
```

---

## Routing & Protected Routes

```typescript
const Router = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/lots" element={<ParkingLotsPage />} />
            <Route path="/lots/new" element={<LotEditPage />} />
            <Route path="/lots/:id" element={<LotEditPage />} />
            <Route path="/sessions" element={<SessionsPage />} />
            <Route path="/sessions/:id" element={<SessionDetailsPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/qr-codes" element={<QRCodeGeneratorPage />} />
            <Route path="/users" element={<UsersPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Route>
        </Route>

        <Route path="/" element={<Navigate to="/dashboard" />} />
      </Routes>
    </BrowserRouter>
  );
};

const ProtectedRoute = () => {
  const { isAuthenticated } = useAuthStore();
  return isAuthenticated ? <Outlet /> : <Navigate to="/login" />;
};
```

---

## Development Checklist

- [ ] Project setup with Vite + React + TypeScript
- [ ] Install dependencies (MUI, Axios, etc.)
- [ ] Configure routing with React Router
- [ ] Set up state management (Zustand)
- [ ] Create API client with interceptors
- [ ] Implement authentication flow
- [ ] Protected route wrapper
- [ ] App layout (sidebar, header)
- [ ] Login page
- [ ] Dashboard page with metrics
- [ ] Parking lots CRUD
- [ ] Sessions management
- [ ] Analytics and charts
- [ ] QR code generator
- [ ] User management (admin only)
- [ ] Settings page
- [ ] Error handling and toasts
- [ ] Loading states
- [ ] Form validation
- [ ] Responsive design
- [ ] Build and deployment

---

## Project Structure

```
admin/
├── src/
│   ├── pages/
│   │   ├── LoginPage.tsx
│   │   ├── DashboardPage.tsx
│   │   ├── ParkingLotsPage.tsx
│   │   ├── LotEditPage.tsx
│   │   ├── SessionsPage.tsx
│   │   ├── AnalyticsPage.tsx
│   │   ├── QRCodeGeneratorPage.tsx
│   │   ├── UsersPage.tsx
│   │   └── SettingsPage.tsx
│   ├── components/
│   │   ├── layout/
│   │   │   ├── AppLayout.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── UserMenu.tsx
│   │   ├── common/
│   │   │   ├── DataTable.tsx
│   │   │   ├── MetricCard.tsx
│   │   │   └── LoadingSpinner.tsx
│   │   ├── lots/
│   │   │   ├── LotForm.tsx
│   │   │   └── SpaceList.tsx
│   │   ├── sessions/
│   │   │   └── SessionFilters.tsx
│   │   └── charts/
│   │       ├── RevenueTrendChart.tsx
│   │       └── OccupancyChart.tsx
│   ├── services/
│   │   ├── api.ts
│   │   └── auth.ts
│   ├── stores/
│   │   ├── authStore.ts
│   │   ├── lotsStore.ts
│   │   └── sessionsStore.ts
│   ├── types/
│   │   └── index.ts
│   ├── utils/
│   │   ├── time.ts
│   │   └── validation.ts
│   ├── App.tsx
│   └── main.tsx
├── index.html
├── vite.config.ts
├── tsconfig.json
└── package.json
```

---

## Getting Started

```bash
# Create new Vite project
npm create vite@latest trufan-admin -- --template react-ts

# Install dependencies
cd trufan-admin
npm install @mui/material @emotion/react @emotion/styled
npm install react-router-dom zustand axios
npm install react-hook-form yup @hookform/resolvers
npm install @tanstack/react-table recharts
npm install date-fns react-toastify qrcode.react

# Start development
npm run dev
```

---

This prompt provides everything needed to build a fully functional admin panel for TruFan Parking. Follow the pages, features, and implementation examples to create a professional, feature-rich management interface.

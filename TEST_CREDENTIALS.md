# TruFan Backend - Test Credentials

**🎉 Backend successfully deployed and ready for testing!**

---

## 🌐 Production API

**Base URL:**
```
https://trufan-admin-production.up.railway.app/api/v1
```

**Health Check:**
```
https://trufan-admin-production.up.railway.app/health
```

**API Docs:**
```
https://trufan-admin-production.up.railway.app/docs
```

---

## 🔐 Test Accounts

### Super Admin (Admin Panel)

```
Email: admin@trufan.com
Password: TruFan2025!Admin
Role: super_admin
```

**Access:**
- Full system access
- Can manage all venues
- Can create/manage users
- Can access all admin endpoints

**Use for:**
- Admin panel testing
- Creating venues, lots, stores
- Managing inventory and orders
- User management

---

### Test User (Mobile App)

```
Email: testuser@trufan.com
Password: TestUser2025!
Role: customer
```

**Access:**
- Mobile app features
- Parking sessions
- Valet requests
- Convenience store orders
- Partner opportunities

**Use for:**
- iOS app testing
- Customer-facing features
- End-to-end flow testing

---

## ✅ Verified Working

- ✅ User registration
- ✅ User login (both accounts tested)
- ✅ JWT token generation
- ✅ Role-based access control
- ✅ Database migrations completed
- ✅ Health endpoint responding
- ✅ API documentation accessible

---

## 📱 Integration Instructions

### For Mobile Team

1. Update base URL in iOS app:
   ```swift
   let baseURL = "https://trufan-admin-production.up.railway.app/api/v1"
   ```

2. Test login with:
   - Email: `testuser@trufan.com`
   - Password: `TestUser2025!`

3. Follow integration guide: `MOBILE_APP_INTEGRATION.md`

---

### For Admin Panel Team

1. Update `.env` file:
   ```bash
   VITE_API_BASE_URL=https://trufan-admin-production.up.railway.app/api/v1
   ```

2. Test login with:
   - Email: `admin@trufan.com`
   - Password: `TruFan2025!Admin`

3. Follow integration guide: `ADMIN_PANEL_INTEGRATION.md`

---

## 🧪 Testing Checklist

### Authentication Flow
- [x] Register new user
- [x] Login with credentials
- [x] Receive JWT tokens
- [ ] Refresh token flow
- [ ] Logout

### Admin Panel
- [ ] Login as super admin
- [ ] View dashboard
- [ ] Create venue
- [ ] Manage inventory
- [ ] Process orders

### Mobile App
- [ ] Login as customer
- [ ] Register new account
- [ ] Start parking session
- [ ] Request valet service
- [ ] Browse convenience store
- [ ] Place order

---

## 🔒 Security Notes

- All passwords use bcrypt hashing
- JWT tokens expire after 30 minutes (access) / 7 days (refresh)
- Rate limiting: 60 requests/minute per IP
- HTTPS enforced by Railway
- CORS configured for Railway domain + localhost

---

## 💡 Quick Test Commands

**Test health:**
```bash
curl https://trufan-admin-production.up.railway.app/health
```

**Test login (admin):**
```bash
curl -X POST https://trufan-admin-production.up.railway.app/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@trufan.com","password":"TruFan2025!Admin"}'
```

**Test login (customer):**
```bash
curl -X POST https://trufan-admin-production.up.railway.app/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"testuser@trufan.com","password":"TestUser2025!"}'
```

---

## 📞 Support

**Issues or Questions:**
- Check Railway logs for backend errors
- Include `correlationId` from error responses
- Review integration guides for troubleshooting

**Documentation:**
- `MOBILE_APP_INTEGRATION.md` - Mobile team guide
- `ADMIN_PANEL_INTEGRATION.md` - Admin panel guide
- `DEPLOYMENT_SUMMARY.md` - Infrastructure details

---

## 🎯 Next Steps

1. ✅ Backend deployed
2. ✅ Test users created
3. ✅ Authentication verified
4. **→ Mobile team: Integrate iOS app**
5. **→ Admin team: Update Vue.js config**
6. **→ Test all features end-to-end**
7. **→ Distribute to internal testers**

---

**Status:** ✅ READY FOR TESTING

**Deployment Date:** November 21, 2025

**Platform:** Railway (PostgreSQL + Redis)

# LUCOST AI Backend

Complete FastAPI backend for AI-powered short-form video generation platform.

## Features

- ✅ User authentication (Firebase)
- ✅ Admin/Manager authentication (Supabase)
- ✅ Job queue system (Redis)
- ✅ GPU management (RunPod)
- ✅ Video generation pipeline
- ✅ Payment processing (Lemon Squeezy, Stripe, Paystack, Flutterwave, FastSpring)
- ✅ File storage (S3 or Cloudflare R2)
- ✅ Push notifications (Firebase Cloud Messaging)
- ✅ Fraud detection & whitelist system
- ✅ Admin dashboard API

## Setup Instructions

### 1. Prerequisites

- Python 3.9+
- PostgreSQL 12+
- Redis 6+
- Git

### 2. Local Development Setup

```bash
# Clone repository
git clone https://github.com/yourusername/lucost-ai-backend.git
cd lucost-ai-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Fill in .env with your API keys (see Configuration section below)
nano .env

# Run migrations (if using Alembic)
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

Server runs at `http://localhost:8000`
API docs at `http://localhost:8000/docs`

### 3. Configuration

Create `.env` file with these values:

**Database:**
- `DATABASE_URL`: PostgreSQL connection string (from Render/Railway)
- `REDIS_URL`: Redis connection string (from Render/Railway)

**Authentication:**
- `SUPABASE_URL`: From Supabase project settings
- `SUPABASE_KEY`: From Supabase project settings
- `FIREBASE_PROJECT_ID`, `FIREBASE_PRIVATE_KEY`, `FIREBASE_CLIENT_EMAIL`: From Firebase service account

**Payment Processors:**
- `LEMON_SQUEEZY_API_KEY`: From Lemon Squeezy dashboard
- `STRIPE_SECRET_KEY`: From Stripe dashboard
- `PAYSTACK_SECRET_KEY`: From Paystack dashboard
- `FLUTTERWAVE_SECRET_KEY`: From Flutterwave dashboard
- `FASTSPRING_API_KEY`: From FastSpring dashboard

**GPU Rendering:**
- `RUNPOD_API_KEY`: From RunPod account settings
- `RUNPOD_ENDPOINT_ID`: Your ComfyUI endpoint ID on RunPod

**Storage (choose one):**
- S3: `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_BUCKET`
- R2: `R2_ACCESS_KEY`, `R2_SECRET_KEY`, `R2_BUCKET`, `R2_ACCOUNT_ID`
- Set `STORAGE_PROVIDER=r2` or `s3`

### 4. Database Setup

If using Render or Railway PostgreSQL:

1. Create database from hosting provider dashboard
2. Copy connection string to `.env` as `DATABASE_URL`
3. Run migrations:
   ```bash
   alembic upgrade head
   ```

### 5. Deployment to Render

1. Push code to GitHub
2. Create new Render service
3. Connect GitHub repository
4. Add PostgreSQL add-on
5. Add Redis add-on
6. In Environment section, add all `.env` variables
7. Deploy

## API Endpoints

### User Endpoints
- `POST /api/auth/signup` - User registration
- `POST /api/auth/login` - User login
- `POST /api/generate` - Submit video generation job
- `GET /api/gallery` - Get user's video jobs
- `GET /api/gallery/{job_id}` - Get specific video

### Admin Endpoints (requires Supabase auth)
- `GET /api/admin/overview` - Dashboard overview
- `GET /api/admin/revenue` - Revenue analytics
- `GET /api/admin/fraud-logs` - Fraud detection logs
- `PUT /api/admin/settings/gpu` - Update GPU allocation
- `GET /api/admin/settings/api-keys` - View API key status
- `PUT /api/admin/settings/api-keys/{service}` - Update API key
- `PUT /api/admin/settings/pricing` - Update tier pricing
- `POST /api/admin/whitelist` - Add whitelisted email
- `DELETE /api/admin/whitelist/{email}` - Remove whitelisted email
- `POST /api/admin/manager` - Create manager account
- `DELETE /api/admin/manager` - Delete manager account

### Webhook Endpoints
- `POST /api/webhooks/lemon-squeezy` - Lemon Squeezy payment webhook
- `POST /api/webhooks/stripe` - Stripe payment webhook
- `POST /api/webhooks/paystack` - Paystack payment webhook
- `POST /api/webhooks/flutterwave` - Flutterwave payment webhook

## Project Structure

```
app/
├── main.py                 # FastAPI app initialization
├── config.py              # Configuration & environment
├── models.py              # Database models (SQLAlchemy)
├── database.py            # Database connection & setup
├── routers/
│   ├── auth.py           # User & admin authentication
│   ├── generate.py       # Video generation endpoints
│   ├── gallery.py        # Gallery/jobs endpoints
│   ├── admin.py          # Admin dashboard endpoints
│   └── webhooks.py       # Payment webhook handlers
├── services/
│   ├── script_parser.py  # Script parsing logic
│   ├── queue_manager.py  # Job queue management
│   ├── gpu_manager.py    # GPU allocation logic
│   ├── storage_manager.py# File storage handling
│   └── payment_handler.py# Payment processing
└── utils/
    ├── encryption.py     # API key encryption
    └── validators.py     # Input validation

static/
├── landing.html          # Landing page
├── dashboard.html        # Main dashboard
└── admin.html           # Admin dashboard
```

## Database Schema

### Users
- `id`, `email`, `subscription_tier`, `trials_remaining`, `created_at`, `updated_at`

### Subscriptions
- `id`, `user_id`, `tier`, `gens_used`, `gens_allowed`, `renews_at`

### Jobs
- `id`, `user_id`, `status`, `script`, `style`, `video_url`, `created_at`, `completed_at`

### API Settings
- `id`, `service`, `key_encrypted`, `is_enabled`, `updated_at`

### GPU Settings
- `tier`, `gpu_count`, `updated_at`

### Pricing Tiers
- `tier`, `price_usd`, `strike_price_usd`, `gens_per_month`, `max_duration_sec`

### Whitelist
- `id`, `email`, `created_at`

### Fraud Logs
- `id`, `email`, `attempt_type`, `details`, `created_at`

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app
```

## Troubleshooting

### CORS Errors
- Check `FRONTEND_URL` in `.env` matches your frontend origin
- Update `CORSMiddleware` in `main.py` if needed

### Database Connection Issues
- Verify `DATABASE_URL` format: `postgresql://user:password@host:port/dbname`
- Ensure PostgreSQL server is running
- Check firewall/network access

### Payment Webhook Issues
- Verify webhook URLs in payment provider dashboards
- Check webhook secrets match in `.env`
- Look at webhook logs in provider dashboards

## Security

- All API keys are encrypted in database
- Passwords hashed with bcrypt
- CORS enabled only for trusted origins
- JWT tokens expire after 24 hours
- Rate limiting recommended for production

## Production Checklist

- [ ] Set `ENV=production` in `.env`
- [ ] Set `DEBUG=false`
- [ ] Use strong JWT_SECRET
- [ ] Generate new ENCRYPTION_KEY
- [ ] All API keys in Render environment variables
- [ ] Enable HTTPS
- [ ] Set up database backups
- [ ] Set up monitoring/logging
- [ ] Configure rate limiting
- [ ] Set up error tracking (Sentry)

## Support

For issues, check the logs:
```bash
# Render logs
render logs

# Or locally
tail -f logs/app.log
```

## License

Proprietary - LUCOST AI

# SEAN PICKS - Deployment Guide

## Quick Deployment Options

### Option 1: Vercel (Frontend) + Railway/Render (Backend) - RECOMMENDED
**Cost: ~$5-20/month**
**Time: 30 minutes**

### Option 2: Netlify (Frontend) + Heroku (Backend)
**Cost: Free tier available**
**Time: 45 minutes**

### Option 3: AWS/DigitalOcean VPS
**Cost: $5-10/month**
**Time: 2 hours**

---

## STEP-BY-STEP DEPLOYMENT (Option 1 - Recommended)

### 1. Prepare Environment Variables

Create `.env.production` files:

**Backend (.env.production):**
```
# API Keys (KEEP THESE SECRET!)
ODDS_API_KEY=d4fa91883b15fd5a5594c64e58b884ef
WEATHER_API_KEY=85203d1084a3bc89e21a0409e5b9418b

# JWT Secret (CHANGE THIS!)
JWT_SECRET=your-production-secret-key-change-this-12345

# Database
DATABASE_URL=sqlite:///./sean_picks.db

# CORS (update after deploying frontend)
FRONTEND_URL=https://your-frontend-url.vercel.app
```

**Frontend (.env.production):**
```
REACT_APP_API_URL=https://your-backend-url.railway.app
```

### 2. Deploy Backend to Railway

1. **Sign up at Railway.app** (https://railway.app)

2. **Install Railway CLI:**
```bash
npm install -g @railway/cli
```

3. **Prepare backend for deployment:**
```bash
cd backend

# Create requirements.txt if not exists
pip freeze > requirements.txt

# Create Procfile
echo "web: uvicorn app.main:app --host 0.0.0.0 --port \$PORT" > Procfile

# Create railway.json
cat > railway.json << 'EOF'
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
EOF
```

4. **Deploy to Railway:**
```bash
railway login
railway init
railway up
railway domain  # Get your backend URL
```

5. **Set environment variables in Railway dashboard:**
- Go to your project settings
- Add all environment variables from .env.production
- Update FRONTEND_URL once you have it

### 3. Deploy Frontend to Vercel

1. **Sign up at Vercel** (https://vercel.com)

2. **Install Vercel CLI:**
```bash
npm install -g vercel
```

3. **Update frontend for production:**
```bash
cd frontend

# Update API URL in code
cat > .env.production << 'EOF'
REACT_APP_API_URL=https://your-backend-railway-url.railway.app
EOF

# Build for production
npm run build
```

4. **Deploy to Vercel:**
```bash
vercel

# Follow prompts:
# - Link to existing project? No
# - What's your project name? sean-picks
# - Which directory? ./
# - Override settings? No
```

5. **Set environment variables in Vercel:**
- Go to project settings
- Add REACT_APP_API_URL with your Railway backend URL

### 4. Update CORS Settings

**Update backend/app/main.py:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://sean-picks.vercel.app",  # Your Vercel URL
        "http://localhost:3000"  # Keep for local dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Redeploy backend:**
```bash
cd backend
railway up
```

### 5. Configure Custom Domain (Optional)

**For Frontend (Vercel):**
1. Go to Vercel project settings
2. Add your domain (e.g., seanpicks.com)
3. Update DNS records as instructed

**For Backend (Railway):**
1. Go to Railway project settings
2. Add custom domain (e.g., api.seanpicks.com)
3. Update DNS records

---

## PRODUCTION CHECKLIST

### Security:
- [ ] Change JWT_SECRET to strong random key
- [ ] Remove all console.log statements
- [ ] Enable HTTPS (automatic with Vercel/Railway)
- [ ] Restrict CORS to your domain only
- [ ] Move API keys to environment variables
- [ ] Enable rate limiting

### Database:
- [ ] Backup SQLite database regularly
- [ ] Consider PostgreSQL for production:
  ```bash
  # Railway provides PostgreSQL
  railway add postgresql
  # Update DATABASE_URL in environment
  ```

### Performance:
- [ ] Enable caching for API responses
- [ ] Minimize bundle size
- [ ] Enable gzip compression
- [ ] Use CDN for static assets

### Monitoring:
- [ ] Set up error tracking (Sentry)
- [ ] Add uptime monitoring (UptimeRobot)
- [ ] Enable Railway metrics
- [ ] Set up log aggregation

---

## ALTERNATIVE DEPLOYMENTS

### Option 2: Netlify + Heroku

**Frontend to Netlify:**
```bash
cd frontend
npm run build
npx netlify-cli deploy --prod --dir=build
```

**Backend to Heroku:**
```bash
cd backend
heroku create sean-picks-api
git push heroku main
heroku config:set ODDS_API_KEY=your-key
```

### Option 3: Single VPS (DigitalOcean/AWS)

**Setup Ubuntu server:**
```bash
# SSH into server
ssh root@your-server-ip

# Install dependencies
apt update && apt upgrade -y
apt install python3-pip nginx nodejs npm certbot -y

# Clone repo
git clone https://github.com/yourusername/sean-picks.git
cd sean-picks

# Setup backend
cd backend
pip3 install -r requirements.txt
pip3 install gunicorn

# Create systemd service
cat > /etc/systemd/system/seanpicks.service << 'EOF'
[Unit]
Description=Sean Picks API
After=network.target

[Service]
User=www-data
WorkingDirectory=/root/sean-picks/backend
ExecStart=/usr/local/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8001
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl enable seanpicks
systemctl start seanpicks

# Setup frontend
cd ../frontend
npm install
npm run build

# Configure nginx
cat > /etc/nginx/sites-available/seanpicks << 'EOF'
server {
    listen 80;
    server_name seanpicks.com;
    
    location / {
        root /root/sean-picks/frontend/build;
        try_files $uri /index.html;
    }
    
    location /api {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
EOF

ln -s /etc/nginx/sites-available/seanpicks /etc/nginx/sites-enabled/
nginx -t && systemctl restart nginx

# Setup SSL
certbot --nginx -d seanpicks.com
```

---

## POST-DEPLOYMENT

1. **Test everything:**
   - Login/logout
   - View NFL games
   - View NCAAF games
   - Check Best Bets
   - Verify weather data loads
   - Confirm odds update

2. **Monitor logs:**
   ```bash
   # Railway
   railway logs
   
   # Vercel
   vercel logs
   ```

3. **Set up backups:**
   - Daily database backups
   - Code repository backups
   - Environment variable backups

4. **Performance optimization:**
   - Enable CloudFlare CDN
   - Implement Redis caching
   - Use image optimization

---

## COSTS BREAKDOWN

### Minimal Setup:
- Vercel (Frontend): FREE
- Railway (Backend): $5/month
- Domain: $12/year
**Total: ~$6/month**

### Professional Setup:
- Vercel Pro: $20/month
- Railway Pro: $10/month  
- PostgreSQL: $5/month
- Monitoring: $10/month
- Domain + SSL: $15/year
**Total: ~$46/month**

---

## TROUBLESHOOTING

### CORS Errors:
- Ensure backend allows your frontend URL
- Check both http/https protocols
- Verify credentials are included

### API Connection Failed:
- Check environment variables
- Verify backend is running
- Check network/firewall rules

### Database Issues:
- Ensure migrations are run
- Check file permissions for SQLite
- Verify connection string

### Build Failures:
- Check Node/Python versions
- Clear cache and rebuild
- Review dependency conflicts

---

## SUPPORT

For deployment help:
- Railway: https://docs.railway.app
- Vercel: https://vercel.com/docs
- Stack Overflow: Tag with [fastapi] [react] [deployment]

Good luck with your deployment! 🚀
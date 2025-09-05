# Setting up PostgreSQL on Railway

1. Go to your Railway project dashboard
2. Click "New" → "Database" → "PostgreSQL"
3. Railway will create a PostgreSQL database
4. Click on the PostgreSQL service
5. Go to the "Variables" tab
6. Copy the DATABASE_URL

7. In your backend service:
   - Go to Variables
   - Add: DATABASE_URL = (paste the PostgreSQL URL)

8. Your app will automatically use PostgreSQL instead of SQLite

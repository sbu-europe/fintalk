# Deployment Checklist for OpenAI-Compatible Streaming API

## Pre-Deployment Checklist

### 1. Local Testing

- [ ] Start the API: `docker-compose up -d`
- [ ] Run health check: `curl http://localhost:8000/api/health/`
- [ ] Run test suite: `./test_openai_endpoint.sh`
- [ ] Test streaming manually:
  ```bash
  curl -X POST http://localhost:8000/api/chat/completions/ \
    -H "Content-Type: application/json" \
    -d '{"messages": [{"role": "user", "content": "Hello"}], "stream": true}'
  ```
- [ ] Test non-streaming manually:
  ```bash
  curl -X POST http://localhost:8000/api/chat/completions/ \
    -H "Content-Type: application/json" \
    -d '{"messages": [{"role": "user", "content": "Hello"}], "stream": false}'
  ```
- [ ] Upload a test document: `POST /api/documents/upload/`
- [ ] Test document search query
- [ ] Test credit card blocking with phone number

### 2. Environment Configuration

- [ ] Set `DEBUG=False` in production `.env`
- [ ] Generate strong `SECRET_KEY`
- [ ] Configure AWS credentials (preferably use IAM roles)
- [ ] Set `ALLOWED_HOSTS` to your domain
- [ ] Configure `CORS_ALLOWED_ORIGINS`
- [ ] Set appropriate `LOG_LEVEL` (INFO or WARNING)
- [ ] Verify database credentials
- [ ] Verify OpenSearch credentials

### 3. Security

- [ ] Enable HTTPS/SSL
- [ ] Configure firewall rules
- [ ] Set up API authentication (if needed)
- [ ] Enable rate limiting
- [ ] Review CORS settings
- [ ] Secure environment variables
- [ ] Set up secrets management
- [ ] Enable security headers

### 4. Infrastructure

- [ ] Provision production server
- [ ] Install Docker and Docker Compose
- [ ] Configure reverse proxy (Nginx/Caddy)
- [ ] Set up SSL certificates (Let's Encrypt)
- [ ] Configure domain DNS
- [ ] Set up monitoring
- [ ] Configure log aggregation
- [ ] Set up backup strategy

## Deployment Steps

### Step 1: Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose -y

# Create app directory
mkdir -p /opt/fintalk
cd /opt/fintalk
```

### Step 2: Deploy Application

```bash
# Clone repository
git clone <your-repo-url> .

# Copy and configure environment
cp .env.example .env
nano .env  # Edit with production values

# Build and start services
docker-compose up -d --build

# Run migrations
docker-compose exec django python manage.py migrate

# Collect static files
docker-compose exec django python manage.py collectstatic --noinput
```

### Step 3: Configure Nginx

Create `/etc/nginx/sites-available/fintalk`:

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # Proxy settings
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # SSE/Streaming support
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 300s;
    }
    
    # Static files
    location /static/ {
        alias /opt/fintalk/staticfiles/;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/fintalk /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Step 4: SSL Certificate

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get certificate
sudo certbot --nginx -d api.yourdomain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

### Step 5: Verify Deployment

```bash
# Check services
docker-compose ps

# Check logs
docker-compose logs -f django

# Test health endpoint
curl https://api.yourdomain.com/api/health/

# Test chat completions
curl -X POST https://api.yourdomain.com/api/chat/completions/ \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello"}], "stream": false}'
```

## Vapi.ai Configuration

### Step 1: Access Vapi.ai Dashboard

1. Log in to https://dashboard.vapi.ai
2. Navigate to **Custom LLM** section

### Step 2: Add Custom LLM Provider

```json
{
  "name": "Fintalk Banking Assistant",
  "provider": "custom-llm",
  "url": "https://api.yourdomain.com/api/chat/completions/",
  "method": "POST",
  "headers": {
    "Content-Type": "application/json"
  }
}
```

### Step 3: Create Assistant

```json
{
  "name": "Fintalk Banking Assistant",
  "model": {
    "provider": "custom-llm",
    "url": "https://api.yourdomain.com/api/chat/completions/",
    "model": "amazon.nova-lite-v1:0",
    "temperature": 0.7
  },
  "voice": {
    "provider": "11labs",
    "voiceId": "professional-female",
    "stability": 0.5,
    "similarityBoost": 0.75
  },
  "firstMessage": "Hello! Thank you for calling FinTalk. I'm your banking assistant. How can I help you today?",
  "systemPrompt": "You are a professional banking call center agent for FinTalk. You assist customers with loan inquiries and credit card services. Always be polite, professional, and helpful. For credit card operations, always ask for the customer's phone number. Speak naturally and conversationally.",
  "endCallMessage": "Thank you for calling FinTalk. Have a great day!",
  "endCallPhrases": ["goodbye", "bye", "that's all", "thank you"],
  "recordingEnabled": true,
  "maxDurationSeconds": 600,
  "silenceTimeoutSeconds": 30,
  "responseDelaySeconds": 1,
  "interruptionsEnabled": true
}
```

### Step 4: Test Integration

1. Use Vapi.ai's test interface
2. Make a test call
3. Verify streaming works
4. Check response quality
5. Test credit card operations

## Monitoring Setup

### Application Monitoring

```bash
# View logs
docker-compose logs -f django

# Monitor resource usage
docker stats

# Check disk space
df -h
```

### Set Up Log Rotation

Create `/etc/logrotate.d/fintalk`:

```
/opt/fintalk/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 root root
    sharedscripts
    postrotate
        docker-compose -f /opt/fintalk/docker-compose.yml restart django
    endscript
}
```

### Set Up Monitoring Alerts

Consider using:
- **Uptime monitoring**: UptimeRobot, Pingdom
- **Error tracking**: Sentry
- **Performance monitoring**: New Relic, DataDog
- **Log aggregation**: ELK Stack, Papertrail

## Post-Deployment Checklist

### Immediate Verification

- [ ] API is accessible via HTTPS
- [ ] Health check returns 200 OK
- [ ] Chat completions endpoint works (streaming)
- [ ] Chat completions endpoint works (non-streaming)
- [ ] Document upload works
- [ ] Agent queries work
- [ ] Credit card operations work
- [ ] Vapi.ai integration works
- [ ] SSL certificate is valid
- [ ] Logs are being written

### Performance Testing

- [ ] Test response times (< 2s for first token)
- [ ] Test concurrent requests (10+ simultaneous)
- [ ] Test large documents upload
- [ ] Test long conversations
- [ ] Monitor memory usage
- [ ] Monitor CPU usage
- [ ] Check database performance
- [ ] Check OpenSearch performance

### Security Verification

- [ ] HTTPS enforced
- [ ] No sensitive data in logs
- [ ] CORS configured correctly
- [ ] Rate limiting working
- [ ] Firewall rules active
- [ ] No debug mode enabled
- [ ] Environment variables secured

## Maintenance

### Daily

- [ ] Check error logs
- [ ] Monitor response times
- [ ] Check disk space
- [ ] Verify backups

### Weekly

- [ ] Review performance metrics
- [ ] Check for security updates
- [ ] Review error patterns
- [ ] Test backup restoration

### Monthly

- [ ] Update dependencies
- [ ] Review AWS costs
- [ ] Optimize database
- [ ] Review and rotate logs
- [ ] Security audit

## Rollback Plan

If deployment fails:

```bash
# Stop services
docker-compose down

# Restore previous version
git checkout <previous-commit>

# Rebuild and restart
docker-compose up -d --build

# Verify
curl https://api.yourdomain.com/api/health/
```

## Troubleshooting

### API Not Responding

```bash
# Check if containers are running
docker-compose ps

# Check logs
docker-compose logs django

# Restart services
docker-compose restart
```

### Streaming Not Working

1. Check Nginx configuration for proxy_buffering
2. Verify X-Accel-Buffering header
3. Check client SSE support
4. Review application logs

### High Latency

1. Check AWS Bedrock region
2. Monitor OpenSearch performance
3. Review database queries
4. Check network latency
5. Consider caching

### Database Issues

```bash
# Check PostgreSQL
docker-compose exec postgres psql -U fintalk_user -d fintalk

# Run migrations
docker-compose exec django python manage.py migrate

# Check connections
docker-compose exec postgres psql -U fintalk_user -d fintalk -c "SELECT count(*) FROM pg_stat_activity;"
```

## Support Contacts

- **Infrastructure**: [Your DevOps team]
- **Application**: [Your dev team]
- **AWS Support**: [AWS account]
- **Vapi.ai Support**: support@vapi.ai

## Documentation Links

- Main README: `README.md`
- Vapi.ai Integration: `VAPI_INTEGRATION.md`
- Streaming API: `STREAMING_API_SUMMARY.md`
- Quick Reference: `QUICK_REFERENCE.md`

## Success Criteria

✅ API responds within 2 seconds
✅ Streaming works smoothly
✅ 99.9% uptime
✅ No critical errors in logs
✅ Vapi.ai integration functional
✅ All tests passing
✅ Security measures active
✅ Monitoring in place

---

**Deployment Date**: _____________
**Deployed By**: _____________
**Version**: _____________
**Status**: ⬜ Success ⬜ Failed ⬜ Rolled Back

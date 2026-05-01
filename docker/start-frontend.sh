#!/bin/sh
# Frontend startup script with URL logging

echo ""
echo "=========================================="
echo "🚀 EduRisk AI Frontend Starting..."
echo "=========================================="
echo ""
echo "📍 Frontend URL: http://localhost:3000"
echo "📍 API Backend:  http://localhost:8000"
echo "📚 API Docs:     http://localhost:8000/docs"
echo ""
echo "=========================================="
echo "✅ Server is ready!"
echo "=========================================="
echo ""

# Start the Next.js server
exec node server.js

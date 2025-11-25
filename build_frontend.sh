#!/bin/bash
set -e

echo "🔨 Building Fanshawe Navigator Frontend..."

cd Fanshawe_Navigator-main/frontend

# Instalar dependências
echo "📦 Installing dependencies..."
npm install

# Corrigir permissões dos binários do node_modules
chmod +x node_modules/.bin/* 2>/dev/null || true

# Copiar imagens para pasta public (Vite copia automaticamente para dist)
echo "🖼️  Preparing images..."
mkdir -p public/Fanshawe_Icons
cp -r Fanshawe_Icons/* public/Fanshawe_Icons/

# Build para produção
echo "🏗️  Building React app..."
npm run build

cd ../..

echo "✅ Frontend build complete!"
echo "📂 Build output: Fanshawe_Navigator-main/frontend/dist/"
echo "▶️  Start backend with: python src/api/app.py"

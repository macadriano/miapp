#!/bin/bash
# Script para analizar el servidor (ejecutar DENTRO del servidor)
# ⚠️ SOLO LECTURA - NO MODIFICA NADA

echo "🔍 Análisis del Servidor - SOLO LECTURA"
echo "========================================"
echo ""

REMOTE_PATH="/root/django-docker-project"
OUTPUT_FILE="/tmp/analisis_servidor.txt"

echo "# 🔍 ANÁLISIS DEL SERVIDOR - RESULTADO" > $OUTPUT_FILE
echo "" >> $OUTPUT_FILE
echo "**Fecha:** $(date)" >> $OUTPUT_FILE
echo "**Ruta:** $REMOTE_PATH" >> $OUTPUT_FILE
echo "**Modo:** SOLO LECTURA" >> $OUTPUT_FILE
echo "" >> $OUTPUT_FILE
echo "---" >> $OUTPUT_FILE
echo "" >> $OUTPUT_FILE

echo "📂 Analizando estructura..."
echo "### Estructura General" >> $OUTPUT_FILE
echo "\`\`\`" >> $OUTPUT_FILE
ls -la $REMOTE_PATH >> $OUTPUT_FILE 2>&1
echo "\`\`\`" >> $OUTPUT_FILE
echo "" >> $OUTPUT_FILE

# FRONTEND
FRONTEND_PATH="$REMOTE_PATH/frontend"
if [ -d "$FRONTEND_PATH" ]; then
    echo "⚛️  Analizando Frontend..."
    echo "## ⚛️  FRONTEND" >> $OUTPUT_FILE
    echo "" >> $OUTPUT_FILE
    
    if [ -f "$FRONTEND_PATH/package.json" ]; then
        echo "📦 package.json" >> $OUTPUT_FILE
        echo "\`\`\`json" >> $OUTPUT_FILE
        cat "$FRONTEND_PATH/package.json" >> $OUTPUT_FILE
        echo "\`\`\`" >> $OUTPUT_FILE
        echo "" >> $OUTPUT_FILE
    fi
    
    if [ -f "$FRONTEND_PATH/vite.config.js" ]; then
        echo "⚡ vite.config.js" >> $OUTPUT_FILE
        echo "\`\`\`javascript" >> $OUTPUT_FILE
        cat "$FRONTEND_PATH/vite.config.js" >> $OUTPUT_FILE
        echo "\`\`\`" >> $OUTPUT_FILE
        echo "" >> $OUTPUT_FILE
    fi
    
    if [ -d "$FRONTEND_PATH/src/pages" ]; then
        echo "📄 Componentes Pages:" >> $OUTPUT_FILE
        echo "\`\`\`" >> $OUTPUT_FILE
        ls -1 "$FRONTEND_PATH/src/pages"/*.jsx "$FRONTEND_PATH/src/pages"/*.tsx 2>/dev/null >> $OUTPUT_FILE
        echo "\`\`\`" >> $OUTPUT_FILE
        echo "" >> $OUTPUT_FILE
    fi
    
    if [ -f "$FRONTEND_PATH/src/config.js" ]; then
        echo "⚙️  config.js" >> $OUTPUT_FILE
        echo "\`\`\`javascript" >> $OUTPUT_FILE
        cat "$FRONTEND_PATH/src/config.js" >> $OUTPUT_FILE
        echo "\`\`\`" >> $OUTPUT_FILE
        echo "" >> $OUTPUT_FILE
    fi
    
    if [ -f "$FRONTEND_PATH/src/App.jsx" ]; then
        echo "🛣️  App.jsx (primeras 100 líneas)" >> $OUTPUT_FILE
        echo "\`\`\`javascript" >> $OUTPUT_FILE
        head -100 "$FRONTEND_PATH/src/App.jsx" >> $OUTPUT_FILE
        echo "\`\`\`" >> $OUTPUT_FILE
        echo "" >> $OUTPUT_FILE
    fi
fi

# BACKEND
BACKEND_PATH="$REMOTE_PATH/app"
if [ -d "$BACKEND_PATH" ]; then
    echo "🐍 Analizando Backend..."
    echo "## 🐍 BACKEND" >> $OUTPUT_FILE
    echo "" >> $OUTPUT_FILE
    
    if [ -f "$BACKEND_PATH/requirements.txt" ]; then
        echo "📦 requirements.txt" >> $OUTPUT_FILE
        echo "\`\`\`" >> $OUTPUT_FILE
        cat "$BACKEND_PATH/requirements.txt" >> $OUTPUT_FILE
        echo "\`\`\`" >> $OUTPUT_FILE
        echo "" >> $OUTPUT_FILE
    fi
    
    echo "📱 Apps Django:" >> $OUTPUT_FILE
    echo "\`\`\`" >> $OUTPUT_FILE
    ls -d "$BACKEND_PATH"/*/ 2>/dev/null | xargs -I {} basename {} >> $OUTPUT_FILE
    echo "\`\`\`" >> $OUTPUT_FILE
    echo "" >> $OUTPUT_FILE
    
    # Analizar cada app
    for app_dir in "$BACKEND_PATH"/*/; do
        if [ -d "$app_dir" ]; then
            app_name=$(basename "$app_dir")
            if [[ ! "$app_name" =~ ^(__pycache__|migrations|\.git) ]]; then
                echo "#### $app_name" >> $OUTPUT_FILE
                echo "" >> $OUTPUT_FILE
                
                if [ -f "$app_dir/models.py" ]; then
                    echo "**models.py (primeras 50 líneas):**" >> $OUTPUT_FILE
                    echo "\`\`\`python" >> $OUTPUT_FILE
                    head -50 "$app_dir/models.py" >> $OUTPUT_FILE
                    echo "\`\`\`" >> $OUTPUT_FILE
                    echo "" >> $OUTPUT_FILE
                fi
                
                if [[ "$app_name" =~ (authentication|empresas) ]]; then
                    if [ -f "$app_dir/views.py" ]; then
                        echo "**views.py (primeras 30 líneas):**" >> $OUTPUT_FILE
                        echo "\`\`\`python" >> $OUTPUT_FILE
                        head -30 "$app_dir/views.py" >> $OUTPUT_FILE
                        echo "\`\`\`" >> $OUTPUT_FILE
                        echo "" >> $OUTPUT_FILE
                    fi
                    
                    if [ -f "$app_dir/urls.py" ]; then
                        echo "**urls.py:**" >> $OUTPUT_FILE
                        echo "\`\`\`python" >> $OUTPUT_FILE
                        cat "$app_dir/urls.py" >> $OUTPUT_FILE
                        echo "\`\`\`" >> $OUTPUT_FILE
                        echo "" >> $OUTPUT_FILE
                    fi
                fi
            fi
        fi
    done
    
    # Settings.py
    SETTINGS_FILE=$(find "$BACKEND_PATH" -name "settings.py" -type f | head -1)
    if [ -f "$SETTINGS_FILE" ]; then
        echo "### ⚙️  settings.py" >> $OUTPUT_FILE
        echo "" >> $OUTPUT_FILE
        echo "**Ubicación:** $SETTINGS_FILE" >> $OUTPUT_FILE
        echo "" >> $OUTPUT_FILE
        echo "**INSTALLED_APPS:**" >> $OUTPUT_FILE
        echo "\`\`\`python" >> $OUTPUT_FILE
        grep -A 30 "INSTALLED_APPS" "$SETTINGS_FILE" | head -35 >> $OUTPUT_FILE
        echo "\`\`\`" >> $OUTPUT_FILE
        echo "" >> $OUTPUT_FILE
    fi
    
    # URLs.py principal
    URLS_FILE=$(find "$BACKEND_PATH" -name "urls.py" -type f | grep -E "(project|config|settings)" | head -1 || find "$BACKEND_PATH" -name "urls.py" -type f | head -1)
    if [ -f "$URLS_FILE" ]; then
        echo "### 🛣️  urls.py (principal)" >> $OUTPUT_FILE
        echo "" >> $OUTPUT_FILE
        echo "**Ubicación:** $URLS_FILE" >> $OUTPUT_FILE
        echo "" >> $OUTPUT_FILE
        echo "\`\`\`python" >> $OUTPUT_FILE
        cat "$URLS_FILE" >> $OUTPUT_FILE
        echo "\`\`\`" >> $OUTPUT_FILE
        echo "" >> $OUTPUT_FILE
    fi
fi

echo ""
echo "✅ Análisis completado. Resultado guardado en: $OUTPUT_FILE"
echo ""
echo "Para ver el resultado, ejecuta:"
echo "  cat $OUTPUT_FILE"
echo ""
echo "Para descargarlo, desde tu PC local ejecuta:"
echo "  scp root@vps-5273003-x.dattaweb.com:$OUTPUT_FILE ."

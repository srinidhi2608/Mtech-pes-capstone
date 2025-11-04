#!/usr/bin/env python3
"""
Automated Frontend Setup Script
Creates all necessary folders and files for the dashboard
"""

import os
import sys

def create_folders():
    """Create necessary folder structure"""
    folders = [
        'frontend',
        'frontend/css',
        'frontend/js',
        'frontend/pages'
    ]
    
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        print(f"✓ Created folder: {folder}")

def create_files():
    """Create all necessary files"""
    print("\n📝 Creating files...")
    print("  ℹ Note: You'll need to copy the content from the artifacts I provided")
    
    files = [
        'frontend/index.html',
        'frontend/css/styles.css',
        'frontend/js/api.js',
        'frontend/js/charts.js',
        'frontend/js/app.js',
        'frontend/pages/students.html',
        'frontend/pages/predictions.html',
        'frontend/pages/ctc.html',
        'frontend/pages/analytics.html'
    ]
    
    for file in files:
        if not os.path.exists(file):
            with open(file, 'w') as f:
                f.write(f'<!-- TODO: Copy content for {file} -->\n')
            print(f"✓ Created file: {file}")
        else:
            print(f"⚠ File already exists: {file}")

def update_api_file():
    """Add instructions to update api.py"""
    print("\n" + "="*70)
    print("📝 NEXT STEP: Update your api.py file")
    print("="*70)
    print("\nAdd these lines to your api.py (after creating the FastAPI app):\n")
    
    code = """
# Add these imports at the top
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# After: app = FastAPI(...)
# Add these lines:

# Serve static files
app.mount("/static/css", StaticFiles(directory="frontend/css"), name="css")
app.mount("/static/js", StaticFiles(directory="frontend/js"), name="js")

# Serve main page
@app.get("/", include_in_schema=False)
async def serve_frontend():
    return FileResponse("frontend/index.html")

@app.get("/pages/{page_name}", include_in_schema=False)
async def serve_page(page_name: str):
    return FileResponse(f"frontend/pages/{page_name}")
"""
    
    print(code)
    
    print("\n" + "="*70)

def show_next_steps():
    """Show what to do next"""
    print("\n" + "="*70)
    print("🎯 NEXT STEPS")
    print("="*70)
    
    steps = [
        ("1", "Copy HTML content to frontend/index.html", 
         "From artifact: 'Main Dashboard - index.html'"),
        ("2", "Copy CSS content to frontend/css/styles.css", 
         "From artifact: 'Dashboard Styles - styles.css'"),
        ("3", "Copy JavaScript to frontend/js/api.js", 
         "From artifact: 'API Connection - api.js'"),
        ("4", "Copy JavaScript to frontend/js/charts.js", 
         "From artifact: 'Charts Functions - charts.js'"),
        ("5", "Copy JavaScript to frontend/js/app.js", 
         "From artifact: 'Main Application - app.js'"),
        ("6", "Update api.py with the code shown above", 
         "Add FastAPI static files configuration"),
        ("7", "Start the API server", 
         "python api.py"),
        ("8", "Open browser", 
         "http://localhost:8000"),
    ]
    
    for num, desc, detail in steps:
        print(f"\n{num}. {desc}")
        print(f"   → {detail}")
    
    print("\n" + "="*70)

def main():
    print("\n" + "="*70)
    print("🎨 FRONTEND DASHBOARD SETUP")
    print("="*70)
    print("\nThis script will create the folder structure for your dashboard.\n")
    
    try:
        # Create folders
        print("📁 Creating folder structure...")
        create_folders()
        
        # Create files
        create_files()
        
        # Show API update instructions
        update_api_file()
        
        # Show next steps
        show_next_steps()
        
        print("\n✅ Setup complete!")
        print("\n💡 Tip: Open VS Code and start copying content to the created files")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
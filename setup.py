#!/usr/bin/env python3
"""
Setup script for AI-SAST
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is 3.8 or higher"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} is supported")
    return True

def install_requirements():
    """Install required packages"""
    print("📦 Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False

def check_gcloud_cli():
    """Check if gcloud CLI is installed"""
    try:
        result = subprocess.run(["gcloud", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Google Cloud CLI is installed")
            return True
        else:
            print("❌ Google Cloud CLI is not installed")
            return False
    except FileNotFoundError:
        print("❌ Google Cloud CLI is not installed")
        return False

def check_authentication():
    """Check if user is authenticated with gcloud"""
    try:
        result = subprocess.run(["gcloud", "auth", "list"], capture_output=True, text=True)
        if "ACTIVE" in result.stdout:
            print("✅ Google Cloud authentication is active")
            return True
        else:
            print("❌ No active Google Cloud authentication found")
            return False
    except FileNotFoundError:
        print("❌ Cannot check authentication - gcloud CLI not found")
        return False

def get_project_id():
    """Get the current Google Cloud project ID"""
    try:
        result = subprocess.run(["gcloud", "config", "get-value", "project"], capture_output=True, text=True)
        project_id = result.stdout.strip()
        if project_id:
            print(f"✅ Current Google Cloud project: {project_id}")
            return project_id
        else:
            print("❌ No Google Cloud project is set")
            return None
    except FileNotFoundError:
        print("❌ Cannot get project ID - gcloud CLI not found")
        return None

def enable_apis():
    """Enable required APIs"""
    print("🔧 Enabling required APIs...")
    apis = [
        "aiplatform.googleapis.com",
        "ml.googleapis.com",
        "compute.googleapis.com"
    ]
    
    for api in apis:
        try:
            result = subprocess.run(
                ["gcloud", "services", "enable", api],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(f"✅ Enabled {api}")
            else:
                print(f"❌ Failed to enable {api}: {result.stderr}")
        except FileNotFoundError:
            print("❌ Cannot enable APIs - gcloud CLI not found")
            return False
    return True

def create_env_file():
    """Create environment configuration file"""
    project_id = get_project_id()
    if not project_id:
        project_id = input("Enter your Google Cloud Project ID: ").strip()
    
    location = input("Enter Vertex AI location (default: us-central1): ").strip() or "us-central1"
    
    env_content = f"""# Google Cloud Project Configuration
GOOGLE_CLOUD_PROJECT={project_id}
GOOGLE_LOCATION={location}

# Authentication (optional - if not using gcloud auth)
# GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account-key.json

# Optional: Custom model configurations
# VERTEX_AI_TEXT_MODEL=text-bison@001
# GEMINI_MODEL=gemini-2.0-flash-exp
# VERTEX_AI_EMBEDDING_MODEL=textembedding-gecko@001
"""
    
    with open("env_config.txt", "w") as f:
        f.write(env_content)
    
    print("✅ Environment configuration saved to env_config.txt")
    print("💡 You can source this file or set these environment variables manually")

def main():
    """Main setup function"""
    print("🚀 Setting up AI-SAST...")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install requirements
    if not install_requirements():
        sys.exit(1)
    
    # Check gcloud CLI
    if not check_gcloud_cli():
        print("\n📋 To install Google Cloud CLI:")
        print("   Visit: https://cloud.google.com/sdk/docs/install")
        print("   Or run: curl https://sdk.cloud.google.com | bash")
        
        choice = input("\nContinue without gcloud CLI? (y/n): ").lower()
        if choice != 'y':
            sys.exit(1)
    else:
        # Check authentication
        if not check_authentication():
            print("\n📋 To authenticate with Google Cloud:")
            print("   Run: gcloud auth login")
            print("   Or: gcloud auth application-default login")
        
        # Enable APIs
        enable_apis()
    
    # Create environment configuration
    create_env_file()
    
    print("\n🎉 Setup complete!")
    print("\n📋 Next steps:")
    print("   1. Set your environment variables (see env_config.txt)")
    print("   2. Run: python -m src.core.scanner --help")
    print("   3. Start scanning your code for security vulnerabilities!")

if __name__ == "__main__":
    main()


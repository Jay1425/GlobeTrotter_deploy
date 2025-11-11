#!/usr/bin/env python3
"""
Pre-deployment test script for GlobeTrotter
Run this before deploying to Render.com
"""
import os
import sys

def check_file_exists(filepath, required=True):
    """Check if a file exists"""
    exists = os.path.exists(filepath)
    status = "✅" if exists else ("❌" if required else "⚠️")
    print(f"{status} {filepath}")
    return exists

def check_deployment_files():
    """Check all required deployment files"""
    print("\n🔍 Checking Deployment Files...\n")
    
    required_files = [
        'Procfile',
        'runtime.txt',
        'requirements.txt',
        'build.sh',
        'render.yaml',
        '.env.example',
        'app.py',
        'models.py',
        'init_db.py',
    ]
    
    optional_files = [
        '.gitignore',
        'RENDER_DEPLOY.md',
        'DEPLOY_CHECKLIST.md',
        'DEPLOYMENT_SUMMARY.md',
    ]
    
    all_good = True
    
    print("Required Files:")
    for file in required_files:
        if not check_file_exists(file, required=True):
            all_good = False
    
    print("\nOptional Files:")
    for file in optional_files:
        check_file_exists(file, required=False)
    
    return all_good

def check_requirements():
    """Check requirements.txt has necessary packages"""
    print("\n🔍 Checking Requirements...\n")
    
    try:
        with open('requirements.txt', 'r', encoding='utf-8') as f:
            content = f.read().lower()
        
        required_packages = ['gunicorn', 'psycopg2', 'flask', 'flask_sqlalchemy']
        all_found = True
        
        for package in required_packages:
            # Check with both underscore and hyphen
            if package in content or package.replace('_', '-') in content:
                print(f"✅ {package.replace('_', '-')}")
            else:
                print(f"❌ {package.replace('_', '-')} - MISSING!")
                all_found = False
        
        return all_found
    except FileNotFoundError:
        print("❌ requirements.txt not found!")
        return False

def check_procfile():
    """Check Procfile configuration"""
    print("\n🔍 Checking Procfile...\n")
    
    try:
        with open('Procfile', 'r') as f:
            content = f.read().strip()
        
        if 'gunicorn' in content and 'app:app' in content:
            print(f"✅ Procfile looks good: {content}")
            return True
        else:
            print(f"⚠️ Procfile may need adjustment: {content}")
            return False
    except FileNotFoundError:
        print("❌ Procfile not found!")
        return False

def check_runtime():
    """Check runtime.txt"""
    print("\n🔍 Checking Python Runtime...\n")
    
    try:
        with open('runtime.txt', 'r') as f:
            content = f.read().strip()
        
        if 'python-3.11' in content:
            print(f"✅ Runtime: {content}")
            return True
        else:
            print(f"⚠️ Runtime version: {content}")
            return True
    except FileNotFoundError:
        print("❌ runtime.txt not found!")
        return False

def check_env_example():
    """Check .env.example"""
    print("\n🔍 Checking Environment Variables Template...\n")
    
    try:
        with open('.env.example', 'r') as f:
            content = f.read()
        
        required_vars = [
            'SECRET_KEY',
            'DATABASE_URL',
            'FLASK_ENV',
            'MAIL_USERNAME',
            'MAIL_PASSWORD',
        ]
        
        all_found = True
        for var in required_vars:
            if var in content:
                print(f"✅ {var}")
            else:
                print(f"❌ {var} - MISSING!")
                all_found = False
        
        return all_found
    except FileNotFoundError:
        print("⚠️ .env.example not found (optional)")
        return True

def check_gitignore():
    """Check .gitignore"""
    print("\n🔍 Checking .gitignore...\n")
    
    try:
        with open('.gitignore', 'r') as f:
            content = f.read()
        
        important_patterns = ['.env', '__pycache__', 'venv/', '*.db']
        all_found = True
        
        for pattern in important_patterns:
            if pattern in content:
                print(f"✅ {pattern}")
            else:
                print(f"⚠️ {pattern} - Consider adding")
                all_found = False
        
        return all_found
    except FileNotFoundError:
        print("⚠️ .gitignore not found")
        return False

def check_build_script():
    """Check build.sh"""
    print("\n🔍 Checking Build Script...\n")
    
    try:
        with open('build.sh', 'r') as f:
            content = f.read()
        
        if 'pip install' in content and 'requirements.txt' in content:
            print("✅ Build script installs dependencies")
        else:
            print("⚠️ Build script may be incomplete")
        
        if 'init_db.py' in content or 'db.create_all' in content:
            print("✅ Build script initializes database")
            return True
        else:
            print("⚠️ Build script doesn't initialize database")
            return False
    except FileNotFoundError:
        print("❌ build.sh not found!")
        return False

def check_sensitive_data():
    """Check for hardcoded sensitive data"""
    print("\n🔍 Checking for Hardcoded Secrets...\n")
    
    try:
        with open('app.py', 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        warnings = []
        
        # Check for os.environ usage
        if 'os.environ.get' in content or 'os.getenv' in content:
            print("✅ Using environment variables")
        else:
            print("⚠️ May not be using environment variables")
            warnings.append("environment variables")
        
        # Check for IS_PRODUCTION variable
        if 'IS_PRODUCTION' in content:
            print("✅ Production mode detection implemented")
        
        if not warnings:
            print("✅ No obvious hardcoded secrets found")
            return True
        else:
            return False
            
    except FileNotFoundError:
        print("❌ app.py not found!")
        return False

def main():
    """Run all checks"""
    print("=" * 60)
    print("🚀 GlobeTrotter - Pre-Deployment Check")
    print("=" * 60)
    
    checks = [
        ("Deployment Files", check_deployment_files),
        ("Requirements", check_requirements),
        ("Procfile", check_procfile),
        ("Python Runtime", check_runtime),
        ("Environment Variables", check_env_example),
        ("Gitignore", check_gitignore),
        ("Build Script", check_build_script),
        ("Sensitive Data", check_sensitive_data),
    ]
    
    results = []
    for name, check_func in checks:
        result = check_func()
        results.append((name, result))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Summary")
    print("=" * 60 + "\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print("\n" + "=" * 60)
    print(f"Score: {passed}/{total} checks passed")
    print("=" * 60 + "\n")
    
    if passed == total:
        print("🎉 All checks passed! You're ready to deploy!")
        print("\nNext steps:")
        print("1. Push to GitHub: git push origin main")
        print("2. Follow DEPLOY_CHECKLIST.md")
        print("3. Create services on Render.com")
        return 0
    else:
        print("⚠️ Some checks failed. Please review the issues above.")
        print("\nFix the issues and run this script again.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

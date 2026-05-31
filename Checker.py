import os
import re

def check_file(filepath):
    print(f"\n{'='*60}")
    print(f"Checking: {filepath}")
    print('='*60)
    
    errors = []
    warnings = []
    
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    # ========== PYTHON FILE CHECK ==========
    if filepath.endswith('.py'):
        app_count = 0
        secret_key_found = False
        init_db_count = 0
        
        for i, line in enumerate(lines, 1):
            # Check 1: Duplicate app = Flask
            if 'app = Flask(__name__)' in line:
                app_count += 1
                if app_count > 1:
                    errors.append(f"Line {i}: Duplicate 'app = Flask(__name__)' mila. Sirf 1 baar likho")
            
            # Check 2: Secret key
            if 'app.secret_key' in line:
                secret_key_found = True
            
            # Check 3: Duplicate def init_db
            if line.strip().startswith('def init_db('):
                init_db_count += 1
                if init_db_count > 1:
                    errors.append(f"Line {i}: 'def init_db()' 2 baar defined hai")
            
            # Check 4: form data access without .get()
            if "request.form['" in line and '.get(' not in line:
                warnings.append(f"Line {i}: request.form['...'] use kar rahe. Better hai .get() use karo: {line.strip()}")
            
            # Check 5: SQL Injection risk
            if 'f"' in line and 'execute' in line:
                warnings.append(f"Line {i}: SQL me f-string risky hai. ? use karo: {line.strip()}")
    
    # ========== HTML FILE CHECK ==========
    if filepath.endswith('.html'):
        if_stack = []
        form_found = False
        form_has_method = False
        
        for i, line in enumerate(lines, 1):
            # Check 1: Jinja if/endif balance
            if '{% if' in line:
                if_stack.append(i)
            if '{% endif' in line:
                if not if_stack:
                    errors.append(f"Line {i}: {% endif %} extra hai, {% if %} missing")
                else:
                    if_stack.pop()
            
            # Check 2: Form method check
            if '<form' in line:
                form_found = True
                if 'method=' not in line:
                    warnings.append(f"Line {i}: <form> me method='POST' missing hai")
                else:
                    form_has_method = True
            
            # Check 3: Input name attribute
            if '<input' in line and 'type=' in line:
                if 'name=' not in line:
                    errors.append(f"Line {i}: <input> me name='' missing hai. Python me data nahi milega: {line.strip()}")
            
            # Check 4: Session use without check
            if 'session.' in line and 'base.html' in filepath:
                warnings.append(f"Line {i}: session use ho raha. main.py me app.secret_key set hai na? Check kar")
            
            # Check 5: extends missing but blocks used
            if '{% block' in line and i < 10:
                has_extends = any('{% extends' in l for l in lines[:5])
                if not has_extends and 'base.html' not in filepath:
                    warnings.append(f"Line {i}: block use ho raha but {% extends %} missing")
        
        # Unclosed if check
        if if_stack:
            for line_num in if_stack:
                errors.append(f"Line {line_num}: {% if %} ka {% endif %} missing hai")
        
        if form_found and not form_has_method:
            warnings.append("Form mila but method='POST' kahi nahi likha")
    
    # ========== PRINT RESULTS ==========
    if errors:
        print("\n❌ ERRORS MILI:")
        for err in errors:
            print(f"  {err}")
    else:
        print("\n✅ Koi Error nahi mila")
    
    if warnings:
        print("\n⚠️  WARNINGS:")
        for warn in warnings:
            print(f"  {warn}")
    
    if not errors and not warnings:
        print("\n🎉 File bilkul perfect hai!")
    
    return len(errors)

def main():
    print("SUREJOB PROJECT CHECKER v1.0")
    print("Har file ko line-by-line check karega\n")
    
    total_errors = 0
    
    # Check main.py
    if os.path.exists('main.py'):
        total_errors += check_file('main.py')
    else:
        print("❌ main.py nahi mila")
    
    # Check all HTML files in templates/
    if os.path.exists('templates'):
        for file in os.listdir('templates'):
            if file.endswith('.html'):
                filepath = os.path.join('templates', file)
                total_errors += check_file(filepath)
    else:
        print("❌ templates folder nahi mila")
    
    print(f"\n{'='*60}")
    print(f"TOTAL ERRORS: {total_errors}")
    if total_errors == 0:
        print("🎉 SAB PERFECT HAI! Deploy kar de")
    else:
        print("⚠️  Upar wali errors fix kar pehle")
    print('='*60)

if __name__ == '__main__':
    main()

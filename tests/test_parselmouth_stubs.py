import ast
import parselmouth
import os
import sys

STUB_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'typings', 'parselmouth', '__init__.pyi'))
OUTPUT_FILE = 'missing_items.txt'

def main():
    if not os.path.exists(STUB_FILE):
        with open(OUTPUT_FILE, 'w') as f:
            f.write(f"Stub file not found at {STUB_FILE}")
        sys.exit(1)
        
    with open(STUB_FILE, 'r') as f:
        tree = ast.parse(f.read())

    missing_items = []
    
    TYPING_ONLY = {'Positive', 'NonNegative'}

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            class_name = node.name
            
            if class_name in TYPING_ONLY:
                continue

            if not hasattr(parselmouth, class_name):
                missing_items.append(f"Missing Class: {class_name}")
                continue

            runtime_class = getattr(parselmouth, class_name)
            
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    method_name = item.name
                    if method_name == '__init__': continue
                    
                    if not hasattr(runtime_class, method_name):
                        missing_items.append(f"Missing Method: {class_name}.{method_name}")
        
        elif isinstance(node, ast.FunctionDef):
             func_name = node.name
             if not hasattr(parselmouth, func_name):
                 missing_items.append(f"Missing Function: {func_name}")

    if missing_items:
        with open(OUTPUT_FILE, 'w') as f:
            f.write("\n".join(missing_items))
        sys.exit(1)
    else:
        with open(OUTPUT_FILE, 'w') as f:
            f.write("Verification Successful")

if __name__ == '__main__':
    main()

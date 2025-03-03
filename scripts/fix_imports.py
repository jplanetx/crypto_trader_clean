"""
Script to fix Python import issues by resetting sys.modules cache and resources.
"""
import sys
import os
import importlib
import logging
import pkgutil
import inspect
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_imports(component_name="coinbase_streaming"):
    """Reset import cache for specific modules."""
    # First, add project root to path
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.insert(0, root_dir)
    
    logger.info(f"Root directory: {root_dir}")
    logger.info(f"Fixing imports for component: {component_name}")
    
    # Clear any module caches that might contain our component
    modules_to_clear = [
        f"src.core.{component_name}",
        f"src.core",
        "src"
    ]
    
    cleared = []
    for module_name in modules_to_clear:
        if module_name in sys.modules:
            del sys.modules[module_name]
            cleared.append(module_name)
    
    logger.info(f"Cleared modules from sys.modules: {', '.join(cleared) or 'none'}")
    
    # Create a backup of the CoinbaseStreaming class
    component_file = os.path.join(root_dir, "src", "core", f"{component_name}.py")
    backup_file = os.path.join(root_dir, "src", "core", f"{component_name}_backup.py")
    
    try:
        with open(component_file, 'r') as f:
            content = f.read()
            
        with open(backup_file, 'w') as f:
            f.write(content)
            
        logger.info(f"Created backup of {component_file} to {backup_file}")
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
    
    # Try to fix the __init__.py files
    init_files = [
        os.path.join(root_dir, "src", "__init__.py"),
        os.path.join(root_dir, "src", "core", "__init__.py"),
    ]
    
    for init_file in init_files:
        try:
            Path(os.path.dirname(init_file)).mkdir(parents=True, exist_ok=True)
            
            if not os.path.exists(init_file):
                with open(init_file, 'w') as f:
                    f.write('"""Package initialization."""\n')
                logger.info(f"Created {init_file}")
            else:
                logger.info(f"{init_file} already exists")
        except Exception as e:
            logger.error(f"Failed to create/check {init_file}: {e}")
    
    # Attempt to directly import the module to validate fix
    try:
        logger.info("Testing import...")
        module_path = f"src.core.{component_name}"
        module = importlib.import_module(module_path)
        
        class_name = ''.join(word.capitalize() for word in component_name.split('_'))
        if hasattr(module, class_name):
            logger.info(f"✅ Successfully imported {class_name} from {module_path}")
        else:
            logger.error(f"❌ Module imported but {class_name} class not found")
            logger.info("Available attributes in module:")
            for attr in dir(module):
                if not attr.startswith('__'):
                    logger.info(f"  - {attr}")
    except ImportError as e:
        logger.error(f"❌ Import failed: {e}")
    
    logger.info("Import fix completed. Run your verification script again.")
    
if __name__ == "__main__":
    fix_imports()

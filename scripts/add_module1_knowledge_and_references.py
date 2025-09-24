import runpy, os, sys

# Compatibility wrapper for moved script
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE1_PATH = os.path.join(CURRENT_DIR, 'module1', 'add_knowledge_and_references.py')
if not os.path.exists(MODULE1_PATH):
    raise SystemExit('Missing module1/add_knowledge_and_references.py')
runpy.run_path(MODULE1_PATH, run_name='__main__')



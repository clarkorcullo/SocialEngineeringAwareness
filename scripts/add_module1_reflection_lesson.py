import runpy, os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE1_PATH = os.path.join(CURRENT_DIR, 'module1', 'add_reflection.py')
if not os.path.exists(MODULE1_PATH):
    raise SystemExit('Missing module1/add_reflection.py')
runpy.run_path(MODULE1_PATH, run_name='__main__')





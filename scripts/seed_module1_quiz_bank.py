import runpy, os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE1_PATH = os.path.join(CURRENT_DIR, 'module1', 'seed_quiz_bank.py')
if not os.path.exists(MODULE1_PATH):
    raise SystemExit('Missing module1/seed_quiz_bank.py')
runpy.run_path(MODULE1_PATH, run_name='__main__')





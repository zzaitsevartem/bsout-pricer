import runpy
import sys
sys.argv.append('--verify')
runpy.run_path('/tmp/hot30_repair.py', run_name='__main__')

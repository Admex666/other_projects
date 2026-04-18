import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from simulator.engine import SimulationEngine

engine = SimulationEngine(days=1, num_users=10)
res = engine.run(mode='baseline')
print(f"Return type: {type(res)}")
if isinstance(res, tuple):
    print(f"Tuple length: {len(res)}")
    for i, item in enumerate(res):
        print(f"Item {i} type: {type(item)}")
else:
    print(f"Single return type: {type(res)}")

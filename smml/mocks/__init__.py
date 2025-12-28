import sys
from . import sentence_transformers_mock as st
from . import lightgbm_mock as lgb
from . import shap_mock as shap

sys.modules['sentence_transformers'] = st
sys.modules['lightgbm'] = lgb
sys.modules['shap'] = shap

import logging
logging.basicConfig(level=logging.DEBUG)
import warnings
warnings.filterwarnings(action="ignore", module="sklearn", message="^internal gelsd")

def is_jupyter_env():
    try:
        __IPYTHON__
        return True
    except NameError:
        return False

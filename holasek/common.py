import logging
logging.basicConfig(level=logging.DEBUG)
mpl_logger = logging.getLogger('matplotlib')
mpl_logger.setLevel(logging.WARNING)
import warnings
warnings.filterwarnings(action="ignore", module="sklearn", message="^internal gelsd")
from IPython.display import Markdown
import multiprocessing

def is_jupyter_env():
    try:
        __IPYTHON__
        return True
    except NameError:
        return False

def load_markup(path):
    with open(path) as input:
        lines = input.readlines()
        markup = "\n".join(map(lambda l: l.strip(), lines))
        return Markdown(markup)

N_CORES = multiprocessing.cpu_count()
logging.info("Using %d cores...", N_CORES)

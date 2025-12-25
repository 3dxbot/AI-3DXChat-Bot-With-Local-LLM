# PyInstaller hook for FAISS
from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = collect_all('faiss')

# Add specific FAISS modules
hiddenimports.extend([
    'faiss._swigfaiss',
    'faiss.contrib',
    'faiss.contrib.exact_scoring',
    'faiss.contrib.inspect_tools',
    'faiss.contrib.ondisk_ivf',
    'faiss.contrib.pca',
    'faiss.contrib.torch_utils'
])

# Exclude GPU modules to reduce size
excludedimports = [
    'faiss.contrib.gpu',
    'torch.cuda'
]
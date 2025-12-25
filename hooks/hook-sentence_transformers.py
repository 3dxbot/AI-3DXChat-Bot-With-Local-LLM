# PyInstaller hook for sentence-transformers
from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = collect_all('sentence_transformers')

# Add transformers dependencies
hiddenimports.extend([
    'transformers',
    'transformers.models',
    'transformers.models.bert',
    'transformers.models.roberta',
    'transformers.models.distilbert',
    'tokenizers',
    'tokenizers.models',
    'tokenizers.pre_tokenizers',
    'tokenizers.processors',
    'tokenizers.normalizers',
    'tokenizers.decoders'
])
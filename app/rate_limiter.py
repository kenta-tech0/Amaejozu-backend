"""
レート制限設定
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

# レート制限インスタンス
limiter = Limiter(key_func=get_remote_address)

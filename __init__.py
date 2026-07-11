# agent/__init__.py
import os
import ssl
import warnings

# ===== SSL 证书问题修复 =====
# 临时解决 Windows SSL 证书问题
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# 抑制 SSL 警告
warnings.filterwarnings('ignore', message='unverified HTTPS request')

# 设置环境变量
os.environ['PYTHONHTTPSVERIFY'] = '0'
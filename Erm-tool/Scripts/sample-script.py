#!c:\project\erm-tool\scripts\python.exe
# EASY-INSTALL-ENTRY-SCRIPT: 'QuantStats==0.0.25','console_scripts','sample'
__requires__ = 'QuantStats==0.0.25'
import re
import sys
from pkg_resources import load_entry_point

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
    sys.exit(
        load_entry_point('QuantStats==0.0.25', 'console_scripts', 'sample')()
    )

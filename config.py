# Statement for enabling the development environment
DEBUG = True

# Define the application directory
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Define the database - we are working with
# SQLite for this example
if 'CODEGRADE_DATABASE_URL' not in os.environ:
    SQLALCHEMY_DATABASE_URI = 'postgresql:///codegrade_dev'
else:
    SQLALCHEMY_DATABASE_URI = os.environ['CODEGRADE_DATABASE_URL']
DATABASE_CONNECT_OPTIONS = {}

# Application threads. A common general assumption is
# using 2 per available processor cores - to handle
# incoming requests using one and performing background
# operations using the other.
THREADS_PER_PAGE = 2

# Enable protection agains *Cross-site Request Forgery (CSRF)*
CSRF_ENABLED     = True

# Use a secure, unique and absolutely secret key for
# signing the data.
CSRF_SESSION_KEY = "secret"

# Secret key for signing cookies
SECRET_KEY = "secret"

# Path for storage of uploaded files
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')

# Maximum size in bytes for single upload request
MAX_UPLOAD_SIZE = 64 * 2**20  # 64 megabytes

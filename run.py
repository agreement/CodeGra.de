#!/usr/bin/env python3

# Run a test server.
import psef

if __name__ == '__main__':
    app = psef.create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)

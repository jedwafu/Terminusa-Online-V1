echo "#!/bin/bash
source venv/bin/activate
exec gunicorn -b 0.0.0.0:5000 -w 4 --timeout 120 server:app" > run.sh
chmod +x run.sh

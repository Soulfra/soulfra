module.exports = {
  apps: [
    {
      name: 'soulfra-flask',
      script: 'app.py',
      interpreter: 'python3',
      cwd: '/Users/matthewmauer/Desktop/roommate-chat/soulfra-simple',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        FLASK_ENV: 'development',
        PYTHONUNBUFFERED: '1'
      },
      error_file: './logs/flask-error.log',
      out_file: './logs/flask-out.log',
      log_file: './logs/flask-combined.log',
      time: true,
      merge_logs: true
    },
    {
      name: 'cringeproof-api',
      script: 'cringeproof_api.py',
      interpreter: 'python3',
      cwd: '/Users/matthewmauer/Desktop/roommate-chat/soulfra-simple',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        FLASK_ENV: 'development',
        PYTHONUNBUFFERED: '1'
      },
      error_file: './logs/cringeproof-error.log',
      out_file: './logs/cringeproof-out.log',
      log_file: './logs/cringeproof-combined.log',
      time: true,
      merge_logs: true
    }
  ]
};

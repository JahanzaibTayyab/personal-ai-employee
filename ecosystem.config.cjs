// PM2 Ecosystem Configuration for AI Employee
// Usage:
//   pm2 start ecosystem.config.cjs
//   pm2 start ecosystem.config.cjs --only file-watcher
//   pm2 start ecosystem.config.cjs --only web-dashboard
//
// Manage:
//   pm2 status          # Check all processes
//   pm2 logs            # View all logs
//   pm2 restart all     # Restart everything
//   pm2 stop all        # Stop everything
//   pm2 save && pm2 startup  # Survive reboots

const path = require('path');

// ─── Configuration ──────────────────────────────────────────────────
// Override these via environment variables or edit directly
const VAULT = process.env.AI_VAULT || path.join(require('os').homedir(), 'AI_Employee_Vault');
const GMAIL_CREDS = process.env.GMAIL_CREDENTIALS || path.join(require('os').homedir(), 'credentials.json');
const WEB_PORT = process.env.AI_WEB_PORT || '8000';
const WEB_HOST = process.env.AI_WEB_HOST || '127.0.0.1';
const CWD = __dirname;

module.exports = {
  apps: [
    // ─── Bronze Tier ──────────────────────────────────────────────
    {
      name: 'file-watcher',
      script: 'uv',
      args: `run ai-employee watch --vault ${VAULT} --interval 60`,
      cwd: CWD,
      autorestart: true,
      restart_delay: 5000,
      max_restarts: 50,
      min_uptime: '10s',
      watch: false,
      env: {
        VAULT_PATH: VAULT,
      },
    },
    {
      name: 'gmail-watcher',
      script: 'uv',
      args: `run ai-employee watch-gmail --vault ${VAULT} --credentials ${GMAIL_CREDS} --interval 120`,
      cwd: CWD,
      autorestart: true,
      restart_delay: 10000,
      max_restarts: 30,
      min_uptime: '10s',
      watch: false,
      env: {
        VAULT_PATH: VAULT,
      },
    },

    // ─── Silver Tier ──────────────────────────────────────────────
    {
      name: 'approval-watcher',
      script: 'uv',
      args: `run ai-employee watch-approvals --vault ${VAULT} --interval 60`,
      cwd: CWD,
      autorestart: true,
      restart_delay: 5000,
      max_restarts: 50,
      min_uptime: '10s',
      watch: false,
      env: {
        VAULT_PATH: VAULT,
      },
    },
    {
      name: 'whatsapp-watcher',
      script: 'uv',
      args: `run ai-employee watch-whatsapp --vault ${VAULT}`,
      cwd: CWD,
      autorestart: true,
      restart_delay: 15000,
      max_restarts: 20,
      min_uptime: '10s',
      watch: false,
      env: {
        VAULT_PATH: VAULT,
      },
    },
    {
      name: 'web-dashboard',
      script: 'uv',
      args: `run ai-employee web --host ${WEB_HOST} --port ${WEB_PORT}`,
      cwd: CWD,
      autorestart: true,
      restart_delay: 3000,
      max_restarts: 50,
      min_uptime: '5s',
      watch: false,
      env: {
        VAULT_PATH: VAULT,
      },
    },
  ],
};

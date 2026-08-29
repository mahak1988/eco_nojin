import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Settings as SettingsIcon, Shield, Bell, Link as LinkIcon,
  Save, Globe, Clock, Lock, Users, Database, Cpu,
  CheckCircle2, XCircle, AlertCircle, Mail, Key, Palette
} from 'lucide-react';
import './AdminTheme.css';

export default function AdminSettings() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<'general' | 'security' | 'notifications' | 'integrations'>('general');
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const tabs = [
    { id: 'general', label: 'General', icon: <SettingsIcon size={16} /> },
    { id: 'security', label: 'Security', icon: <Shield size={16} /> },
    { id: 'notifications', label: 'Notifications', icon: <Bell size={16} /> },
    { id: 'integrations', label: 'Integrations', icon: <LinkIcon size={16} /> },
  ];

  return (
    <div className="admin-page-container">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <SettingsIcon size={32} style={{ color: 'var(--accent-primary)' }} />
            {t('nav.settings')}
          </h1>
          <p className="page-subtitle">Configure and customize your Eco Nojin platform</p>
        </div>
        {saved && (
          <div className="status-badge success">
            <CheckCircle2 size={14} /> {t('common.save')}d!
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="settings-tabs">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={'settings-tab' + (activeTab === tab.id ? ' active' : '')}
            onClick={() => setActiveTab(tab.id as any)}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="settings-card">
        {/* General Tab */}
        {activeTab === 'general' && (
          <div>
            <h2 className="settings-section-title">
              <SettingsIcon size={24} style={{ color: 'var(--accent-primary)' }} />
              General Settings
            </h2>

            <div className="settings-group">
              <div className="settings-row">
                <div className="settings-row-info">
                  <div className="settings-row-label">Platform Name</div>
                  <p className="settings-row-desc">Display name shown across the platform</p>
                </div>
                <input className="form-input" type="text" defaultValue="Eco Nojin" style={{ maxWidth: '300px' }} />
              </div>

              <div className="settings-row">
                <div className="settings-row-info">
                  <div className="settings-row-label">Default Language</div>
                  <p className="settings-row-desc">Primary language for new users</p>
                </div>
                <select className="form-input" defaultValue="fa" style={{ maxWidth: '200px' }}>
                  <option value="fa">🇮🇷 فارسی</option>
                  <option value="en">🇬🇧 English</option>
                  <option value="ar">🇸🇦 العربية</option>
                </select>
              </div>

              <div className="settings-row">
                <div className="settings-row-info">
                  <div className="settings-row-label">Timezone</div>
                  <p className="settings-row-desc">System-wide timezone</p>
                </div>
                <select className="form-input" defaultValue="Asia/Tehran" style={{ maxWidth: '250px' }}>
                  <option value="Asia/Tehran">Asia/Tehran (UTC+3:30)</option>
                  <option value="UTC">UTC</option>
                  <option value="Europe/London">Europe/London</option>
                  <option value="America/New_York">America/New York</option>
                </select>
              </div>

              <div className="settings-row">
                <div className="settings-row-info">
                  <div className="settings-row-label">Date Format</div>
                  <p className="settings-row-desc">How dates are displayed</p>
                </div>
                <select className="form-input" defaultValue="YYYY-MM-DD" style={{ maxWidth: '200px' }}>
                  <option value="YYYY-MM-DD">YYYY-MM-DD</option>
                  <option value="DD/MM/YYYY">DD/MM/YYYY</option>
                  <option value="MM/DD/YYYY">MM/DD/YYYY</option>
                </select>
              </div>

              <div className="settings-row">
                <div className="settings-row-info">
                  <div className="settings-row-label">Currency</div>
                  <p className="settings-row-desc">Default currency for financial displays</p>
                </div>
                <select className="form-input" defaultValue="IRR" style={{ maxWidth: '200px' }}>
                  <option value="IRR">🇮🇷 IRR (Rial)</option>
                  <option value="USD">🇺🇸 USD</option>
                  <option value="EUR">🇪🇺 EUR</option>
                </select>
              </div>
            </div>

            <button className="btn-primary" onClick={handleSave}>
              <Save size={16} /> Save Changes
            </button>
          </div>
        )}

        {/* Security Tab */}
        {activeTab === 'security' && (
          <div>
            <h2 className="settings-section-title">
              <Shield size={24} style={{ color: 'var(--accent-primary)' }} />
              Security Settings
            </h2>

            <div className="settings-group">
              <div className="settings-row">
                <div className="settings-row-info">
                  <div className="settings-row-label">Session Timeout</div>
                  <p className="settings-row-desc">Auto-logout after inactivity (minutes)</p>
                </div>
                <input className="form-input" type="number" defaultValue="60" style={{ maxWidth: '150px' }} />
              </div>

              <div className="settings-row">
                <div className="settings-row-info">
                  <div className="settings-row-label">Max Login Attempts</div>
                  <p className="settings-row-desc">Lock account after failed attempts</p>
                </div>
                <input className="form-input" type="number" defaultValue="5" style={{ maxWidth: '150px' }} />
              </div>

              <div className="settings-row">
                <div className="settings-row-info">
                  <div className="settings-row-label">Password Minimum Length</div>
                  <p className="settings-row-desc">Minimum characters required</p>
                </div>
                <input className="form-input" type="number" defaultValue="8" style={{ maxWidth: '150px' }} />
              </div>

              <div className="settings-row">
                <div className="settings-row-info">
                  <div className="settings-row-label">Two-Factor Authentication</div>
                  <p className="settings-row-desc">Require 2FA for admin accounts</p>
                </div>
                <div className="toggle-switch active" />
              </div>

              <div className="settings-row">
                <div className="settings-row-info">
                  <div className="settings-row-label">IP Whitelist</div>
                  <p className="settings-row-desc">Restrict admin access to specific IPs</p>
                </div>
                <button className="btn-secondary">
                  <Lock size={14} /> Configure
                </button>
              </div>
            </div>

            <button className="btn-primary" onClick={handleSave}>
              <Save size={16} /> Save Changes
            </button>
          </div>
        )}

        {/* Notifications Tab */}
        {activeTab === 'notifications' && (
          <div>
            <h2 className="settings-section-title">
              <Bell size={24} style={{ color: 'var(--accent-primary)' }} />
              Notification Settings
            </h2>

            <div className="settings-group">
              {[
                { title: 'New User Registration', desc: 'Get notified when users sign up', enabled: true },
                { title: 'Failed Login Attempts', desc: 'Alert on suspicious login activity', enabled: true },
                { title: 'System Errors', desc: 'Critical error notifications', enabled: true },
                { title: 'Content Approval Required', desc: 'When content needs review', enabled: true },
                { title: 'Security Alerts', desc: 'High-priority security events', enabled: true },
                { title: 'Financial Transactions', desc: 'Large transaction alerts', enabled: false },
                { title: 'Weekly Reports', desc: 'Summary every Monday', enabled: true },
                { title: 'System Maintenance', desc: 'Scheduled maintenance alerts', enabled: false },
              ].map((notif, i) => (
                <div className="settings-row" key={i}>
                  <div className="settings-row-info">
                    <div className="settings-row-label">{notif.title}</div>
                    <p className="settings-row-desc">{notif.desc}</p>
                  </div>
                  <div className={'toggle-switch' + (notif.enabled ? ' active' : '')} />
                </div>
              ))}
            </div>

            <button className="btn-primary" onClick={handleSave}>
              <Save size={16} /> Save Changes
            </button>
          </div>
        )}

        {/* Integrations Tab */}
        {activeTab === 'integrations' && (
          <div>
            <h2 className="settings-section-title">
              <LinkIcon size={24} style={{ color: 'var(--accent-primary)' }} />
              Integrations
            </h2>

            <div className="settings-group">
              {[
                { name: 'Supabase', status: 'connected', icon: <Database size={24} />, desc: 'Database & Auth' },
                { name: 'Ollama (AI)', status: 'connected', icon: <Cpu size={24} />, desc: 'Local AI models' },
                { name: 'CDSE (Satellite)', status: 'connected', icon: <Globe size={24} />, desc: 'Copernicus satellite data' },
                { name: 'NASA POWER', status: 'connected', icon: <Globe size={24} />, desc: 'Weather & climate data' },
                { name: 'Telegram Bot API', status: 'connected', icon: <Mail size={24} />, desc: 'Bot messaging service' },
                { name: 'Blockchain', status: 'disconnected', icon: <Key size={24} />, desc: 'Not configured yet' },
                { name: 'Stripe Payments', status: 'disconnected', icon: <Key size={24} />, desc: 'Not configured yet' },
              ].map((integration, i) => (
                <div className="integration-card" key={i}>
                  <div className="integration-icon">
                    {integration.icon}
                  </div>
                  <div className="integration-info">
                    <div className="integration-name">{integration.name}</div>
                    <div className={'integration-status ' + integration.status}>
                      <span className={'integration-status-dot ' + (integration.status === 'connected' ? 'online' : 'offline')}></span>
                      {integration.desc}
                    </div>
                  </div>
                  <button className="btn-secondary" style={{ flexShrink: 0 }}>
                    Configure
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

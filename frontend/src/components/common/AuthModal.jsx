import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { IconShield, IconUser, IconLock, IconCheckCircle, IconAlertTriangle, IconX } from './Icons';

export const AuthModal = ({ isOpen, onClose }) => {
  const { login, register, quickLogin, authError, setAuthError } = useAuth();
  const [mode, setMode] = useState('login'); // 'login' or 'register'
  const [submitting, setSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');

  // Form states
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [role, setRole] = useState('environmental_analyst');

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setSuccessMessage('');
    setAuthError(null);

    try {
      if (mode === 'login') {
        await login(username, password);
        setSuccessMessage('Authentication successful! Welcome back.');
      } else {
        await register({
          username,
          email,
          password,
          full_name: fullName,
          role,
        });
        setSuccessMessage('Account created and logged in successfully!');
      }
      setTimeout(() => {
        onClose();
      }, 700);
    } catch (err) {
      // Error is set in context
    } finally {
      setSubmitting(false);
    }
  };

  const handleQuickLogin = async (roleType) => {
    setSubmitting(true);
    setSuccessMessage('');
    try {
      await quickLogin(roleType);
      setSuccessMessage(`Authenticated as ${roleType === 'admin' ? 'Administrator' : 'Analyst'}!`);
      setTimeout(() => {
        onClose();
      }, 600);
    } catch (err) {
      // Handled in context
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
      <div className="bg-[#051c14] border border-emerald-500/30 w-full max-w-md rounded-2xl shadow-2xl p-6 sm:p-7 relative overflow-hidden">
        {/* Glow accent */}
        <div className="absolute -top-24 -right-24 w-48 h-48 bg-emerald-500/20 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -left-24 w-48 h-48 bg-teal-500/20 rounded-full blur-3xl pointer-events-none" />

        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-white p-1 rounded-lg hover:bg-forest-800/60 transition-colors"
        >
          <IconX className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400">
            <IconShield className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">
              {mode === 'login' ? 'EcoPulse AI Security Login' : 'Create Platform Account'}
            </h3>
            <p className="text-xs text-slate-400">
              {mode === 'login'
                ? 'Sign in to access protected environmental controls'
                : 'Register a new authenticated monitoring operator'}
            </p>
          </div>
        </div>

        {/* Quick Demo Logins */}
        <div className="mb-5 p-3 rounded-xl bg-forest-950/70 border border-emerald-500/20">
          <span className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider block mb-2">
            One-Click Test Profiles
          </span>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => handleQuickLogin('admin')}
              disabled={submitting}
              className="py-1.5 px-3 rounded-lg text-xs font-semibold bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40 transition-all flex items-center justify-center gap-1.5"
            >
              <span>Admin Profile</span>
              <span className="text-[10px] text-emerald-400/80 font-mono">(sarang)</span>
            </button>
            <button
              type="button"
              onClick={() => handleQuickLogin('analyst')}
              disabled={submitting}
              className="py-1.5 px-3 rounded-lg text-xs font-semibold bg-teal-500/20 hover:bg-teal-500/30 text-teal-300 border border-teal-500/40 transition-all flex items-center justify-center gap-1.5"
            >
              <span>Analyst Profile</span>
              <span className="text-[10px] text-teal-400/80 font-mono">(analyst)</span>
            </button>
          </div>
        </div>

        {/* Mode Toggle */}
        <div className="flex items-center bg-forest-950 p-1 rounded-xl border border-forest-800 mb-5 text-xs">
          <button
            type="button"
            onClick={() => {
              setMode('login');
              setAuthError(null);
            }}
            className={`flex-1 py-1.5 rounded-lg font-semibold transition-all ${
              mode === 'login'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => {
              setMode('register');
              setAuthError(null);
            }}
            className={`flex-1 py-1.5 rounded-lg font-semibold transition-all ${
              mode === 'register'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Register
          </button>
        </div>

        {/* Error / Success Notifications */}
        {authError && (
          <div className="mb-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
            <IconAlertTriangle className="w-4 h-4 shrink-0 text-rose-400" />
            <span>{authError}</span>
          </div>
        )}

        {successMessage && (
          <div className="mb-4 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2">
            <IconCheckCircle className="w-4 h-4 shrink-0 text-emerald-400" />
            <span>{successMessage}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-3.5">
          {mode === 'register' && (
            <>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Full Display Name</label>
                <div className="relative">
                  <IconUser className="w-4 h-4 text-emerald-400/80 absolute left-3 top-2.5" />
                  <input
                    type="text"
                    required
                    placeholder="e.g. Dr. Jane Smith"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 bg-forest-900/80 border border-forest-700 focus:border-emerald-500/60 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none transition-colors"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Email Address</label>
                <input
                  type="email"
                  required
                  placeholder="analyst@ecopulse.ai"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-3 py-2 bg-forest-900/80 border border-forest-700 focus:border-emerald-500/60 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none transition-colors"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Assigned Role</label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="w-full px-3 py-2 bg-forest-900/80 border border-forest-700 focus:border-emerald-500/60 rounded-xl text-xs text-white focus:outline-none transition-colors cursor-pointer"
                >
                  <option value="environmental_analyst">Environmental Analyst</option>
                  <option value="field_operator">Field Monitoring Operator</option>
                  <option value="admin">System Administrator</option>
                </select>
              </div>
            </>
          )}

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Username or Identifier</label>
            <div className="relative">
              <IconUser className="w-4 h-4 text-emerald-400/80 absolute left-3 top-2.5" />
              <input
                type="text"
                required
                placeholder={mode === 'login' ? 'Username or email' : 'Choose unique username'}
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full pl-9 pr-3 py-2 bg-forest-900/80 border border-forest-700 focus:border-emerald-500/60 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none transition-colors font-mono"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Password</label>
            <div className="relative">
              <IconLock className="w-4 h-4 text-emerald-400/80 absolute left-3 top-2.5" />
              <input
                type="password"
                required
                placeholder="••••••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-9 pr-3 py-2 bg-forest-900/80 border border-forest-700 focus:border-emerald-500/60 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none transition-colors"
              />
            </div>
            {mode === 'register' && (
              <span className="text-[10px] text-slate-400 mt-1 block">
                Must be at least 6 characters with secure bcrypt hashing.
              </span>
            )}
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full mt-4 py-2.5 px-4 rounded-xl font-bold text-xs bg-emerald-500 text-forest-950 hover:bg-emerald-400 disabled:opacity-50 transition-all shadow-lg shadow-emerald-500/20 flex items-center justify-center gap-2"
          >
            {submitting ? (
              <div className="w-4 h-4 border-2 border-forest-950 border-t-transparent rounded-full animate-spin" />
            ) : mode === 'login' ? (
              'Authenticate & Access Platform'
            ) : (
              'Register Account'
            )}
          </button>
        </form>
      </div>
    </div>
  );
};

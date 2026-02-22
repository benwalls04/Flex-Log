import { useState, useEffect, useRef } from 'react';
import { useApp } from '../context/AppContext';
import { useAuth } from '../context/AuthContext';
import WorkoutTab from '../components/WorkoutTab';
import LogsTab from '../components/LogsTab';

const TABS = [
  { id: 'workout', label: 'Workout' },
  { id: 'logs', label: 'Logs' },
];

function SettingsIcon({ className }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  );
}

export default function Main() {
  const [activeTab, setActiveTab] = useState('workout');
  const [settingsOpen, setSettingsOpen] = useState(false);
  const settingsRef = useRef(null);
  const { loadExercises, loadLogs } = useApp();
  const { signOut } = useAuth();

  useEffect(() => {
    loadExercises();
    loadLogs();
  }, [loadExercises, loadLogs]);

  useEffect(() => {
    function handleClickOutside(e) {
      if (settingsRef.current && !settingsRef.current.contains(e.target)) {
        setSettingsOpen(false);
      }
    }
    if (settingsOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [settingsOpen]);

  const handleSignOut = () => {
    setSettingsOpen(false);
    signOut();
    window.location.href = '/';
  };

  return (
    <div className="min-h-screen flex flex-col bg-[var(--color-background)]">
      <nav className="border-b border-border bg-surface sticky top-0 z-10">
        <div className="flex items-center justify-between gap-2 p-2">
          <div className="flex gap-1">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'bg-primary text-white'
                    : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
          <div className="relative" ref={settingsRef}>
            <button
              type="button"
              onClick={() => setSettingsOpen((o) => !o)}
              className="p-2 rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
              aria-label="Settings"
            >
              <SettingsIcon className="w-6 h-6" />
            </button>
            {settingsOpen && (
              <div className="absolute right-0 top-full mt-1 py-1 w-40 rounded-lg border border-border bg-surface shadow-lg z-20">
                <button
                  type="button"
                  onClick={handleSignOut}
                  className="w-full text-left px-4 py-2 text-sm text-foreground hover:bg-muted rounded-lg"
                >
                  Sign Out
                </button>
              </div>
            )}
          </div>
        </div>
      </nav>
      <main className="flex-1 overflow-auto p-4">
        {activeTab === 'workout' && <WorkoutTab />}
        {activeTab === 'logs' && <LogsTab />}
      </main>
    </div>
  );
}

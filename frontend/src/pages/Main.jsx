import { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import WorkoutTab from '../components/WorkoutTab';
import LogsTab from '../components/LogsTab';
import SettingsTab from '../components/SettingsTab';

const TABS = [
  { id: 'workout', label: 'Workout' },
  { id: 'logs', label: 'Logs' },
  { id: 'settings', label: 'Settings' },
];

export default function Main() {
  const [activeTab, setActiveTab] = useState('workout');
  const { loadExercises, loadLogs } = useApp();

  useEffect(() => {
    loadExercises();
    loadLogs();
  }, [loadExercises, loadLogs]);

  return (
    <div className="min-h-screen flex flex-col bg-[var(--color-background)]">
      <nav className="border-b border-border bg-surface sticky top-0 z-10">
        <div className="flex gap-1 p-2">
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
      </nav>
      <main className="flex-1 overflow-auto p-4">
        {activeTab === 'workout' && <WorkoutTab />}
        {activeTab === 'logs' && <LogsTab />}
        {activeTab === 'settings' && <SettingsTab />}
      </main>
    </div>
  );
}

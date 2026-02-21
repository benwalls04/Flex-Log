import { useAuth } from '../context/AuthContext';

export default function SettingsTab() {
  const { signOut } = useAuth();

  const handleSignOut = () => {
    signOut();
    window.location.href = '/';
  };

  return (
    <div className="max-w-md mx-auto space-y-6">
      <h2 className="text-xl font-semibold">Settings</h2>
      <section className="rounded-xl border border-border bg-surface p-4">
        <h3 className="text-sm font-medium text-muted-foreground mb-3">Account</h3>
        <button
          onClick={handleSignOut}
          className="rounded-lg bg-danger px-4 py-2 font-medium text-white hover:bg-danger-hover"
        >
          Sign Out
        </button>
      </section>
    </div>
  );
}

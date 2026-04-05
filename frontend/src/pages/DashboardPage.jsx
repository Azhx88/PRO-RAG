import { useState, useEffect } from 'react';
import Sidebar from '../components/layout/Sidebar';
import WorkspacePanel from '../components/workspace/WorkspacePanel';
import ChatWindow from '../components/chat/ChatWindow';
import { filesAPI } from '../api/client';

export default function DashboardPage() {
  const [files, setFiles] = useState([]);
  const [selectedWorkspace, setSelectedWorkspace] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const loadFiles = async () => {
    try {
      const res = await filesAPI.list();
      setFiles(res.data);
    } catch (e) {
      console.error('Failed to load files', e);
    }
  };

  useEffect(() => { loadFiles(); }, []);

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden', background: 'var(--bg-base)' }}>
      {/* Sidebar */}
      <Sidebar
        files={files}
        selectedWorkspace={selectedWorkspace}
        onSelectWorkspace={setSelectedWorkspace}
        onFilesChange={loadFiles}
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
      />

      {/* Main area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {selectedWorkspace ? (
          <ChatWindow workspace={selectedWorkspace} />
        ) : (
          <WorkspacePanel onFilesChange={loadFiles} onSelectWorkspace={setSelectedWorkspace} />
        )}
      </div>
    </div>
  );
}

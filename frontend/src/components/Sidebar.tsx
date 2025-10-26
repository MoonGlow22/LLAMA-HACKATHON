import { FileText, MessageSquare, Github, Briefcase } from 'lucide-react';
import { cn } from './utils';

interface SidebarProps {
  activeView: string;
  onNavigate: (view: string) => void;
}

const menuItems = [
  { id: 'cv', label: 'CV Score', icon: FileText },
  { id: 'githubprofile', label: 'GitHub Profile', icon: Github },
  { id: 'githubrepo', label: 'GitHub Repository', icon: Github },
  { id: 'chat', label: 'AI Assistant', icon: MessageSquare },
  { id: 'career', label: 'Career Dashboard', icon: Briefcase },
];

export function Sidebar({ activeView, onNavigate }: SidebarProps) {
  return (
    <aside className="w-64 bg-white border-r border-gray-200 min-h-[calc(100vh-73px)] p-4">
      <nav className="space-y-2">
        {menuItems.map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={cn(
                'w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors',
                activeView === item.id
                  ? 'bg-blue-50 text-blue-600'
                  : 'text-gray-700 hover:bg-gray-50'
              )}
            >
              <Icon className="h-5 w-5" />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>
    </aside>
  );
}

export default Sidebar;

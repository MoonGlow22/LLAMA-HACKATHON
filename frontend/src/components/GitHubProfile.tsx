import { useState } from 'react';
import { 
  Card, CardContent, CardHeader, CardTitle 
} from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Search, Github } from 'lucide-react';
import api from "./api";

export function GitHubProfile() {
  const [username, setUsername] = useState('');
  const [loading, setLoading] = useState(false);
  const [profileData, setProfileData] = useState<Record<string, string> | null>(null);

  const orderedKeys = [
    "user",
    "stats",
    "languages",
    "popular_repos",
    "profile_score",
    "ai_analysis",
    "learning_path",
    "course_metadata",
  ];

  const handleSearch = async () => {
    if (!username.trim()) {
      alert('Please enter a GitHub username.');
      return;
    }

    setLoading(true);
    setProfileData(null);

    try {
      const response = await api.post('/github/request', {
        link: username
      });
      setProfileData(response.data);
    } catch (error) {
      console.error('Error fetching GitHub data:', error);
      alert('Could not fetch GitHub data. Please check the username or server.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-gray-900 mb-1 text-xl font-semibold">GitHub Profile Analyzer</h1>
        <p className="text-gray-600">Fetch and display GitHub profile analysis from backend API</p>
      </div>

      {/* Search Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Github className="h-5 w-5" />
            Search GitHub Profile
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-3">
            <div className="flex-1">
              <Label htmlFor="username" className="sr-only">GitHub Username</Label>
              <Input
                id="username"
                placeholder="Enter GitHub username..."
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              />
            </div>
            <Button onClick={handleSearch} disabled={loading}>
              <Search className="h-4 w-4 mr-2" />
              {loading ? 'Loading...' : 'Analyze'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Response Sections (Always in fixed order) */}
      {profileData && (
        <div className="space-y-6">
          {orderedKeys.map((key) =>
            profileData[key] ? (
              <Card key={key}>
                <CardHeader>
                  <CardTitle className="text-lg capitalize">
                    {key.replace("_", " ")}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-700 whitespace-pre-wrap">{profileData[key]}</p>
                </CardContent>
              </Card>
            ) : null
          )}
        </div>
      )}
    </div>
  );
}

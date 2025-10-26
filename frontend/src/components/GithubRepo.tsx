import { useState } from 'react';
import { 
  Card, CardContent, CardHeader, CardTitle 
} from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Search, Github } from 'lucide-react';
import api from "./api";

export function GitHubRepo() {
  const [username, setUsername] = useState('');
  const [loading, setLoading] = useState(false);
  const [profileData, setProfileData] = useState<{ ai_report?: string; reco?: string } | null>(null);

  const handleSearch = async () => {
    if (!username.trim()) {
      alert('Please enter a GitHub repo link.');
      return;
    }

    setLoading(true);
    setProfileData(null);

    try {
      const response = await api.post('/github/request2', {
        link: username
      });
      setProfileData(response.data);
    } catch (error) {
      console.error('Error fetching GitHub data:', error);
      alert('Could not fetch GitHub data. Please check the repo link or server.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-gray-900 mb-1 text-xl font-semibold">GitHub Repo Analyzer</h1>
        <p className="text-gray-600">Fetch and display Repo AI Analysis from backend API</p>
      </div>

      {/* Search Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Github className="h-5 w-5" />
            Search GitHub Repo
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-3">
            <div className="flex-1">
              <Label htmlFor="username" className="sr-only">GitHub Repo Link</Label>
              <Input
                id="username"
                placeholder="Enter GitHub repo link..."
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

      {/* Response Section */}
      {profileData && (
        <div className="space-y-6">
          {/* AI Report Section */}
          {profileData.ai_report && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">AI Report</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">
                  {profileData.ai_report}
                </p>
              </CardContent>
            </Card>
          )}

          {/* Recommendations Section */}
          {profileData.reco && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Recommendations</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">
                  {profileData.reco}
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}

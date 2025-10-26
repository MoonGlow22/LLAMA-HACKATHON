// CVScore.tsx
import { useState } from "react";
import api from "./api";
import { Button } from "./ui/button";

interface CVAnalysisResult {
  short_summary: string;
  key_strength: string;
  weakness: string;
  jobs: string;
  suggests: string;
  ats: string;
  interview: string;
  questions: string;
  cv_score: string;
}

export function CVScore() {
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [result, setResult] = useState<CVAnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && file.type === "application/pdf") {
      setUploadedFile(file);
      setResult(null); // Yeni dosya yüklendiğinde önceki sonucu temizle
    } else {
      alert("Please upload a PDF file");
    }
  };

  const handleAnalyze = async () => {
    if (!uploadedFile) return;
    
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("file", uploadedFile);

      const response = await api.post<CVAnalysisResult>("/cv/cvextract", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      setResult(response.data);
    } catch (error) {
      console.error(error);
      alert("Error analyzing CV");
    } finally {
      setLoading(false);
    }
  };

  // Başlıkları daha okunabilir formata çeviren fonksiyon
  const formatTitle = (key: string): string => {
    const titles: { [key: string]: string } = {
      short_summary: "Short Summary",
      key_strength: "Key Strengths",
      weakness: "Weaknesses",
      jobs: "Suggested Job Roles",
      suggests: "Improvement Suggestions",
      ats: "ATS Keywords",
      interview: "Interview Preparation Tips",
      questions: "Potential Interview Questions",
      cv_score: "CV Score"
    };
    return titles[key] || key;
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col space-y-4">
        <input 
          type="file" 
          accept=".pdf" 
          onChange={handleFileChange}
          className="p-2 border rounded"
        />
        <Button 
          onClick={handleAnalyze} 
          disabled={!uploadedFile || loading}
          className="w-fit"
        >
          {loading ? "Analyzing..." : "Analyze CV"}
        </Button>
      </div>

      {result && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* CV Score - Özel olarak daha büyük göster */}
          {result.cv_score && (
            <div className="md:col-span-2">
              <div className="p-4 border-2 border-green-500 rounded-lg bg-green-50">
                <h3 className="text-lg font-bold text-green-800 mb-2">
                  {formatTitle("cv_score")}
                </h3>
                <p className="text-green-700">{result.cv_score}</p>
              </div>
            </div>
          )}

          {/* Diğer tüm alanlar */}
          {Object.entries(result)
            .filter(([key]) => key !== "cv_score")
            .map(([key, value]) => (
              <div 
                key={key}
                className="p-4 border rounded-lg bg-white shadow-sm hover:shadow-md transition-shadow"
              >
                <h3 className="font-semibold text-gray-800 mb-2">
                  {formatTitle(key)}
                </h3>
                <p className="text-gray-600 text-sm whitespace-pre-wrap">
                  {value}
                </p>
              </div>
            ))
          }
        </div>
      )}
    </div>
  );
}

export default CVScore;
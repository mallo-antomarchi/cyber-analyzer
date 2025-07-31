'use client'

import { useState } from 'react';

interface SecurityIssue {
  title: string;
  description: string;
  code: string;
  fix: string;
  cvss_score: number;
  severity: 'critical' | 'high' | 'medium' | 'low';
}

interface AnalysisResponse {
  summary: string;
  issues: SecurityIssue[];
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function Home() {
  const [codeContent, setCodeContent] = useState('');
  const [fileName, setFileName] = useState('');
  const [analysisResults, setAnalysisResults] = useState<AnalysisResponse | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && file.name.endsWith('.py')) {
      setFileName(file.name);
      const reader = new FileReader();
      reader.onload = (e) => {
        const content = e.target?.result as string;
        setCodeContent(content);
        setAnalysisResults(null);
        setError(null);
      };
      reader.readAsText(file);
    } else {
      alert('Please select a Python (.py) file');
    }
  };

  const handleAnalyzeCode = async () => {
    if (!codeContent) {
      alert('Please upload a Python file first');
      return;
    }

    setIsAnalyzing(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code: codeContent }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const results: AnalysisResponse = await response.json();
      setAnalysisResults(results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred during analysis');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'text-red-700 bg-red-100';
      case 'high': return 'text-orange-700 bg-orange-100';
      case 'medium': return 'text-yellow-700 bg-yellow-100';
      case 'low': return 'text-green-700 bg-green-100';
      default: return 'text-gray-700 bg-gray-100';
    }
  };

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto">
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-foreground">Cybersecurity Analyst</h1>
          <p className="text-accent mt-2">Python code analysis tool for security assessment</p>
        </header>

        <div className="grid grid-rows-2 gap-6 h-[calc(100vh-200px)]">
          {/* Upper Section - Code Input */}
          <div className="bg-white rounded-lg border border-border shadow-sm p-6 flex flex-col">
            <div className="flex items-center justify-between mb-4 flex-shrink-0">
              <label htmlFor="code-input" className="text-lg font-semibold text-foreground">
                Code to analyze
              </label>
              <div className="flex items-center gap-4">
                {fileName && (
                  <span className="text-sm text-accent bg-secondary/20 px-3 py-1 rounded-full">
                    {fileName}
                  </span>
                )}
                <input
                  type="file"
                  accept=".py"
                  onChange={handleFileUpload}
                  className="hidden"
                  id="file-upload"
                />
                <label
                  htmlFor="file-upload"
                  className="bg-primary hover:bg-primary/90 text-white px-4 py-2 rounded-lg cursor-pointer transition-colors font-medium"
                >
                  Open python file...
                </label>
                <button
                  onClick={handleAnalyzeCode}
                  disabled={!codeContent || isAnalyzing}
                  className="bg-accent hover:bg-accent/90 disabled:bg-gray-400 disabled:cursor-not-allowed text-white px-6 py-2 rounded-lg transition-colors font-medium"
                >
                  {isAnalyzing ? 'Analyzing...' : 'Analyze code'}
                </button>
              </div>
            </div>
            <textarea
              id="code-input"
              value={codeContent}
              readOnly
              placeholder="Select a Python file to display its contents here..."
              className="flex-1 w-full resize-none border border-border rounded-lg p-4 font-mono text-sm bg-input-bg focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
          </div>

          {/* Lower Section - Analysis Results */}
          <div className="bg-white rounded-lg border border-border shadow-sm p-6 flex flex-col">
            <h2 className="text-lg font-semibold text-foreground mb-4 flex-shrink-0">Results of Analysis</h2>
            <div className="flex-1 overflow-auto">
              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
                  <strong>Error:</strong> {error}
                </div>
              )}
              
              {!analysisResults && !error && (
                <div className="bg-gray-50 rounded-lg border border-border p-4 text-sm text-accent text-center">
                  {isAnalyzing ? 'Analyzing code...' : 'Upload and analyze Python code to see security assessment results here.'}
                </div>
              )}
              
              {analysisResults && (
                <div className="space-y-6">
                  {/* Summary */}
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h3 className="font-semibold text-blue-900 mb-2">Analysis Summary</h3>
                    <p className="text-blue-800 text-sm">{analysisResults.summary}</p>
                  </div>
                  
                  {/* Issues Table */}
                  {analysisResults.issues.length > 0 && (
                    <div className="border border-border rounded-lg overflow-hidden">
                      <div className="bg-gray-50 px-4 py-3 border-b border-border">
                        <h3 className="font-semibold text-foreground">Security Issues Found ({analysisResults.issues.length})</h3>
                      </div>
                      <div className="overflow-x-auto">
                        <table className="w-full">
                          <thead className="bg-gray-100">
                            <tr>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Issue</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Severity</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">CVSS</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Description</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Vulnerable Code</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Recommended Fix</th>
                            </tr>
                          </thead>
                          <tbody className="bg-white divide-y divide-gray-200">
                            {analysisResults.issues.map((issue, index) => (
                              <tr key={index} className="hover:bg-gray-50">
                                <td className="px-4 py-4 text-sm font-medium text-gray-900">{issue.title}</td>
                                <td className="px-4 py-4">
                                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getSeverityColor(issue.severity)}`}>
                                    {issue.severity.toUpperCase()}
                                  </span>
                                </td>
                                <td className="px-4 py-4 text-sm text-gray-900 font-mono">{issue.cvss_score}</td>
                                <td className="px-4 py-4 text-sm text-gray-700 max-w-xs">{issue.description}</td>
                                <td className="px-4 py-4 text-sm font-mono bg-gray-50 text-red-600 max-w-xs overflow-hidden">
                                  <pre className="whitespace-pre-wrap break-words">{issue.code}</pre>
                                </td>
                                <td className="px-4 py-4 text-sm font-mono bg-green-50 text-green-700 max-w-xs overflow-hidden">
                                  <pre className="whitespace-pre-wrap break-words">{issue.fix}</pre>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
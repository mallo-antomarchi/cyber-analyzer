'use client'

import { useState } from 'react';

export default function Home() {
  const [codeContent, setCodeContent] = useState('');
  const [fileName, setFileName] = useState('');

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && file.name.endsWith('.py')) {
      setFileName(file.name);
      const reader = new FileReader();
      reader.onload = (e) => {
        const content = e.target?.result as string;
        setCodeContent(content);
      };
      reader.readAsText(file);
    } else {
      alert('Please select a Python (.py) file');
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
            <div className="flex-1 bg-gray-50 rounded-lg border border-border p-4 text-sm text-accent overflow-auto">
              Analysis results will appear here...
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
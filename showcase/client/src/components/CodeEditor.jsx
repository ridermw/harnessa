import { useState, useRef, useEffect } from 'react';

export default function CodeEditor({ value, onChange, language }) {
  const textareaRef = useRef(null);
  const lineNumbersRef = useRef(null);

  const lines = (value || '').split('\n');
  const lineCount = Math.max(lines.length, 1);

  function handleScroll() {
    if (lineNumbersRef.current && textareaRef.current) {
      lineNumbersRef.current.scrollTop = textareaRef.current.scrollTop;
    }
  }

  return (
    <div className="flex rounded-lg border border-gray-700 bg-gray-900 overflow-hidden font-mono text-sm">
      <div
        ref={lineNumbersRef}
        className="flex-shrink-0 bg-gray-800/50 text-gray-500 text-right select-none overflow-hidden py-3 px-2"
        style={{ width: '3rem' }}
      >
        {Array.from({ length: lineCount }, (_, i) => (
          <div key={i} className="leading-6 h-6">
            {i + 1}
          </div>
        ))}
      </div>
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onScroll={handleScroll}
        className="flex-1 bg-transparent text-gray-100 p-3 outline-none resize-none leading-6 code-editor"
        placeholder={`Paste your ${language || 'code'} here...`}
        rows={Math.max(12, lineCount)}
        spellCheck={false}
      />
    </div>
  );
}

import React, { useMemo } from 'react';
import katex from 'katex';

interface LatexRendererProps {
  content: string;
  className?: string;
}

/**
 * Renders HTML + Markdown + Inline ($...$) and Display ($$...$$) LaTeX mathematics
 * using KaTeX with zero layout shift.
 */
export const LatexRenderer: React.FC<LatexRendererProps> = ({
  content,
  className = '',
}) => {
  const renderedHtml = useMemo(() => {
    if (!content) return '';

    let processed = content;

    // 1. Replace block math $$...$$ first
    processed = processed.replace(/\$\$([\s\S]*?)\$\$/g, (_, math) => {
      try {
        return katex.renderToString(math.trim(), {
          displayMode: true,
          throwOnError: false,
        });
      } catch {
        return `<code>${math}</code>`;
      }
    });

    // 2. Replace inline math $...$
    processed = processed.replace(/\$([^$\n]+?)\$/g, (_, math) => {
      try {
        return katex.renderToString(math.trim(), {
          displayMode: false,
          throwOnError: false,
        });
      } catch {
        return `<code>${math}</code>`;
      }
    });

    // 3. Light markdown formatting if plain text (headers, bold, newlines)
    if (!processed.includes('<p>') && !processed.includes('<div')) {
      processed = processed
        .replace(/^### (.*$)/gm, '<h4 class="font-bold text-sky-400 mt-2 mb-1">$1</h4>')
        .replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-white">$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n/g, '<br/>');
    }

    return processed;
  }, [content]);

  return (
    <div
      className={`latex-content leading-relaxed ${className}`}
      dangerouslySetInnerHTML={{ __html: renderedHtml }}
    />
  );
};

export default LatexRenderer;

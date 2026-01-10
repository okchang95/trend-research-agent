import { marked } from 'marked';

/**
 * HTML 이스케이프 처리
 */
export const escapeHtml = (text: string): string => {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
};

/**
 * 마크다운 코드 블록 백틱 짝 맞추기
 */
const fixMarkdownBackticks = (text: string): string => {
  if (!text || typeof text !== 'string') {
    return text || '';
  }
  
  let fixedText = text;
  
  // 코드 블록 백틱 짝 맞추기 (```로 시작했는데 닫히지 않은 경우)
  const matches = text.match(/```/g);
  if (matches) {
    const codeBlockCount = matches.length;
    // 홀수 개면 마지막 백틱 3개 추가
    if (codeBlockCount % 2 !== 0) {
      fixedText = text + '\n```';
    }
  }
  
  // 인라인 코드 백틱 짝 맞추기 (`로 시작했는데 닫히지 않은 경우)
  const inlineMatches = fixedText.match(/`/g);
  if (inlineMatches) {
    const inlineCount = inlineMatches.length;
    // 홀수 개면 마지막 백틱 추가
    if (inlineCount % 2 !== 0) {
      fixedText = fixedText + '`';
    }
  }
  
  return fixedText;
};

/**
 * 마크다운 파싱을 안전하게 수행하는 함수
 */
export const safeMarkdownParse = (text: string): string => {
  if (!text || typeof text !== 'string') {
    return '';
  }
  
  try {
    return marked.parse(text) as string;
  } catch (e) {
    console.warn('Markdown parsing failed, attempting to fix backticks:', e);
    // 파싱 실패 시 백틱 문제 수정 후 재시도
    try {
      const fixedText = fixMarkdownBackticks(text);
      return marked.parse(fixedText) as string;
    } catch (e2) {
      console.error('Markdown parsing failed even after fixing:', e2);
      // 그래도 실패하면 기본 텍스트로 표시
      return escapeHtml(text).replace(/\n/g, '<br>');
    }
  }
};

interface MermaidPlaceholder {
  placeholder: string;
  content: string;
}

/**
 * Mermaid 코드 블록을 플레이스홀더로 교체
 */
const processMermaidBlocks = (text: string): { processedText: string; placeholders: MermaidPlaceholder[] } => {
  if (!text || typeof text !== 'string') {
    return { processedText: text || '', placeholders: [] };
  }
  
  const mermaidPlaceholders: MermaidPlaceholder[] = [];
  const mermaidRegex = /```mermaid\s*\n([\s\S]*?)```/g;
  let index = 0;
  let processedText = text;
  
  let match;
  while ((match = mermaidRegex.exec(text)) !== null) {
    const placeholder = `__MERMAID_PLACEHOLDER_${index}__`;
    mermaidPlaceholders.push({
      placeholder: placeholder,
      content: match[1].trim()
    });
    processedText = processedText.replace(match[0], placeholder);
    index++;
  }
  
  return { processedText, placeholders: mermaidPlaceholders };
};

/**
 * 플레이스홀더를 실제 Mermaid div로 교체
 */
const replaceMermaidPlaceholders = (html: string, placeholders: MermaidPlaceholder[]): string => {
  if (!placeholders || placeholders.length === 0) {
    return html;
  }
  
  let result = html;
  placeholders.forEach((item) => {
    const mermaidDiv = `<div class="mermaid">${item.content}</div>`;
    result = result.replace(item.placeholder, mermaidDiv);
  });
  
  return result;
};

/**
 * 텍스트를 마크다운으로 변환하고 Mermaid를 처리
 */
export const processMarkdownWithMermaid = (text: string): string => {
  const { processedText, placeholders } = processMermaidBlocks(text);
  let html = safeMarkdownParse(processedText);
  html = replaceMermaidPlaceholders(html, placeholders);
  return html;
};

/**
 * Mermaid 다이어그램 렌더링
 */
export const renderMermaidDiagrams = async (container: HTMLElement): Promise<void> => {
  if (typeof window === 'undefined') return;
  
  try {
    const mermaid = (window as any).mermaid;
    if (!mermaid) return;
    
    mermaid.initialize({ startOnLoad: false, theme: 'default' });
    const mermaidDiagrams = container.querySelectorAll<HTMLElement>('.mermaid');
    
    for (const diagram of Array.from(mermaidDiagrams)) {
      if (!diagram.hasAttribute('data-processed')) {
        await mermaid.run({ nodes: [diagram] });
      }
    }
  } catch (e) {
    console.error('Mermaid rendering error:', e);
  }
};

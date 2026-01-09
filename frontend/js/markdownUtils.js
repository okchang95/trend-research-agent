/**
 * 마크다운 및 Mermaid 처리 유틸리티
 */

/**
 * HTML 이스케이프 처리
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * 마크다운 코드 블록 백틱 짝 맞추기
 */
function fixMarkdownBackticks(text) {
    if (!text || typeof text !== 'string') {
        return text || '';
    }
    
    // 코드 블록 백틱 짝 맞추기 (```로 시작했는데 닫히지 않은 경우)
    const codeBlockRegex = /```[\s\S]*?/g;
    let codeBlockCount = 0;
    let fixedText = text;
    
    // 모든 코드 블록 시작/끝 찾기
    const matches = text.match(/```/g);
    if (matches) {
        codeBlockCount = matches.length;
        // 홀수 개면 마지막 백틱 3개 추가
        if (codeBlockCount % 2 !== 0) {
            fixedText = text + '\n```';
        }
    }
    
    // 인라인 코드 백틱 짝 맞추기 (`로 시작했는데 닫히지 않은 경우)
    const inlineCodeRegex = /`/g;
    const inlineMatches = fixedText.match(inlineCodeRegex);
    if (inlineMatches) {
        const inlineCount = inlineMatches.length;
        // 홀수 개면 마지막 백틱 추가
        if (inlineCount % 2 !== 0) {
            fixedText = fixedText + '`';
        }
    }
    
    return fixedText;
}

/**
 * 마크다운 파싱을 안전하게 수행하는 함수
 */
function safeMarkdownParse(text) {
    if (!text || typeof text !== 'string') {
        return '';
    }
    
    try {
        if (typeof marked === 'undefined') {
            // marked가 없으면 기본 이스케이프 처리
            return escapeHtml(text).replace(/\n/g, '<br>');
        }
        
        return marked.parse(text);
    } catch (e) {
        console.warn('Markdown parsing failed, attempting to fix backticks:', e);
        // 파싱 실패 시 백틱 문제 수정 후 재시도
        try {
            const fixedText = fixMarkdownBackticks(text);
            return marked.parse(fixedText);
        } catch (e2) {
            console.error('Markdown parsing failed even after fixing:', e2);
            // 그래도 실패하면 기본 텍스트로 표시
            return escapeHtml(text).replace(/\n/g, '<br>');
        }
    }
}

/**
 * Mermaid 코드 블록을 플레이스홀더로 교체하고 실제 Mermaid div로 변환
 */
function processMermaidBlocks(text) {
    if (!text || typeof text !== 'string') {
        return { processedText: text || '', placeholders: [] };
    }
    
    if (typeof mermaid === 'undefined') {
        return { processedText: text, placeholders: [] };
    }
    
    const mermaidPlaceholders = [];
    const mermaidRegex = /```mermaid\s*\n([\s\S]*?)```/g;
    let match;
    let index = 0;
    let processedText = text;
    
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
}

/**
 * 플레이스홀더를 실제 Mermaid div로 교체
 */
function replaceMermaidPlaceholders(html, placeholders) {
    if (!placeholders || placeholders.length === 0) {
        return html;
    }
    
    if (typeof mermaid === 'undefined') {
        return html;
    }
    
    let result = html;
    placeholders.forEach((item) => {
        const mermaidDiv = `<div class="mermaid">${item.content}</div>`;
        result = result.replace(item.placeholder, mermaidDiv);
    });
    
    return result;
}

/**
 * Mermaid 다이어그램 렌더링
 */
function renderMermaidDiagrams(container) {
    if (typeof mermaid === 'undefined') {
        return;
    }
    
    try {
        mermaid.initialize({ startOnLoad: false, theme: 'default' });
        const mermaidDiagrams = container.querySelectorAll('.mermaid');
        mermaidDiagrams.forEach((diagram) => {
            if (!diagram.hasAttribute('data-processed')) {
                mermaid.run({ nodes: [diagram] });
            }
        });
    } catch (e) {
        console.error('Mermaid rendering error:', e);
    }
}

/**
 * 텍스트를 마크다운으로 변환하고 Mermaid를 처리
 */
function processMarkdownWithMermaid(text) {
    const { processedText, placeholders } = processMermaidBlocks(text);
    let html = safeMarkdownParse(processedText);
    html = replaceMermaidPlaceholders(html, placeholders);
    return html;
}

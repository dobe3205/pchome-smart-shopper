// DOM 載入完成
document.addEventListener('DOMContentLoaded', function() {
    // 綁定按鈕事件
    document.getElementById('clearBtn').addEventListener('click', clearInput);
    document.getElementById('submitBtn').addEventListener('click', sendQuestion);
    
    // 輸入框按鍵事件
    document.getElementById('queryInput').addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendQuestion();
        }
    });
    
    // 範例查詢點擊事件
    document.querySelectorAll('.example-query').forEach(item => {
        item.addEventListener('click', function() {
            useExample(this);
        });
    });
});

// 使用查詢範例
function useExample(element) {
    document.getElementById('queryInput').value = element.textContent;
    document.getElementById('queryInput').focus();
}

// 清除輸入框內容
function clearInput() {
    document.getElementById('queryInput').value = '';
    document.getElementById('queryInput').focus();
}

// 顯示載入動畫
function showLoading() {
    const resultDiv = document.getElementById('result');
    resultDiv.innerHTML = `
        <div class="loading-container">
            <div class="loading-spinner"></div>
            <div class="loading-text">正在搜尋和分析商品資訊</div>
            <div class="loading-subtext">這可能需要 15-30 秒的時間，請耐心等待</div>
        </div>
    `;
    resultDiv.classList.add('active');
}

// 顯示錯誤訊息
function showError(message) {
    const resultDiv = document.getElementById('result');
    resultDiv.innerHTML = `
        <div class="error">
            <i class="fas fa-exclamation-circle"></i>
            <div>
                <strong>處理請求時發生錯誤：</strong><br>
                ${message}
            </div>
        </div>
    `;
    resultDiv.classList.add('active');
}

// 修復垂直條表格格式
function fixTableFormat(text) {
    // 檢測是否包含垂直條表格格式 (使用 | 符號分隔的表格)
    if (text.includes('|') && text.includes('|-')) {
        // 獲取所有可能的表格行
        const lines = text.split('\n');
        let tableStartIndex = -1;
        let tableEndIndex = -1;
        
        // 尋找表格的開始和結束
        for (let i = 0; i < lines.length; i++) {
            if (lines[i].trim().startsWith('|') && lines[i].trim().endsWith('|')) {
                if (tableStartIndex === -1) {
                    tableStartIndex = i;
                }
                tableEndIndex = i;
            } else if (tableStartIndex !== -1 && tableEndIndex !== -1 && !lines[i].trim().startsWith('|')) {
                break;
            }
        }
        
        // 如果找到了表格
        if (tableStartIndex !== -1 && tableEndIndex !== -1) {
            const tableLines = lines.slice(tableStartIndex, tableEndIndex + 1);
            const headerLine = tableLines[0];
            const separatorLine = tableLines.find(line => line.includes('|-'));
            
            // 從標題行提取列標題
            const headers = headerLine.split('|')
                .filter(cell => cell.trim() !== '')
                .map(cell => cell.trim());
                
            // 準備HTML表格 - 增加表格大小
            let htmlTable = '<table style="width:100%; border-collapse:collapse; margin:20px 0; font-size:1.05rem;">';
            
            // 添加表格標題
            htmlTable += '<thead><tr>';
            headers.forEach(header => {
                htmlTable += `<th style="background-color:#f0f7ff; padding:12px; border:1px solid #ccc; font-weight:bold;">${header}</th>`;
            });
            htmlTable += '</tr></thead>';
            
            // 添加表格內容
            htmlTable += '<tbody>';
            for (let i = 1; i < tableLines.length; i++) {
                // 跳過分隔線
                if (tableLines[i].includes('|-')) continue;
                
                const cells = tableLines[i].split('|')
                    .filter(cell => cell.trim() !== '')
                    .map(cell => cell.trim());
                
                if (cells.length > 0) {
                    htmlTable += '<tr>';
                    cells.forEach(cell => {
                        htmlTable += `<td style="padding:12px; border:1px solid #ccc;">${cell}</td>`;
                    });
                    htmlTable += '</tr>';
                }
            }
            htmlTable += '</tbody></table>';
            
            // 替換原始文本中的表格
            const originalTable = lines.slice(tableStartIndex, tableEndIndex + 1).join('\n');
            text = text.replace(originalTable, htmlTable);
        }
    }
    
    return text;
}

// 表格
function fixListFormat(text) {
    // 處理優缺點分析區域
    text = text.replace(/\*\s+\*\*(.*?)\*\*\s*:\s*\*\s+(優點|缺點)：(.*?)\s*\*\s+(優點|缺點)：(.*?)(?=\*\s+\*\*|\n\n|$)/gs, function(match, title, type1, content1, type2, content2) {
        return `
        <div style="margin:20px 0; padding:15px; background:#f9f9f9; border-radius:8px;">
            <h3 style="margin-bottom:10px; color:#333;">${title}</h3>
            <div style="margin-bottom:8px;">
                <strong style="color:#38a169;">✓ ${type1}：</strong> ${content1}
            </div>
            <div>
                <strong style="color:#e53e3e;">✗ ${type2}：</strong> ${content2}
            </div>
        </div>
        `;
    });
    
    // 處理編號列表 (1. 2. 3. ...)
    text = text.replace(/(\d+)\.\s+(.*?):\s*\n([\s\S]*?)(?=\d+\.\s+|\n\n|$)/g, function(match, number, title, content) {
        return `
        <div style="margin:20px 0;">
            <h3 style="margin-bottom:10px; color:#333;"><span style="display:inline-block; width:25px; height:25px; line-height:25px; text-align:center; background:#1f60aa; color:white; border-radius:50%; margin-right:8px;">${number}</span>${title}</h3>
            <div style="margin-left:33px;">${content}</div>
        </div>
        `;
    });
    
    // 處理推薦列表
    text = text.replace(/\*\s+\*\*(.*?選擇)：\*\*(.*?)(?=\*\s+\*\*|\n\n|$)/g, function(match, type, content) {
        let icon = '⭐';
        let color = '#f6ad55';
        
        if (type.includes('CP值')) {
            icon = '💰';
            color = '#38a169';
        } else if (type.includes('特定用途')) {
            icon = '🎯';
            color = '#3182ce';
        }
        
        return `
        <div style="margin:10px 0; padding:10px; background:#f0f7ff; border-radius:8px; border-left:4px solid ${color};">
            <div style="font-weight:bold; margin-bottom:5px;">
                <span style="margin-right:5px;">${icon}</span> ${type}：
            </div>
            <div style="margin-left:25px;">${content}</div>
        </div>
        `;
    });
    
    // 處理帶星號的項目列表
    text = text.replace(/\*\s+(.*?)(?=\*\s+|\n\n|$)/g, '<div style="margin:8px 0;"><span style="display:inline-block; margin-right:8px; color:#1f60aa;">•</span>$1</div>');
    
    return text;
}

// 增強回應的基本格式化
function enhanceResponse(text) {
    // 處理強調的內容
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong style="color:#1f60aa;">$1</strong>');
    
    // 處理重要的價格資訊
    text = text.replace(/(\$\s*[\d,]+|NT\$\s*[\d,]+)/g, '<span style="color:#e53e3e;font-weight:bold">$1</span>');
    
    // 修復表格格式
    text = fixTableFormat(text);
    
    // 修復列表格式
    text = fixListFormat(text);
    
    // 處理章節標題
    text = text.replace(/(\d+)\.\s+(.*?):/g, '<h3 style="margin:20px 0 10px 0; padding-bottom:5px; border-bottom:1px solid #eee; color:#1f60aa;">$1. $2</h3>');
    
    // 處理購買連結 - 更大更醒目的樣式
    text = text.replace(/(https:\/\/24h\.pchome\.com\.tw\/[^\s<]+)/g, '<a href="$1" target="_blank" style="display:inline-block; background-color:#ec6618; color:white; padding:5px 12px; border-radius:4px; text-decoration:none; font-weight:bold; margin:5px 0;"><i class="fas fa-shopping-cart" style="margin-right:5px;"></i>查看商品</a>');
    
    return text;
}

// 發送查詢請求
async function sendQuestion() {
    const query = document.getElementById('queryInput').value;
    
    if (!query.trim()) {
        alert('請輸入商品需求或比較問題');
        return;
    }
    
    // 顯示載入動畫
    showLoading();
    
    try {
        const response = await fetch('/respone', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({"content": query })
        });
        
        const data = await response.json();
        
        if (data.error) {
            showError(data.error);
            return;
        }
        
        // 增強回應內容
        let enhancedResponse = enhanceResponse(data.respone);
        
        // 將回應顯示在結果區域
        const resultDiv = document.getElementById('result');
        resultDiv.innerHTML = `
            <div class="result-question">
                <strong><i class="fas fa-search"></i> 您的需求：</strong> ${query}
            </div>
            <div class="result-answer">${enhancedResponse}</div>
        `;
        resultDiv.classList.add('active');
        
        // 滾動到結果區域
        resultDiv.scrollIntoView({ behavior: 'smooth' });
        
    } catch (error) {
        console.error('錯誤:', error);
        showError(error.message);
    }
}

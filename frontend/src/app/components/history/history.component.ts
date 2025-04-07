import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { HistoryService } from '../../services/history.service';
import { MessageService } from '../../services/message/message.service';
import { LoadingSpinnerComponent } from '../shared/loading-spinner/loading-spinner.component';

@Component({
  selector: 'app-history',
  standalone: true,
  imports: [CommonModule, RouterModule, LoadingSpinnerComponent],
  templateUrl: './history.component.html',
  styleUrls: ['./history.component.css']
})
export class HistoryComponent implements OnInit {
  queryHistory: any[] = [];
  selectedQuery: any = null;
  parsedResponse: any = null;
  totalRecords: number = 0;
  currentPage: number = 0;
  pageSize: number = 10;
  isLoading: boolean = false;
  errorMessage: string = '';

  constructor(
    private historyService: HistoryService,
    private messageService: MessageService
  ) {}

  ngOnInit() {
    this.loadHistory();
  }

  loadHistory(page: number = 0) {
    this.isLoading = true;
    this.errorMessage = '';
    
    this.historyService.getQueryHistory(page * this.pageSize, this.pageSize).subscribe({
      next: (response) => {
        this.queryHistory = response.records;
        this.totalRecords = response.total;
        this.currentPage = page;
        this.isLoading = false;
        
        // 如果這是第一頁且有記錄，自動選擇第一條
        if (page === 0 && this.queryHistory.length > 0 && !this.selectedQuery) {
          this.viewQueryDetails(this.queryHistory[0]);
        }

        if (this.queryHistory.length === 0) {
          this.messageService.info('您還沒有任何查詢記錄');
        }
      },
      error: (error) => {
        this.errorMessage = error.message || '無法載入查詢歷史';
        this.messageService.error(this.errorMessage);
        this.isLoading = false;
      }
    });
  }

  viewQueryDetails(query: any) {
    this.selectedQuery = query;
    
    try {
      // 處理回應格式
      // 檢查response是否已經是JSON對象
      if (typeof query.response === 'object') {
        this.parsedResponse = query.response;
      } 
      // 如果是字符串，嘗試解析
      else if (typeof query.response === 'string') {
        // 檢查是否包含markdown格式的json
        if (query.response.includes('```json')) {
          // 從 markdown 代碼塊中提取 JSON
          const jsonStart = query.response.indexOf('```json') + 7;
          const jsonEnd = query.response.indexOf('```', jsonStart);
          const jsonString = query.response.substring(jsonStart, jsonEnd).trim();
          this.parsedResponse = JSON.parse(jsonString);
        } else {
          // 直接嘗試解析整個回應
          this.parsedResponse = JSON.parse(query.response);
        }
      } else {
        throw new Error('無法識別的回應格式');
      }
    } catch (e) {
      console.error('解析回應時出錯:', e);
      this.parsedResponse = null;
      this.messageService.warning('無法解析此查詢回應的詳細資訊');
    }
  }

  deleteQuery(event: Event, queryId: number) {
    event.stopPropagation();
    
    if (confirm('確定要刪除這條查詢記錄嗎？')) {
      this.historyService.deleteQuery(queryId).subscribe({
        next: () => {
          // 從列表中移除已刪除的查詢
          this.queryHistory = this.queryHistory.filter(q => q.id !== queryId);
          this.messageService.success('已刪除查詢記錄');
          
          // 如果刪除的是當前選中的查詢，重置選中狀態
          if (this.selectedQuery && this.selectedQuery.id === queryId) {
            this.selectedQuery = null;
            this.parsedResponse = null;
            
            // 如果還有其他查詢，選擇第一條
            if (this.queryHistory.length > 0) {
              this.viewQueryDetails(this.queryHistory[0]);
            }
          }
          
          // 更新總記錄數
          this.totalRecords--;
          
          // 如果當前頁已空且不是第一頁，加載上一頁
          if (this.queryHistory.length === 0 && this.currentPage > 0) {
            this.loadHistory(this.currentPage - 1);
          }
        },
        error: (error) => {
          this.errorMessage = error.message || '刪除查詢失敗';
          this.messageService.error(this.errorMessage);
        }
      });
    }
  }

  changePage(newPage: number) {
    if (newPage >= 0 && newPage * this.pageSize < this.totalRecords) {
      this.loadHistory(newPage);
    }
  }

  get totalPages(): number {
    return Math.ceil(this.totalRecords / this.pageSize);
  }
  
  formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleString('zh-TW', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  truncateText(text: string, maxLength: number = 50): string {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  }
}

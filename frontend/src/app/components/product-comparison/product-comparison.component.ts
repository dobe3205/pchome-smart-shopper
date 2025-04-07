import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ProductService } from '../../services/product.service';
import { MessageService } from '../../services/message/message.service';
import { LoadingSpinnerComponent } from '../shared/loading-spinner/loading-spinner.component';

@Component({
  selector: 'app-product-comparison',
  standalone: true,
  imports: [CommonModule, FormsModule, LoadingSpinnerComponent],
  templateUrl: './product-comparison.component.html',
  styleUrls: ['./product-comparison.component.css']
})
export class ProductComparisonComponent {
  query: string = '';
  comparisonResults: any = null;
  errorMessage: string = '';
  isLoading: boolean = false;
  showExamples: boolean = true;
  queryExamples: string[] = [
    '我想買一台2萬元以內，螢幕至少15吋的筆電，主要用於文書處理和看影片',
    '推薦一台適合小家庭使用的智能冰箱，預算3萬元以內'
  ];

  constructor(
    private productService: ProductService,
    private messageService: MessageService
  ) {}

  submitQuery() {
    if (!this.query.trim()) {
      this.messageService.warning('請輸入查詢內容');
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';
    this.comparisonResults = null;
    this.showExamples = false;

    this.productService.compareProducts(this.query).subscribe({
      next: (response) => {
        // 後端現在直接返回JSON，不需要字符串解析
        this.comparisonResults = response;
        this.isLoading = false;
        this.messageService.success('查詢成功');
      },
      error: (error) => {
        this.errorMessage = error.message || '查詢處理時發生錯誤';
        this.messageService.error(this.errorMessage);
        this.isLoading = false;
      }
    });
  }

  useExample(example: string) {
    this.query = example;
    this.submitQuery();
  }

  resetComparison() {
    this.query = '';
    this.comparisonResults = null;
    this.errorMessage = '';
    this.showExamples = true;
  }
}

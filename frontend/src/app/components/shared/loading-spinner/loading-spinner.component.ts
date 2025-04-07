import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-loading-spinner',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="spinner-container" [class.overlay]="overlay" [class.inline]="!overlay">
      <div class="spinner" [style.width.px]="size" [style.height.px]="size"></div>
      <div class="spinner-text" *ngIf="message">{{ message }}</div>
    </div>
  `,
  styles: [`
    .spinner-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
    }
    
    .spinner-container.overlay {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background-color: rgba(255, 255, 255, 0.7);
      z-index: 9999;
    }
    
    .spinner-container.inline {
      padding: 1rem;
    }
    
    .spinner {
      border: 3px solid rgba(0, 0, 0, 0.1);
      border-radius: 50%;
      border-top: 3px solid #1a73e8;
      width: 30px;
      height: 30px;
      animation: spin 1s linear infinite;
    }
    
    .spinner-text {
      margin-top: 1rem;
      color: #5f6368;
      font-weight: 500;
    }
    
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
  `]
})
export class LoadingSpinnerComponent {
  @Input() overlay: boolean = false;
  @Input() message: string = '';
  @Input() size: number = 30;
}

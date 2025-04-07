import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MessageService, Message, MessageType } from '../../../services/message/message.service';
import { Subscription, timer } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Component({
  selector: 'app-message',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="message-container" *ngIf="messages.length > 0">
      <div 
        *ngFor="let message of messages"
        class="message"
        [class.success]="message.type === 'success'"
        [class.error]="message.type === 'error'"
        [class.info]="message.type === 'info'"
        [class.warning]="message.type === 'warning'"
      >
        <div class="message-content">
          <div class="message-icon">
            <span *ngIf="message.type === 'success'">✓</span>
            <span *ngIf="message.type === 'error'">✕</span>
            <span *ngIf="message.type === 'info'">ℹ</span>
            <span *ngIf="message.type === 'warning'">⚠</span>
          </div>
          <div class="message-text">{{ message.text }}</div>
        </div>
        <button class="close-button" (click)="removeMessage(message.id!)">✕</button>
      </div>
    </div>
  `,
  styles: [`
    .message-container {
      position: fixed;
      top: 20px;
      right: 20px;
      z-index: 10000;
      max-width: 350px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    
    .message {
      padding: 12px 16px;
      border-radius: 4px;
      box-shadow: 0 3px 6px rgba(0, 0, 0, 0.16);
      display: flex;
      justify-content: space-between;
      align-items: center;
      animation: slide-in 0.3s ease-out;
    }
    
    .message.success {
      background-color: #e6f4ea;
      border-left: 4px solid #0f9d58;
    }
    
    .message.error {
      background-color: #fce8e6;
      border-left: 4px solid #d93025;
    }
    
    .message.info {
      background-color: #e8f0fe;
      border-left: 4px solid #1a73e8;
    }
    
    .message.warning {
      background-color: #fef7e0;
      border-left: 4px solid #f9ab00;
    }
    
    .message-content {
      display: flex;
      align-items: center;
      flex: 1;
    }
    
    .message-icon {
      margin-right: 12px;
      font-size: 18px;
    }
    
    .message.success .message-icon {
      color: #0f9d58;
    }
    
    .message.error .message-icon {
      color: #d93025;
    }
    
    .message.info .message-icon {
      color: #1a73e8;
    }
    
    .message.warning .message-icon {
      color: #f9ab00;
    }
    
    .message-text {
      font-size: 14px;
    }
    
    .close-button {
      background: transparent;
      border: none;
      color: #5f6368;
      cursor: pointer;
      font-size: 14px;
      margin-left: 10px;
      padding: 4px;
    }
    
    .close-button:hover {
      color: #202124;
    }
    
    @keyframes slide-in {
      from {
        transform: translateX(100%);
        opacity: 0;
      }
      to {
        transform: translateX(0);
        opacity: 1;
      }
    }
    
    @keyframes slide-out {
      from {
        transform: translateX(0);
        opacity: 1;
      }
      to {
        transform: translateX(100%);
        opacity: 0;
      }
    }
  `]
})
export class MessageComponent implements OnInit, OnDestroy {
  messages: Message[] = [];
  private subscription = new Subscription();

  constructor(private messageService: MessageService) { }

  ngOnInit(): void {
    this.subscription.add(
      this.messageService.messages$.subscribe(message => {
        this.addMessage(message);
      })
    );
  }

  ngOnDestroy(): void {
    this.subscription.unsubscribe();
  }

  private addMessage(message: Message): void {
    // 添加消息到數組
    this.messages.push(message);
    
    // 如果設置了持續時間，則定時移除消息
    if (message.duration && message.duration > 0) {
      timer(message.duration)
        .subscribe(() => {
          this.removeMessage(message.id!);
        });
    }
  }

  removeMessage(id: number): void {
    const index = this.messages.findIndex(m => m.id === id);
    if (index !== -1) {
      this.messages.splice(index, 1);
    }
  }
}

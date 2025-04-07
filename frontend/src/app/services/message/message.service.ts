import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, Subject } from 'rxjs';

export enum MessageType {
  Success = 'success',
  Error = 'error',
  Info = 'info',
  Warning = 'warning'
}

export interface Message {
  type: MessageType;
  text: string;
  duration?: number;
  id?: number;
}

@Injectable({
  providedIn: 'root'
})
export class MessageService {
  private messageSubject = new Subject<Message>();
  private messageCounter = 0;

  messages$ = this.messageSubject.asObservable();

  constructor() { }

  // 顯示成功訊息
  success(text: string, duration: number = 5000): number {
    return this.show({
      type: MessageType.Success,
      text,
      duration
    });
  }

  // 顯示錯誤訊息
  error(text: string, duration: number = 5000): number {
    return this.show({
      type: MessageType.Error,
      text,
      duration
    });
  }

  // 顯示資訊訊息
  info(text: string, duration: number = 5000): number {
    return this.show({
      type: MessageType.Info,
      text,
      duration
    });
  }

  // 顯示警告訊息
  warning(text: string, duration: number = 5000): number {
    return this.show({
      type: MessageType.Warning,
      text,
      duration
    });
  }

  // 顯示訊息
  private show(message: Message): number {
    const id = ++this.messageCounter;
    this.messageSubject.next({
      ...message,
      id
    });
    return id;
  }

  // 清除訊息
  clear(id: number): void {
    // 這個方法將與訊息顯示組件一起使用
    // 在訊息顯示組件中實現清除邏輯
  }
}

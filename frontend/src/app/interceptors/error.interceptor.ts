import { Injectable } from '@angular/core';
import {
  HttpRequest,
  HttpHandler,
  HttpEvent,
  HttpInterceptor,
  HttpErrorResponse
} from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { Router } from '@angular/router';

@Injectable()
export class ErrorInterceptor implements HttpInterceptor {

  constructor(private router: Router) {}

  intercept(request: HttpRequest<unknown>, next: HttpHandler): Observable<HttpEvent<unknown>> {
    return next.handle(request).pipe(
      catchError((error: HttpErrorResponse) => {
        console.error('API 錯誤:', error);
        
        if (error.status === 0) {
          // 網路錯誤或後端服務未啟動
          console.error('無法連接到後端服務。請確保後端服務已啟動。');
        } else if (error.status === 401) {
          // 未授權 - 登入失敗或 token 過期
          if (!request.url.includes('/api/token')) {
            // 如果不是登入請求，則重新導向到登入頁面
            localStorage.removeItem('auth_token');
            localStorage.removeItem('token_type');
            this.router.navigate(['/login'], {
              queryParams: { returnUrl: this.router.url }
            });
          }
        } else if (error.status === 403) {
          // 禁止訪問 - 權限不足
          console.error('您沒有權限訪問此資源');
        } else if (error.status === 404) {
          // 資源不存在
          console.error('請求的資源不存在');
        } else if (error.status === 500) {
          // 伺服器錯誤
          console.error('伺服器內部錯誤');
        }
        
        // 將錯誤傳遞給組件處理
        return throwError(() => error);
      })
    );
  }
}

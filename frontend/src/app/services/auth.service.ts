import { Injectable, PLATFORM_ID, Inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, BehaviorSubject, throwError, of } from 'rxjs';
import { catchError, tap, finalize } from 'rxjs/operators';
import { Router } from '@angular/router';
import { isPlatformBrowser } from '@angular/common';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = 'http://localhost:8000';  // 改為正確的API路徑
  private currentUserSubject = new BehaviorSubject<any>(null);
  public currentUser$ = this.currentUserSubject.asObservable();
  private tokenKey = 'auth_token';
  private tokenTypeKey = 'token_type';
  private isBrowser: boolean;

  constructor(
    private http: HttpClient,
    private router: Router,
    @Inject(PLATFORM_ID) platformId: Object
  ) {
    this.isBrowser = isPlatformBrowser(platformId);
    if (this.isBrowser) {
      this.loadStoredUser();
    }
  }

  private loadStoredUser() {
    if (this.isBrowser) {
      const token = localStorage.getItem(this.tokenKey);
      if (token) {
        this.fetchCurrentUser().subscribe();
      }
    }
  }

  register(userData: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/api/register`, userData)
      .pipe(
        catchError(this.handleError)
      );
  }

  login(username: string, password: string): Observable<any> {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);

    return this.http.post(`${this.apiUrl}/api/token`, formData)
      .pipe(
        tap(response => this.handleAuth(response)),
        catchError(this.handleError)
      );
  }

  private handleAuth(response: any) {
    if (response && response.access_token && this.isBrowser) {
      localStorage.setItem(this.tokenKey, response.access_token);
      localStorage.setItem(this.tokenTypeKey, response.token_type);
      this.fetchCurrentUser().subscribe();
    }
  }

  fetchCurrentUser(): Observable<any> {
    if (!this.isBrowser || !this.getToken()) {
      return of(null);
    }
    
    return this.http.get(`${this.apiUrl}/users/me`, { headers: this.getAuthHeaders() })
      .pipe(
        tap(user => {
          this.currentUserSubject.next(user);
        }),
        catchError(error => {
          this.logout();
          return throwError(() => error);
        })
      );
  }

  logout(): Observable<any> {
    // 只有在用戶登入狀態下才呼叫登出 API
    if (this.isBrowser && this.getToken()) {
      return this.http.post(`${this.apiUrl}/api/logout`, {}, { headers: this.getAuthHeaders() })
        .pipe(
          finalize(() => {
            // 無論 API 呼叫成功與否，都執行本地登出操作
            if (this.isBrowser) {
              localStorage.removeItem(this.tokenKey);
              localStorage.removeItem(this.tokenTypeKey);
            }
            this.currentUserSubject.next(null);
            this.router.navigate(['/login']);
          }),
          catchError(error => {
            console.error('Logout API error:', error);
            // 即使 API 呼叫失敗，仍然完成本地登出
            return of(null);
          })
        );
    } else {
      // 如果用戶沒有登入，則只在本地處理
      if (this.isBrowser) {
        localStorage.removeItem(this.tokenKey);
        localStorage.removeItem(this.tokenTypeKey);
      }
      this.currentUserSubject.next(null);
      this.router.navigate(['/login']);
      return of({ message: '已登出' });
    }
  }

  getToken(): string | null {
    if (!this.isBrowser) {
      return null;
    }
    return localStorage.getItem(this.tokenKey);
  }

  getAuthHeaders(): HttpHeaders {
    if (!this.isBrowser) {
      return new HttpHeaders();
    }
    
    const token = localStorage.getItem(this.tokenKey);
    const tokenType = localStorage.getItem(this.tokenTypeKey) || 'Bearer';
    
    if (token) {
      return new HttpHeaders({
        'Authorization': `${tokenType} ${token}`
      });
    }
    
    return new HttpHeaders();
  }

  isAuthenticated(): boolean {
    if (!this.isBrowser) {
      return false;
    }
    return !!localStorage.getItem(this.tokenKey);
  }

  private handleError(error: any) {
    let errorMessage = 'An error occurred';
    if (error.error instanceof ErrorEvent) {
      // Client-side error
      errorMessage = error.error.message;
    } else {
      // Server-side error
      errorMessage = error.error?.detail || `Error Code: ${error.status}\nMessage: ${error.message}`;
    }
    console.error(errorMessage);
    return throwError(() => new Error(errorMessage));
  }
}

import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { AuthService } from './auth.service';

@Injectable({
  providedIn: 'root'
})
export class HistoryService {
  private apiUrl = 'http://localhost:8000';  // 改為正確的API路徑

  constructor(
    private http: HttpClient,
    private authService: AuthService
  ) { }

  getQueryHistory(skip: number = 0, limit: number = 10): Observable<any> {
    return this.http.get(`${this.apiUrl}/api/history?skip=${skip}&limit=${limit}`, {
      headers: this.authService.getAuthHeaders()
    }).pipe(
      catchError(this.handleError)
    );
  }

  getQueryById(recordId: number): Observable<any> {
    return this.http.get(`${this.apiUrl}/api/history/${recordId}`, {
      headers: this.authService.getAuthHeaders()
    }).pipe(
      catchError(this.handleError)
    );
  }

  getLatestQuery(): Observable<any> {
    return this.http.get(`${this.apiUrl}/api/history/latest`, {
      headers: this.authService.getAuthHeaders()
    }).pipe(
      catchError(this.handleError)
    );
  }

  deleteQuery(recordId: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/api/history/${recordId}`, {
      headers: this.authService.getAuthHeaders()
    }).pipe(
      catchError(this.handleError)
    );
  }

  private handleError(error: any) {
    let errorMessage = 'An error occurred while processing your request';
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

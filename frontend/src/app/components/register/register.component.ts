import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { HttpErrorResponse } from '@angular/common/http';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './register.component.html',
  styleUrls: ['./register.component.css']
})
export class RegisterComponent {
  user = {
    user_name: '',
    email: '',
    password: ''
  };
  confirmPassword: string = '';
  errorMessage: string = '';
  isLoading: boolean = false;
  submitting: boolean = false;

  constructor(
    private authService: AuthService,
    private router: Router
  ) {
    // Redirect if already logged in
    if (this.authService.isAuthenticated()) {
      this.router.navigate(['/']);
    }
  }

  register() {
    this.errorMessage = '';
    this.isLoading = true;
    this.submitting = true;

    console.log('註冊開始處理');

    // Validate inputs
    if (!this.user.user_name || !this.user.email || !this.user.password) {
      this.errorMessage = '請填寫所有必填欄位';
      this.isLoading = false;
      this.submitting = false;
      console.log('驗證失敗：', this.errorMessage);
      return;
    }

    if (this.user.password !== this.confirmPassword) {
      this.errorMessage = '密碼和確認密碼不一致';
      this.isLoading = false;
      this.submitting = false;
      console.log('驗證失敗：', this.errorMessage);
      return;
    }

    // Simple email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(this.user.email)) {
      this.errorMessage = '請輸入有效的電子郵件地址';
      this.isLoading = false;
      this.submitting = false;
      console.log('驗證失敗：', this.errorMessage);
      return;
    }

    console.log('驗證通過，準備發送請求');
    console.log('註冊數據：', JSON.stringify(this.user));

    this.authService.register(this.user).subscribe({
      next: (response) => {
        console.log('註冊成功：', response);
        this.isLoading = false;
        this.submitting = false;
        // After successful registration, redirect to login
        this.router.navigate(['/login'], { 
          queryParams: { registered: 'true' } 
        });
      },
      error: (error: any) => {
        this.isLoading = false;
        this.submitting = false;
        console.error('註冊錯誤：', error);
        
        if (error instanceof HttpErrorResponse) {
          if (error.error?.detail) {
            this.errorMessage = error.error.detail;
          } else {
            this.errorMessage = `HTTP錯誤 ${error.status}: ${error.statusText || '伺服器錯誤'}`;
          }
        } else {
          this.errorMessage = error.message || '註冊失敗，請重試';
        }
      }
    });
  }

  navigateToLogin() {
    this.router.navigate(['/login']);
  }
}

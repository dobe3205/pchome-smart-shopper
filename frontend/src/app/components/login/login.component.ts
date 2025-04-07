import { Component, OnInit, PLATFORM_ID, Inject } from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { AuthService } from '../../services/auth.service';
import { catchError, of, timeout } from 'rxjs';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent implements OnInit {
  username: string = '';
  password: string = '';
  errorMessage: string = '';
  successMessage: string = '';
  isLoading: boolean = false;
  isBackendAvailable: boolean = true;
  checkingBackend: boolean = false;
  private isBrowser: boolean;
  private returnUrl: string | null = null;

  constructor(
    private authService: AuthService,
    private router: Router,
    private route: ActivatedRoute,
    private http: HttpClient,
    @Inject(PLATFORM_ID) platformId: Object
  ) {
    this.isBrowser = isPlatformBrowser(platformId);
    
    // Redirect if already logged in
    if (this.authService.isAuthenticated()) {
      this.router.navigate(['/']);
    }
  }

  ngOnInit() {
    // 檢查後端是否可用
    if (this.isBrowser) {
      this.checkBackendAvailability();
    }
    
    // 檢查是否從註冊頁面跳轉過來
    this.route.queryParams.subscribe(params => {
      if (params['registered'] === 'true') {
        this.successMessage = '註冊成功！請使用您的新帳號登入。';
      }
      
      // 檢查是否有返回URL
      if (params['returnUrl']) {
        this.returnUrl = params['returnUrl'];
        if (this.isBrowser) {
          sessionStorage.setItem('returnUrl', params['returnUrl']);
        }
      }
    });
  }

  checkBackendAvailability() {
    this.checkingBackend = true;
    
    // 使用 OPTIONS 請求檢查 API 端點可用性
    this.http.options('http://localhost:8000/api/token', { observe: 'response' })
      .pipe(
        timeout(5000), // 5秒超時
        catchError(error => {
          console.error('後端連接測試失敗:', error);
          // 如果 OPTIONS 請求失敗，但不是網絡錯誤，可能是 CORS 設置問題，後端可能仍在運行
          if (error.status && error.status !== 0) {
            console.log('後端可能正在運行，但 CORS 設置可能有問題');
            return of({ status: 200 }); // 假設後端可用
          }
          return of(null);
        })
      )
      .subscribe({
        next: (response) => {
          if (response) {
            console.log('後端連接成功或可能存在');
            this.isBackendAvailable = true;
          } else {
            this.isBackendAvailable = false;
            this.errorMessage = '無法連接到後端服務。請確保後端服務已啟動並在 http://localhost:8000 運行。';
          }
          this.checkingBackend = false;
        }
      });
  }

  login() {
    // 檢查後端是否可用
    if (!this.isBackendAvailable) {
      this.errorMessage = '無法連接到後端服務。請確保後端服務已啟動並在 http://localhost:8000 運行。';
      return;
    }

    this.errorMessage = '';
    this.successMessage = '';
    this.isLoading = true;

    if (!this.username || !this.password) {
      this.errorMessage = '請輸入用戶名和密碼';
      this.isLoading = false;
      return;
    }

    console.log('登入嘗試中...');
    
    this.authService.login(this.username, this.password).subscribe({
      next: () => {
        this.isLoading = false;
        console.log('登入成功');
        
        // 檢查是否有儲存的返回URL
        let savedReturnUrl = this.returnUrl;
        if (this.isBrowser) {
          const storedReturnUrl = sessionStorage.getItem('returnUrl');
          if (storedReturnUrl) {
            savedReturnUrl = storedReturnUrl;
            sessionStorage.removeItem('returnUrl');
          }
        }
        
        if (savedReturnUrl) {
          this.router.navigateByUrl(savedReturnUrl);
        } else {
          this.router.navigate(['/']);
        }
      },
      error: (error) => {
        this.isLoading = false;
        console.error('登入失敗:', error);
        
        if (error.status === 401) {
          this.errorMessage = '用戶名或密碼錯誤';
        } else {
          this.errorMessage = error.message || '登入失敗，請檢查帳號密碼';
        }
      }
    });
  }

  navigateToRegister() {
    this.router.navigate(['/register']);
  }

  clearMessages() {
    this.errorMessage = '';
    this.successMessage = '';
  }
  
  retryConnection() {
    this.errorMessage = '';
    this.checkBackendAvailability();
  }

  // 跳過後端檢查，直接進入登入流程
  skipCheck() {
    this.isBackendAvailable = true;
    this.checkingBackend = false;
  }
}

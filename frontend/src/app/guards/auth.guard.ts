import { inject } from '@angular/core';
import { Router, CanActivateFn } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const authGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (authService.isAuthenticated()) {
    return true;
  }

  // 記錄嘗試訪問的 URL，以便在登入後重定向
  router.navigate(['/login'], { queryParams: { returnUrl: state.url } });
  return false;
};

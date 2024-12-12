import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { API_URL } from './env';
import { map, shareReplay } from 'rxjs/operators';

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  constructor(private http: HttpClient) {}

  login(email: string, password: string) {
    return this.http
      .post(`${API_URL}/auth/login`, { email, password })
      .pipe(shareReplay());
  }

  register(email: string, password: string) {
    return this.http
      .post(`${API_URL}/auth/register`, { email, password })
      .pipe(shareReplay());
  }

  setToken(token: string) {
    localStorage.setItem('token', token);
    localStorage.setItem('tokenExpires', (Date.now() + 86400000).toString());
  }

  logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('tokenExpires');
  }

  public isLoggedIn() {
    const tokenExpires = localStorage.getItem('tokenExpires');
    return tokenExpires ? Date.now() < parseInt(tokenExpires, 10) : false;
  }

  public getToken() {
    return localStorage.getItem('token');
  }
}

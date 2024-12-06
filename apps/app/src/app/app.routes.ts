import { Routes } from '@angular/router';
import { AppLoginComponent } from './login/login.component';
import { AppComponent } from './app.component';
import { ImageSearchComponent } from './image-search/image-search.component';

export const routes: Routes = [
  { path: '', component: AppComponent },
  { path: 'login', component: AppLoginComponent },
  { path: 'image-search', component: ImageSearchComponent },
];

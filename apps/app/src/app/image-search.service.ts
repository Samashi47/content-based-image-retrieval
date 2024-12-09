import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { API_URL } from './env';
import { map, shareReplay } from 'rxjs/operators';
import { Observable } from 'rxjs';

interface result {
  image: string;
  similarity: number;
}

@Injectable({
  providedIn: 'root',
})
export class ImageSearchService {
  constructor(private http: HttpClient) {}

  imageSimpleSearch(query: File): Observable<result[]> {
    const formData = new FormData();
    formData.append('image', query);

    return this.http
      .post<result[]>(`${API_URL}/image/simple-search`, formData)
      .pipe(shareReplay());
  }
}

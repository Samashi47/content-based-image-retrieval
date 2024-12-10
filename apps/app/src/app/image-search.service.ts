import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { API_URL } from './env';
import { map, shareReplay } from 'rxjs/operators';
import { Observable } from 'rxjs';

interface searchResult {
  title: string;
  image: string;
  similarity: number;
}

interface imageDescriptors {
  dominant_colors: number[][];
  color_histogram: number[][];
  hu_moments: number[];
}

@Injectable({
  providedIn: 'root',
})
export class ImageSearchService {
  constructor(private http: HttpClient) {}

  imageDescriptors(query: File): Observable<imageDescriptors> {
    const formData = new FormData();
    formData.append('image', query);

    return this.http
      .post<imageDescriptors>(`${API_URL}/image/descriptors`, formData)
      .pipe(shareReplay());
  }

  imageSimpleSearch(query: File): Observable<searchResult[]> {
    const formData = new FormData();
    formData.append('image', query);

    return this.http
      .post<searchResult[]>(`${API_URL}/image/simple-search`, formData)
      .pipe(shareReplay());
  }

  advancedSearch(query: File): Observable<searchResult[]> {
    const formData = new FormData();
    formData.append('image', query);

    return this.http
      .post<searchResult[]>(`${API_URL}/image/advanced-search`, formData)
      .pipe(shareReplay());
  }

  relevanceFeedback(weights: any, relevance: number[]): void {
    const formData = new FormData();
    formData.append('weights', JSON.stringify(weights));
    formData.append('relevance', JSON.stringify(relevance));

    console.log(formData);
    this.http.post(`${API_URL}/image/relevance-feedback`, formData).subscribe(
      (data) => {
        console.log(data);
      },
      (error: HttpErrorResponse) => {
        console.log(error.error);
      }
    );
  }
}

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

interface weights {
  dominant_colors: number;
  color_histogram: number;
  fourier_descriptors: number;
  hu_moments: number;
  edge_histogram: number;
  gabor: number;
}

interface advancedResults {
  images: searchResult[];
  query_id: string;
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

  advancedSearch(query: File): Observable<advancedResults> {
    const formData = new FormData();
    formData.append('image', query);
    console.log(formData);
    return this.http
      .post<advancedResults>(`${API_URL}/image/advanced-search`, formData)
      .pipe(shareReplay());
  }

  relevanceFeedback(
    relevance: number[],
    query_id: string
  ): Observable<advancedResults> {
    const formData = new FormData();
    formData.append('relevance', JSON.stringify(relevance));
    formData.append('query_id', query_id);
    console.log(formData);
    return this.http
      .post<advancedResults>(`${API_URL}/image/relevance-feedback`, formData)
      .pipe(shareReplay());
  }
}

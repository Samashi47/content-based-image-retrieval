import { Component, inject, OnInit, Input } from '@angular/core';
import { MatTabsModule } from '@angular/material/tabs';
import {
  AbstractControl,
  FormBuilder,
  FormsModule,
  ReactiveFormsModule,
  ValidationErrors,
  ValidatorFn,
  Validators,
} from '@angular/forms';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatStepperModule } from '@angular/material/stepper';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { AuthService } from '../auth.service';
import { ImageSearchService } from '../image-search.service';
import { Router } from '@angular/router';
import { DomSanitizer, SafeUrl } from '@angular/platform-browser';
import { MatCardModule } from '@angular/material/card';
import { NgxCroppedEvent, NgxPhotoEditorService } from 'ngx-photo-editor';
import { StepperOrientation } from '@angular/material/stepper/testing';

interface result {
  image: string;
  similarity: number;
}

@Component({
  selector: 'app-image-search',
  imports: [
    MatIconModule,
    MatTabsModule,
    MatButtonModule,
    MatStepperModule,
    FormsModule,
    ReactiveFormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatCardModule,
  ],
  templateUrl: './image-search.component.html',
  styleUrl: './image-search.component.css',
})
export class ImageSearchComponent implements OnInit {
  private _formBuilder = inject(FormBuilder);
  private _authService = inject(AuthService);
  private _imageSearchService = inject(ImageSearchService);
  private _router = inject(Router);
  private _domSanitizer = inject(DomSanitizer);
  private _ngxPhotoEditorService = inject(NgxPhotoEditorService);

  selectedImageIndex: number | null = null;

  firstFormGroup = this._formBuilder.group({
    firstCtrl: [''],
  });

  secondFormGroup = this._formBuilder.group({
    secondCtrl: [null as number | null, Validators.required],
  });

  isLinear = true;
  uploadedFiles: { blob: File; sanitized: string }[] = [];
  currentFile: File | null = null;
  fileName = 'Select your image(s)';
  results: result[] = [];

  ngOnInit(): void {
    if (!this._authService.isLoggedIn()) {
      this._router.navigate(['/login']);
    }
  }

  selectFiles(event: any): void {
    if (event.target.files) {
      for (let i = 0; i < event.target.files.length; i++) {
        const file = event.target.files[i];
        this.uploadedFiles.push({
          blob: file,
          sanitized: '',
        });
        const reader = new FileReader();
        reader.readAsDataURL(file);

        reader.onload = (e) => {
          this.uploadedFiles[i].sanitized = e.target?.result as string;
        };
      }

      this.updateFileName();
    }
  }

  selectCard(index: number): void {
    if (this.selectedImageIndex === index) {
      this.selectedImageIndex = null;
      this.secondFormGroup.get('secondCtrl')?.setValue(null);
    } else {
      this.selectedImageIndex = index;
      this.secondFormGroup.get('secondCtrl')?.setValue(index);
    }
  }

  /*
  selectFiles(event: any): void {
    if (event.target.files) {
      for (let i = 0; i < event.target.files.length; i++) {
        this.uploadedFiles.push(event.target.files[i]);
      }
      this.saveFilesToSession();
      this.updateFileName();
    }
  }*/

  deleteFile(index: number): void {
    this.uploadedFiles.splice(index, 1);
    this.updateFileName();
    if (this.selectedImageIndex === index) {
      this.selectedImageIndex = null;
    }
  }

  updateFileName(): void {
    this.fileName =
      this.uploadedFiles.length > 0
        ? `${this.uploadedFiles.length} images uploaded`
        : 'Select your image(s)';
  }

  /*
  saveFilesToSession(): void {
    sessionStorage.setItem('uploadedFiles', JSON.stringify(this.uploadedFiles));
  }

  loadFilesFromSession(): void {
    const files = sessionStorage.getItem('uploadedFiles');
    if (files) {
      this.uploadedFiles = JSON.parse(files);
      this.updateFileName();
    }
  }*/

  deleteAllFiles(): void {
    this.uploadedFiles = [];
    this.updateFileName();
    this.selectedImageIndex = null;
    this.results = [];
  }

  /*
  selectFile(event: any): void {
    if (event.target.files && event.target.files[0]) {
      const file: File = event.target.files[0];
      this.currentFile = file;
      this.fileName = this.currentFile.name;
    } else {
      this.fileName = 'Select your image';
    }
  }
  */

  /*async arrayBufferToBase64(buffer: Promise<ArrayBuffer>): Promise<string> {
    let binary = '';
    const bytes = new Uint8Array(await buffer);
    const len = bytes.byteLength;
    for (let i = 0; i < len; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return window.btoa(binary);
  }*/

  sanitize(url: string): SafeUrl {
    return this._domSanitizer.bypassSecurityTrustUrl(url);
  }

  openImageEditor(index: number): void {
    this._ngxPhotoEditorService
      .open(this.uploadedFiles[index].blob)
      .subscribe((data) => {
        if (data.file && data.base64) {
          this.uploadedFiles[index].blob = data.file;
          this.uploadedFiles[index].sanitized = data.base64;
        }
      });
  }

  search(): void {
    if (this.selectedImageIndex !== null) {
      const selectedFile = this.uploadedFiles[this.selectedImageIndex].blob;
      this._imageSearchService.imageSimpleSearch(selectedFile).subscribe(
        (results) => {
          this.results = results;
          console.log('Search results:', this.results);
        },
        (error) => {
          console.error('Search error:', error);
        }
      );
    }
  }
}
import { Component, inject, OnInit } from '@angular/core';
import { MatTabsModule } from '@angular/material/tabs';
import { FormBuilder, FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatStepperModule } from '@angular/material/stepper';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { AuthService } from '../auth.service';
import { Router } from '@angular/router';
import { DomSanitizer, SafeUrl } from '@angular/platform-browser';
import { MatCardModule } from '@angular/material/card';
import { NgxCroppedEvent, NgxPhotoEditorService } from 'ngx-photo-editor';
import { StepperOrientation } from '@angular/material/stepper/testing';

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
  private _router = inject(Router);
  private _domSanitizer = inject(DomSanitizer);
  private _ngxPhotoEditorService = inject(NgxPhotoEditorService);

  // firstCtrl should be when uploadedFiles is empty
  firstFormGroup = this._formBuilder.group({
    firstCtrl: [''],
  });

  isLinear = true;
  uploadedFiles: { blob: File; sanitized: string }[] = [];
  currentFile?: File;
  fileName = 'Select your image(s)';

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
  }

  selectFile(event: any): void {
    if (event.target.files && event.target.files[0]) {
      const file: File = event.target.files[0];
      this.currentFile = file;
      this.fileName = this.currentFile.name;
    } else {
      this.fileName = 'Select your image';
    }
  }

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
}

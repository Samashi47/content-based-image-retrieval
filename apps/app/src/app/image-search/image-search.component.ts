import {
  Component,
  inject,
  Inject,
  OnInit,
  Input,
  ChangeDetectionStrategy,
} from '@angular/core';
import { MatTabsModule } from '@angular/material/tabs';
import {
  AbstractControl,
  FormBuilder,
  FormsModule,
  ReactiveFormsModule,
  ValidationErrors,
  ValidatorFn,
  Validators,
  FormControl,
  FormGroupDirective,
  NgForm,
} from '@angular/forms';
import { ErrorStateMatcher } from '@angular/material/core';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatStepperModule } from '@angular/material/stepper';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { AuthService } from '../auth.service';
import { ImageSearchService } from '../image-search.service';
import { PlotlyService } from '../plotly.service';
import { Router } from '@angular/router';
import { DomSanitizer, SafeUrl } from '@angular/platform-browser';
import { MatCardModule } from '@angular/material/card';
import { NgxCroppedEvent, NgxPhotoEditorService } from 'ngx-photo-editor';
import { MatSelectModule } from '@angular/material/select';
import {
  MatDialog,
  MatDialogActions,
  MatDialogClose,
  MatDialogContent,
  MatDialogRef,
  MatDialogTitle,
  MAT_DIALOG_DATA,
} from '@angular/material/dialog';

interface result {
  title: string;
  image: SafeUrl;
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
  images: result[];
  weights: weights;
  query_id: string;
}

interface imageDescriptors {
  dominant_colors: number[][];
  color_histogram: number[][];
  hu_moments: number[];
}

/** Error when invalid control is dirty, touched, or submitted. */
export class MyErrorStateMatcher implements ErrorStateMatcher {
  isErrorState(
    control: FormControl | null,
    form: FormGroupDirective | NgForm | null
  ): boolean {
    const isSubmitted = form && form.submitted;
    return !!(
      control &&
      control.invalid &&
      (control.dirty || control.touched || isSubmitted)
    );
  }
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
    MatSelectModule,
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
  readonly _dialog = inject(MatDialog);

  selectedImageIndex: number | null = null;

  firstFormGroup = this._formBuilder.group({
    firstCtrl: [''],
  });

  secondFormGroup = this._formBuilder.group({
    secondCtrl: [null as number | null, Validators.required],
  });

  thirdCtrl = new FormControl('', Validators.required);
  thirdFormGroup = this._formBuilder.group({
    thirdCtrl: this.thirdCtrl,
  });

  matcher = new MyErrorStateMatcher();
  isLinear = true;
  uploadedFiles: { blob: File; sanitized: string }[] = [];
  currentFile: File | null = null;
  fileName = 'Select your image(s)';
  results: result[] = [];
  advancedResults: result[] = [];
  weights: weights = {
    dominant_colors: 0.5,
    color_histogram: 0.5,
    fourier_descriptors: 0.5,
    hu_moments: 0.5,
    edge_histogram: 0.5,
    gabor: 0.5,
  };
  queryId = '';
  relevanceFeedback: string[] = Array.from({ length: 15 }, () => '');

  ngOnInit(): void {
    if (!this._authService.isLoggedIn()) {
      this._router.navigate(['/login']);
    }
  }

  selectFiles(event: any): void {
    if (event.target.files) {
      const l = this.uploadedFiles.length;
      for (let i = 0; i < event.target.files.length; i++) {
        const file = event.target.files[i];
        this.uploadedFiles.push({
          blob: file,
          sanitized: '',
        });
        const reader = new FileReader();
        reader.readAsDataURL(file);

        reader.onload = (e) => {
          this.uploadedFiles[i + l].sanitized = e.target?.result as string;
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

  deleteFile(index: number): void {
    if (this.selectedImageIndex === index) {
      this.selectedImageIndex = null;
      this.secondFormGroup.get('secondCtrl')?.setValue(null);
    }
    this.uploadedFiles.splice(index, 1);
    this.updateFileName();
  }

  updateFileName(): void {
    this.fileName =
      this.uploadedFiles.length > 0
        ? `${this.uploadedFiles.length} images uploaded`
        : 'Select your image(s)';
  }

  deleteAllFiles(): void {
    this.uploadedFiles = [];
    this.updateFileName();
    this.selectedImageIndex = null;
    this.secondFormGroup.get('secondCtrl')?.setValue(null);
    this.results = [];
    this.advancedResults = [];
    this.relevanceFeedback = Array.from({ length: 15 }, () => '');
  }

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

  descriptors(index: number): void {
    this._dialog.open(DescriptorsDialog, {
      data: { index: index, uploadedFiles: this.uploadedFiles },
    });
  }

  simpleSearch(): void {
    console.log('Selected image:', this.selectedImageIndex);
    if (this.selectedImageIndex !== null) {
      console.log('Selected image:', this.selectedImageIndex);
      const selectedFile = this.uploadedFiles[this.selectedImageIndex].blob;
      this._imageSearchService.imageSimpleSearch(selectedFile).subscribe(
        (results) => {
          this.results = results.map((result) => {
            return {
              title: result.title,
              image: this.sanitize('data:image/jpeg;base64,' + result.image),
              similarity: result.similarity,
            };
          });
          console.log('Search results:', results);
        },
        (error) => {
          console.error('Search error:', error);
        }
      );
    }
  }

  advancedSearch(): void {
    console.log('Selected image:', this.selectedImageIndex);
    if (this.selectedImageIndex !== null) {
      console.log('Selected image:', this.selectedImageIndex);
      const selectedFile = this.uploadedFiles[this.selectedImageIndex].blob;
      this._imageSearchService.advancedSearch(selectedFile).subscribe(
        (results) => {
          this.advancedResults = results.images.map((result) => {
            return {
              title: result.title,
              image: this.sanitize('data:image/jpeg;base64,' + result.image),
              similarity: result.similarity,
            };
          });
          this.queryId = results.query_id;
          console.log('Advanced search results:', results);
        },
        (error) => {
          console.error('Advanced search error:', error);
        }
      );
    }
  }

  relevanceFeedbackSearch(): void {
    console.log('Selected image:', this.selectedImageIndex);
    if (this.selectedImageIndex !== null) {
      const relevance = this.relevanceFeedback.map((value) => {
        return value === '0' ? 0 : 1;
      });

      this._imageSearchService
        .relevanceFeedback(relevance, this.queryId)
        .subscribe(
          (results) => {
            this.advancedResults = results.images.map((result) => {
              return {
                title: result.title,
                image: this.sanitize('data:image/jpeg;base64,' + result.image),
                similarity: result.similarity,
              };
            });
            this.queryId = results.query_id;
            console.log('Relevance feedback results:', results);
          },
          (error) => {
            console.error('Relevance feedback error:', error);
          }
        );
    }
  }

  logout(): void {
    this._authService.logout();
    this._router.navigate(['/login']);
  }
}

@Component({
  selector: 'descriptors-dialog',
  templateUrl: 'descriptors-dialog.html',
  imports: [
    MatButtonModule,
    MatDialogActions,
    MatDialogClose,
    MatDialogTitle,
    MatDialogContent,
  ],
  styleUrl: './image-search.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DescriptorsDialog {
  constructor(
    private plot: PlotlyService,
    @Inject(MAT_DIALOG_DATA) public data: { index: number; uploadedFiles: any }
  ) {}

  private _imageSearchService = inject(ImageSearchService);
  readonly dialogRef = inject(MatDialogRef<DescriptorsDialog>);

  ngOnInit(): void {
    const { index, uploadedFiles } = this.data;
    const selectedFile = uploadedFiles[index].blob;
    let humoments: number[] = [];

    this._imageSearchService.imageDescriptors(selectedFile).subscribe(
      (results) => {
        console.log('Descriptors:', results);
        this.plot.plotHist(
          'histPlot',
          results.color_histogram[0],
          results.color_histogram[1],
          results.color_histogram[2]
        );

        this.plot.plotDominantColors(
          'dominantColorContainer',
          results.dominant_colors
        );

        humoments = results.hu_moments;
        const humomentsDiv = document.getElementById('humomentsContainer');
        for (let i = 0; i < humoments.length; i++) {
          const p = document.createElement('p');
          p.textContent = `Hu Moment ${i + 1}: ${humoments[i]}`;
          humomentsDiv?.appendChild(p);
        }
      },
      (error) => {
        console.error('Descriptors error:', error);
      }
    );
  }
}

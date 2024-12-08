import { Component, CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { NgxPhotoEditorModule } from 'ngx-photo-editor';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, NgxPhotoEditorModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css',
  schemas: [CUSTOM_ELEMENTS_SCHEMA],
})
export class AppComponent {
  title = 'app';
}

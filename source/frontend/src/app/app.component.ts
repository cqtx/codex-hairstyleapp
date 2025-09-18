import { Component, computed, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';

interface StyleTransferResponse {
  mimeType: string;
  data: string;
}

type ImageKind = 'user' | 'reference';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent {
  private readonly apiBaseUrl = (window as any).__APP_API_BASE__ ?? 'http://localhost:8000';

  userPreview = signal<string | null>(null);
  referencePreview = signal<string | null>(null);
  resultImage = signal<string | null>(null);
  isLoading = signal(false);
  errorMessage = signal<string | null>(null);

  private userFile = signal<File | null>(null);
  private referenceFile = signal<File | null>(null);

  cannotSubmit = computed(() => this.isLoading() || !this.userFile() || !this.referenceFile());

  constructor(private readonly http: HttpClient) {}

  onFileSelected(kind: ImageKind, event: Event): void {
    const target = event.target as HTMLInputElement;
    const file = target.files?.item(0);

    if (!file) {
      return;
    }

    const validationError = this.validateFile(file);
    if (validationError) {
      this.errorMessage.set(`${this.formatLabel(kind)}: ${validationError}`);
      target.value = '';
      this.setFile(kind, null, null);
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      const dataUrl = typeof reader.result === 'string' ? reader.result : null;
      this.setFile(kind, file, dataUrl);
      target.value = '';
    };
    reader.onerror = () => {
      this.errorMessage.set('Could not read the selected file.');
      target.value = '';
      this.setFile(kind, null, null);
    };
    reader.readAsDataURL(file);
  }

  upload(): void {
    if (this.cannotSubmit()) {
      this.errorMessage.set('Select both images before generating a hairstyle.');
      return;
    }

    const formData = new FormData();
    const userFile = this.userFile();
    const referenceFile = this.referenceFile();
    if (!userFile || !referenceFile) {
      this.errorMessage.set('Select both images before generating a hairstyle.');
      this.isLoading.set(false);
      return;
    }

    formData.append('user_image', userFile);
    formData.append('reference_image', referenceFile);

    this.isLoading.set(true);
    this.errorMessage.set(null);
    this.resultImage.set(null);

    this.http.post<StyleTransferResponse>(`${this.apiBaseUrl}/api/style-transfer`, formData).subscribe({
      next: (response) => {
        this.isLoading.set(false);
        if (!response?.data) {
          this.errorMessage.set('The API returned an empty response.');
          return;
        }
        const mime = response.mimeType ?? 'image/png';
        this.resultImage.set(`data:${mime};base64,${response.data}`);
      },
      error: (error: HttpErrorResponse) => {
        this.isLoading.set(false);
        this.errorMessage.set(this.extractErrorMessage(error));
      },
    });
  }

  downloadResult(): void {
    const result = this.resultImage();
    if (!result) {
      return;
    }
    const element = document.createElement('a');
    element.href = result;
    element.download = 'nano-banana-hairstyle.png';
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  }

  clear(kind: ImageKind): void {
    this.setFile(kind, null, null);
    this.errorMessage.set(null);
  }

  private validateFile(file: File): string | null {
    if (!file.type.startsWith('image/')) {
      return 'Please choose an image file.';
    }
    if (file.size > 7 * 1024 * 1024) {
      return 'Image must be under 7MB to keep the upload fast.';
    }
    return null;
  }

  private setFile(kind: ImageKind, file: File | null, preview: string | null): void {
    if (kind === 'user') {
      this.userFile.set(file);
      this.userPreview.set(preview);
    } else {
      this.referenceFile.set(file);
      this.referencePreview.set(preview);
    }
  }

  private formatLabel(kind: ImageKind): string {
    return kind === 'user' ? 'Your photo' : 'Reference hair';
  }

  private extractErrorMessage(error: HttpErrorResponse): string {
    const defaultMessage = 'Could not generate the hairstyle. Please try again.';

    const detail = error.error?.detail;
    if (!detail) {
      return error.message || defaultMessage;
    }

    if (typeof detail === 'string') {
      const parts = detail.split('\n').map((part) => part.trim()).filter(Boolean);
      return parts[0] ?? defaultMessage;
    }

    if (typeof detail === 'object') {
      const reason = detail.reason ?? detail.message;
      const label = detail.image === 'user' || detail.image === 'reference'
        ? this.formatLabel(detail.image)
        : 'Image';
      if (reason) {
        return `${label}: ${reason}`;
      }
    }

    return defaultMessage;
  }
}

declare interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList;
}

declare interface SpeechRecognitionResultList {
  [index: number]: SpeechRecognitionResult;
  length: number;
}

declare interface SpeechRecognitionResult {
  [index: number]: SpeechRecognitionAlternate;
  length: number;
  isFinal: boolean;
}

declare interface SpeechRecognitionAlternate {
  transcript: string;
  confidence: number;
}

declare class SpeechRecognition {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  maxAlternatives: number;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: ((event: Event) => void) | null;
  onstart: (() => void) | null;
  onend: (() => void) | null;
  start(): void;
  stop(): void;
  abort(): void;
}

declare interface Window {
  SpeechRecognition?: typeof SpeechRecognition;
  webkitSpeechRecognition?: typeof SpeechRecognition;
}

/** Shared types for the profile/settings content. */

export interface ProfileContent {
  kicker: string;
  title: string;
  lead: string;
  clientKeyTitle: string;
  clientKeyHint: string;
  copy: string;
  copied: string;
  displayNameTitle: string;
  displayNameLabel: string;
  displayNameHint: string;
  save: string;
  saved: string;
  runsTitle: string;
  privacyNote: string;
}

export interface SettingsContent {
  kicker: string;
  title: string;
  lead: string;
  apiTitle: string;
  apiHint: string;
  apiLabel: string;
  apiSave: string;
  apiSaved: string;
  apiInvalid: string;
  langTitle: string;
  langHint: string;
  dataTitle: string;
  dataHint: string;
  dataButton: string;
  dataDone: string;
  endpointsTitle: string;
  endpoints: { method: string; path: string; desc: string }[];
}

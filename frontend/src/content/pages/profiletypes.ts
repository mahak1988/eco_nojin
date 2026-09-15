export interface LegacyCard {
  title: string;
  value: string;
  unit: string;
  source: string;
  updated: string;
  empty: string;
}

export interface Achievement {
  icon: string;
  title: string;
  description: string;
  date: string;
}

export interface Milestone {
  icon: string;
  title: string;
  date: string;
}

export interface AssetItem {
  name: string;
  detail: string;
  status?: string;
  actionLabel?: string;
  actionPath?: string;
}

export interface AssetGroup {
  title: string;
  count: string;
  empty: string;
  items: AssetItem[];
}

export interface PreferenceItem {
  label: string;
  hint: string;
}

export interface SecurityAction {
  label: string;
  description: string;
  variant: 'primary' | 'danger' | 'warning';
}

export interface PrivacyOption {
  label: string;
  description: string;
}

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
  privacyNote: string;
  identityTitle: string;
  identityBioLabel: string;
  identityBioPlaceholder: string;
  identityBioHint: string;
  identityOrgLabel: string;
  identityOrgPlaceholder: string;
  identityLocationLabel: string;
  identityLocationPlaceholder: string;
  identityMemberSince: string;
  identityEdit: string;
  identityViewPublic: string;
  identityShare: string;
  identityPendingBanner: string;
  identityRestrictedBanner: string;
  legacyTitle: string;
  legacySubtitle: string;
  legacyCarbon: LegacyCard;
  legacyArea: LegacyCard;
  legacyWater: LegacyCard;
  legacyActivity: LegacyCard;
  legacyAchievements: string;
  legacyMilestones: string;
  legacyEmpty: string;
  legacyAchievementEmpty: string;
  assetsTitle: string;
  assetsLands: AssetGroup;
  assetsSensors: AssetGroup;
  assetsWallet: AssetGroup;
  assetsApiKeys: AssetGroup;
  assetsProjects: AssetGroup;
  assetsManage: string;
  prefsTitle: string;
  prefsLanguage: PreferenceItem;
  prefsTimezone: PreferenceItem;
  prefsUnits: PreferenceItem;
  prefsUnitsWarning: string;
  prefsTheme: PreferenceItem;
  prefsNotifications: PreferenceItem;
  prefsDashboard: PreferenceItem;
  prefsSaved: string;
  securityTitle: string;
  securityPassword: SecurityAction;
  security2fa: SecurityAction;
  securitySessions: SecurityAction;
  securityApiKeys: SecurityAction;
  securityExport: SecurityAction;
  securityPrivacy: SecurityAction;
  securityDeactivate: SecurityAction;
  securityDelete: SecurityAction;
  securityDeleteConfirm: string;
  securityDeleteType: string;
  securityDeleteFinal: string;
  securityDeleteCancelled: string;
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

export interface ProfileSettings {
  profile: ProfileContent;
  settings: SettingsContent;
}

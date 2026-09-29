/**
 * Sample strings for the stories.
 *
 * These are fixtures, not product copy. Every primitive takes its labels as
 * props precisely so that the component library carries no translatable string
 * of its own — the defect that kept 53 public pages in one language — and a
 * story that inlined a label would argue against the rule the stories exist to
 * demonstrate. The real strings live in `messages/*.json` and reach a component
 * through a page; the contract that page owes is what these stories photograph.
 *
 * `fa` and `en` are written out because those are the two the review has to be
 * possible in: `fa` is the platform default and the only RTL the design was drawn
 * for, and `en` is what every reader of this repository reads. The other twelve
 * locales fall back to `en` for their strings while the toolbar still sets
 * `lang` and `dir` for them — that is a limitation of the fixture set, not of the
 * components.
 *
 * `check-ui-kit.mjs` fails on a Persian literal in a JSX text position or a
 * `label=` prop inside `src/components/ui`, which is why the literals live here
 * and are passed as variables rather than inlined. Do not move them back.
 */

export interface SampleText {
  groupLabel: string;
  soilTitle: string;
  soilSummary: string;
  soilBody: string;
  waterTitle: string;
  waterSummary: string;
  waterBody: string;
  canopyTitle: string;
  canopyBody: string;
  lockedTitle: string;
  badgeNeutral: string;
  badgeInfo: string;
  badgeSuccess: string;
  badgeWarn: string;
  badgeBad: string;
  cardTitle: string;
  cardBody: string;
  dialogTitle: string;
  dialogDescription: string;
  dialogBody: string;
  dialogConfirm: string;
  inputLabel: string;
  inputPlaceholder: string;
  inputError: string;
  inputHint: string;
  selectLabel: string;
  selectOptionA: string;
  selectOptionB: string;
  selectOptionC: string;
  selectError: string;
  textareaLabel: string;
  textareaPlaceholder: string;
  textareaError: string;
  switchLabel: string;
  switchDescription: string;
  progressLabel: string;
  progressDetail: string;
  progressDetailShort: string;
  statLabel: string;
  statTrendUp: string;
  statTrendDown: string;
  statProvenanceSource: string;
  statProvenanceMethod: string;
  tableCaption: string;
  tableHeaderSite: string;
  tableHeaderNdvi: string;
  tableHeaderMoisture: string;
  tableEmpty: string;
  tableSource: string;
  breadcrumbHome: string;
  breadcrumbSystem: string;
  breadcrumbCurrent: string;
  paginationLabel: string;
  paginationPrevious: string;
  paginationNext: string;
  tabsLabel: string;
  tabsOverview: string;
  tabsMeasurements: string;
  tabsHistory: string;
  tabsLocked: string;
  tabsBody: string;
  toastInfoTitle: string;
  toastSuccessTitle: string;
  toastWarningTitle: string;
  toastErrorTitle: string;
  toastAction: string;
  offlineMessage: string;
  reconnectingMessage: string;
  paletteSearch: string;
  paletteClose: string;
  paletteItemRun: string;
  paletteItemDescribe: string;
  paletteItemExport: string;
  paletteRunDescription: string;
  paletteDescribeDescription: string;
  paletteExportDescription: string;
  boundaryTitle: string;
  boundaryBody: string;
  boundaryRetry: string;
  skeletonCaption: string;
}

const en: SampleText = {
  groupLabel: 'Site measurements',
  soilTitle: 'Soil moisture',
  soilSummary: 'Sampled 12 Aug, 3 depths',
  soilBody:
    'Volumetric water content averaged over the top 30 cm. The reading is from the last successful sync, not a live probe.',
  waterTitle: 'Surface water',
  waterSummary: 'OpenELE, Sentinel-2',
  waterBody: 'Water extent for the reporting window, derived from the last cloud-free scene.',
  canopyTitle: 'Canopy cover',
  canopyBody: 'Fraction of the cell classified as vegetated.',
  lockedTitle: 'Bulk export (administrators only)',
  badgeNeutral: 'Draft',
  badgeInfo: 'Scheduled',
  badgeSuccess: 'Verified',
  badgeWarn: 'Needs review',
  badgeBad: 'Rejected',
  cardTitle: 'Restoration site 14',
  cardBody:
    'A card is a surface, not a message: it holds whatever the page puts in it and carries no copy of its own.',
  dialogTitle: 'Archive this site?',
  dialogDescription: 'Archived sites stop receiving scheduled sampling. Nothing is deleted.',
  dialogBody:
    'Two of the four sampling points for this site are offline. Archiving keeps their last readings.',
  dialogConfirm: 'Archive',
  inputLabel: 'Site name',
  inputPlaceholder: 'e.g. Urmia lake north',
  inputError: 'A site name is required, and must be unique in this workspace.',
  inputHint: 'Shown on every public page for this site.',
  selectLabel: 'Sampling depth',
  selectOptionA: '10 cm',
  selectOptionB: '30 cm',
  selectOptionC: '60 cm',
  selectError: 'Choose a depth. The gateway rejects a query without one.',
  textareaLabel: 'Field notes',
  textareaPlaceholder: 'What changed since the last visit?',
  textareaError: 'Notes are limited to 500 characters.',
  switchLabel: 'Include this site in the public summary',
  switchDescription:
    'Turned off, the site stays in the workspace and disappears from the public list.',
  progressLabel: 'Ingesting readings',
  progressDetail: '3 of 51 sites',
  progressDetailShort: '7%',
  statLabel: 'Canopy cover',
  statTrendUp: 'up 4.1 pts since June',
  statTrendDown: 'down 2.3 pts since June',
  statProvenanceSource: 'Sentinel-2 L2A',
  statProvenanceMethod: 'NDVI mean, cloud mask 20%',
  tableCaption: 'Sampling points',
  tableHeaderSite: 'Site',
  tableHeaderNdvi: 'NDVI',
  tableHeaderMoisture: 'Moisture %',
  tableEmpty: 'No sampling point matches this filter.',
  tableSource: 'source: /api/v1/carbon/measurements?page=1',
  breadcrumbHome: 'Home',
  breadcrumbSystem: 'System',
  breadcrumbCurrent: 'Measurements',
  paginationLabel: 'Pagination',
  paginationPrevious: 'Previous',
  paginationNext: 'Next',
  tabsLabel: 'Site sections',
  tabsOverview: 'Overview',
  tabsMeasurements: 'Measurements',
  tabsHistory: 'History',
  tabsLocked: 'Maintenance',
  tabsBody: 'The panel belongs to the caller, so the markup inside a tab is the page’s decision.',
  toastInfoTitle: 'Sync started',
  toastSuccessTitle: 'Site archived',
  toastWarningTitle: 'Four points are offline',
  toastErrorTitle: 'Archive failed',
  toastAction: 'Retry',
  offlineMessage: 'You are offline. Readings from this device are shown.',
  reconnectingMessage: 'Reconnecting…',
  paletteSearch: 'Search commands',
  paletteClose: 'Close command palette',
  paletteItemRun: 'Run a HyDroMa model',
  paletteItemDescribe: 'Describe a site',
  paletteItemExport: 'Export measurements',
  paletteRunDescription: 'Soil, hydrology, erosion or carbon',
  paletteDescribeDescription: 'Summarise the last 90 days',
  paletteExportDescription: 'CSV of every sampling point',
  boundaryTitle: 'This panel could not be rendered',
  boundaryBody: 'The readings for this site failed to load. The rest of the page is unaffected.',
  boundaryRetry: 'Try again',
  skeletonCaption: 'Loading sampling points',
};

const fa: SampleText = {
  groupLabel: 'اندازه‌گیری ایستگاه',
  soilTitle: 'رطوبت خاک',
  soilSummary: 'نمونه‌برداری ۲۱ مرداد، سه عمق',
  soilBody:
    'میانگین آب خاک در ۳۰ سانتی‌متر بالای سطح. این مقدار از آخرین همگام‌سازی موفق است، نه از یک حسگر زنده.',
  waterTitle: 'آب سطحی',
  waterSummary: 'OpenELE، Sentinel-2',
  waterBody: 'گستره آب برای بازه گزارش، برگرفته از آخرین تصویر بدون ابر.',
  canopyTitle: 'پوشش تاج‌پوشش',
  canopyBody: 'سهم پوشش گیاهی از کل سلول شبکه.',
  lockedTitle: 'برون‌بری گروهی (تنها مدیران)',
  badgeNeutral: 'پیش‌نویس',
  badgeInfo: 'زمان‌بندی‌شده',
  badgeSuccess: 'تأییدشده',
  badgeWarn: 'نیازمند بازبینی',
  badgeBad: 'ردشده',
  cardTitle: 'ایستگاه احیای شماره ۱۴',
  cardBody: 'کارت یک سطح است، نه یک پیام: هرچه صفحه در آن بگذارد را نگه می‌دارد و خودش متنی ندارد.',
  dialogTitle: 'این ایستگاه بایگانی شود؟',
  dialogDescription:
    'ایستگاه‌های بایگانی‌شده نمونه‌برداری زمان‌بندی‌شده دریافت نمی‌کنند. چیزی حذف نمی‌شود.',
  dialogBody:
    'دو تا از چهار نقطه نمونه‌برداری این ایستگاه آفلاین‌اند. بایگانی کردن، آخرین قرائت آن‌ها را نگه می‌دارد.',
  dialogConfirm: 'بایگانی',
  inputLabel: 'نام ایستگاه',
  inputPlaceholder: 'مثلاً دریاچه ارومیه شمالی',
  inputError: 'نام ایستگاه الزامی است و باید در این فضای کاری یکتا باشد.',
  inputHint: 'روی هر صفحه عمومی این ایستگاه نمایش داده می‌شود.',
  selectLabel: 'عمق نمونه‌برداری',
  selectOptionA: '۱۰ سانتی‌متر',
  selectOptionB: '۳۰ سانتی‌متر',
  selectOptionC: '۶۰ سانتی‌متر',
  selectError: 'عمق را انتخاب کنید. دروازه بدون آن درخواست را نمی‌پذیرد.',
  textareaLabel: 'یادداشت میدانی',
  textareaPlaceholder: 'از بازدید پیش چه چیزی تغییر کرد؟',
  textareaError: 'یادداشت حداکثر ۵۰۰ نویسه است.',
  switchLabel: 'این ایستگاه در خلاصه عمومی بیاید',
  switchDescription: 'با خاموش بودن، ایستگاه در فضای کاری می‌ماند و از فهرست عمومی حذف می‌شود.',
  progressLabel: 'در حال دریافت قرائت‌ها',
  progressDetail: '۳ ایستگاه از ۵۱',
  progressDetailShort: '۷٪',
  statLabel: 'پوشش تاج‌پوشش',
  statTrendUp: '۴٫۱ واحد بیشتر نسبت به ژوئن',
  statTrendDown: '۲٫۳ واحد کمتر نسبت به ژوئن',
  statProvenanceSource: 'Sentinel-2 L2A',
  statProvenanceMethod: 'میانگین NDVI، پوشش ابر ۲۰٪',
  tableCaption: 'نقاط نمونه‌برداری',
  tableHeaderSite: 'ایستگاه',
  tableHeaderNdvi: 'NDVI',
  tableHeaderMoisture: 'رطوبت ٪',
  tableEmpty: 'هیچ نقطه نمونه‌برداری با این صافی مطابقت ندارد.',
  tableSource: 'منبع: /api/v1/carbon/measurements?page=1',
  breadcrumbHome: 'خانه',
  breadcrumbSystem: 'سامانه',
  breadcrumbCurrent: 'اندازه‌گیری‌ها',
  paginationLabel: 'صفحه‌بندی',
  paginationPrevious: 'پیشین',
  paginationNext: 'بعدی',
  tabsLabel: 'بخش‌های ایستگاه',
  tabsOverview: 'نمای کلی',
  tabsMeasurements: 'اندازه‌گیری‌ها',
  tabsHistory: 'تاریخچه',
  tabsLocked: 'نگهداری',
  tabsBody: 'پنل در اختیار صفحه است، پس نشانه‌گذاری درون هر زبانه تصمیم خودِ صفحه است.',
  toastInfoTitle: 'همگام‌سازی آغاز شد',
  toastSuccessTitle: 'ایستگاه بایگانی شد',
  toastWarningTitle: 'چهار نقطه آفلاین‌اند',
  toastErrorTitle: 'بایگانی ناموفق بود',
  toastAction: 'تلاش دوباره',
  offlineMessage: 'شما آفلاین هستید. قرائت‌های این دستگاه نمایش داده می‌شود.',
  reconnectingMessage: 'در حال اتصال دوباره…',
  paletteSearch: 'جست‌وجوی فرمان‌ها',
  paletteClose: 'بستن جعبه‌فرمان',
  paletteItemRun: 'اجرای یک مدل HyDroMa',
  paletteItemDescribe: 'توصیف یک ایستگاه',
  paletteItemExport: 'برون‌بری اندازه‌گیری‌ها',
  paletteRunDescription: 'خاک، هیدرولوژی، فرسایش یا کربن',
  paletteDescribeDescription: 'خلاصه نود روز گذشته',
  paletteExportDescription: 'CSV همه نقاط نمونه‌برداری',
  boundaryTitle: 'این بخش رندر نشد',
  boundaryBody: 'قرائت‌های این ایستگاه بارگذاری نشد. بقیه صفحه بی‌تأثیر است.',
  boundaryRetry: 'تلاش دوباره',
  skeletonCaption: 'در حال بارگذاری نقاط نمونه‌برداری',
};

export const sampleText: Record<'fa' | 'en', SampleText> = { fa, en };

/**
 * The English text for the keys HEAD's `en.json` predates.
 *
 * `en.json` was emptied three times in one session — twice by the applier's prune
 * branch reaching the reference catalogue, and once by a diagnostic of mine that
 * opened the file with the truncate flag. Restoring it from HEAD brought back an
 * older file: HEAD has 30 namespaces and 1,267 keys, the working tree had 35 and
 * 1,429. The 162 keys below were added by work committed after HEAD and existed
 * only in the working tree.
 *
 * Key names come from the Persian catalogue, which was never damaged. A first
 * attempt guessed plausible names — `why.problemTitle`, `manual.cropCalendar` —
 * and the message-usage gate rejected every one, because the pages ask for
 * `why.whatTitle` and `manual.columnNote`. Key names are a contract with the code
 * that reads them; they are not reconstructed from meaning.
 */
export const MISSING_NAMESPACES = {
  footer: {
    sitemap: 'Sitemap',
    techStack: 'Built for broad accessibility',
    navTitle: 'Public links',
  },

  nav: { modelCount: 'Model count' },

  brand: {
    description: 'Ecological intelligence for soil, water, climate and livelihoods.',
  },

  accessibility: {
    standardTitle: 'Standards applied',
    standardDesc:
      'The site targets WCAG 2.2 level AA. Automated checks do not replace manual verification with people.',
    feedbackTitle: 'Reporting an accessibility barrier',
    feedbackDesc:
      'If you hit a barrier, report the page in question. We will resolve it in the next update cycle.',
  },

  ai: {
    sourceRule: 'Every answer must cite its source or be labelled a model draft.',
    limitsTitle: 'Declared limits',
    nextTitle: 'Next step',
  },

  developers: {
    docsTitle: 'API documentation',
    docsDesc:
      'Every endpoint is documented with request and response examples, rate limits and error codes.',
    toolsTitle: 'Developer tools',
    toolsDesc: 'The tools include generated clients, test collections and integration examples.',
    changesTitle: 'Change log',
    changesDesc: 'Every API change is tied to a version and published in the change log.',
    publicNote:
      'The public environment is read-only. Tests and writes are authenticated and limited to permitted operations.',
  },

  evidence: {
    refsTitle: 'Method and references',
    refs: [
      'Soil modelling and water-balance methods',
      'FAO-56 standards for evapotranspiration',
      'Sampling and quality-control protocols',
    ],
    limitsTitle: 'Declared limits',
    nextTitle: 'Next step',
  },

  learn: {
    title: 'Content and training',
    lead: 'Video lessons, a bilingual glossary and operational guides for use in the field.',
  },

  legal: {
    termsTitle: 'Terms of use',
    termsBody:
      'Using the platform means accepting these terms. The project does not claim external certifications it has not verified.',
    privacyTitle: 'Personal data',
    privacyBody:
      'We use personal data to provide the service requested. We do not share identifying data for commercial purposes.',
    cookiesTitle: 'Cookies and language',
    cookiesBody:
      'We use one technical cookie to remember the chosen language; you can change it at any time in your browser settings.',
  },

  services: {
    farmersTitle: 'For agricultural producers',
    farmersDesc:
      'Crop planning, irrigation, soil fertility and water-resource management with reasoned recommendations.',
    institutionsTitle: 'For institutions',
    institutionsDesc: 'At-risk area mapping, water-resource planning and compliance reporting.',
    researchersTitle: 'For researchers and universities',
    researchersDesc: 'Scientific models, open datasets, a compute environment and reproducible processing.',
    pilotCta: 'Request a pilot session',
    pilotNote: 'Pilot sites are limited and selected on the basis of the data.',
  },

  trust: {
    provenanceTitle: 'Provenance explorer',
    provenanceDesc: 'Follow any datum to the service, the dataset image and the acquisition date.',
    registryTitle: 'Carbon registry',
    registryDesc:
      'The carbon credits the project generates are accessible and verifiable; the blockchain address is not available yet.',
    disclosureTitle: 'Responsible disclosure',
    disclosureDesc: 'Vulnerabilities are disclosed privately, without exposing user data.',
    statusCta: 'See the service status',
  },

  statusPage: {
    science: 'Scientific services',
    storage: 'Storage',
    operational: 'Operational',
    available: 'Available',
    requestUnavailable: 'The request could not be completed at this time.',
  },

  public: {
    channels: {
      title: 'Access channels',
      lead: 'The same platform, on whichever device the reader actually has.',
      provenanceLabel: 'Source of the claim',
      whatTitle: 'What this is',
      whatLead: 'One contract, four ways to reach it.',
      whatDesc:
        'The gateway decides which channel can serve which surface, and the client renders whichever it can.',
      audience: 'Farmers, cooperatives, researchers, planners and their funders',
      channels: 'Available channels',
      webPwa: 'Web and installable app',
      mobileApp: 'Mobile app',
      ussd: 'USSD',
      sms: 'SMS',
      voice: 'Voice',
      telegram: 'Telegram',
      evidenceItems: [
        'The status shown is the status the channel endpoint reports, read at request time.',
        'A channel that cannot be reached says so rather than falling back silently.',
      ],
      limitsItems: [
        'A channel narrower than a form can only carry a short set of fields.',
        'A channel that is down cannot be described as available.',
      ],
      nextItems: [
        'Choose the channel your device actually supports.',
        'Read the channel status before relying on it.',
      ],
      ussdLabel: 'USSD',
      ussdBody: 'Works on any handset with a keypad. No data plan required.',
      smsLabel: 'SMS',
      smsBody:
        'Short text updates for the state a farmer needs without opening anything, and only for events they have subscribed to.',
      voiceLabel: 'Voice',
      voiceBody: 'Guidance read aloud for readers who cannot use a screen.',
      webLabel: 'Web',
      webBody: 'The full interface, for a device that can show a screen.',
      whatsappLabel: 'WhatsApp',
      whatsappBody: 'Marketplace notices on a channel many producers already use.',
    },
    visit: {
      title: 'Farm visit',
      lead: 'A guide to observing the pilot sites and recording what you see.',
      provenanceLabel: 'Source of the claim',
      whatTitle: 'What this is',
      whatLead: 'Requesting a visit, and what happens next.',
      whatDesc:
        'A visit request is posted to the gateway. No date is promised until the request has been answered.',
      audience: 'Farmers, cooperatives, researchers and the teams hosting visits',
      visitSteps: 'The steps of a visit',
      s1_title: 'Agree the purpose',
      s1_desc: 'What the visit is for, agreed before anyone travels.',
      s2_title: 'Record the site',
      s2_desc: 'The location, with the coordinates the gateway holds.',
      s3_title: 'Observe',
      s3_desc: 'What was seen, recorded against the site rather than remembered later.',
      s4_title: 'Submit the observation',
      s4_desc: 'The observation is posted to the gateway, which stores it against the site.',
      scheduleVisit: 'Request a visit',
      body: 'The visit request is posted to the gateway.',
      visitNote: 'No date is promised until the request has been answered.',
    },
    cta: {
      title: 'Take part',
      lead: 'Your way into the market, the scientific engine and the training starts here.',
      provenanceLabel: 'Source of the claim',
      whatTitle: 'What this is',
      whatLead: 'Four paths, each posting to a real endpoint.',
      whatDesc:
        'Choose the path that matches your work. Nothing on this page posts anywhere that does not exist.',
      audience: 'Farmers, cooperatives, researchers, planners and their funders',
      primaryCTAs: 'The paths',
      cta1_title: 'Enter the market',
      cta1_desc: 'Browse, list and settle, with every order traceable.',
      cta1_action: 'See the marketplace',
      cta2_title: 'Use the scientific engine',
      cta2_desc: 'Run a soil, hydrology, climate or carbon model.',
      cta2_action: 'Open the engine',
      cta3_title: 'Read the field manual',
      cta3_desc: 'Reference tables and guides for the work itself.',
      cta3_action: 'Open the manual',
      cta4_title: 'Check the platform',
      cta4_desc: 'What the verification suite found, including its failures.',
      cta4_action: 'See the status',
      evidenceItems: [
        'Each path posts to an endpoint the gateway publishes.',
        'A path that cannot be reached says so rather than appearing to work.',
      ],
      limitsItems: [
        'A path is only as good as the contract behind it; the contract is linked.',
        'Nothing on this page promises a result the checks have not demonstrated.',
      ],
      nextItems: ['Choose one path rather than all four.', 'Read the contract before you rely on it.'],
      body: 'Choose the path that matches your work. Each one posts to a real endpoint.',
      optionsTitle: 'Where to start',
      farmersLink: 'I grow something',
      governmentLink: 'I work for a public body',
      investorsLink: 'I fund work like this',
      ngosLink: 'I work for a non-profit',
      newsletterBody: 'Occasional notes on what changed, and what the checks found.',
      newsletterConsent: 'Send me the newsletter',
      newsletterSubmit: 'Subscribe',
    },
  },

  why: {
    title: 'Why Eco Nojin?',
    lead: 'This page says only what the checks that were run and the gateway counters support. Anything the platform cannot demonstrate is declared unavailable rather than filled in.',
    whatTitle: 'What this platform is',
    whatLead: 'One integrated ecological intelligence platform: a scientific engine, an API gateway, an offline-first client and an event bus.',
    whatDesc: 'Soil, hydrology, climate, erosion and carbon modelling behind one contract, with a client that works without a network.',
    audience: 'Farmers, cooperatives, researchers, planners and their funders',
    problem: 'The problem',
    solution: 'This platform’s answer',
    problemSolutionTable: 'Problem and answer',
    provenanceLabel: 'Source of the claim',
    problemRows: [
      {
        problem: 'A farmer offline cannot reach a dashboard that assumes a connection.',
        solution:
          'The client holds the reference datasets and declares which surface is unavailable rather than showing a stale number as a current one.',
      },
      {
        problem: 'A model result arrives with no way to tell a measurement from an estimate.',
        solution:
          'Every surface carries a provenance stamp naming the source, the method, and whether the value is verified.',
      },
      {
        problem: 'A claim with no executed check behind it.',
        solution:
          'The only source of the platform’s claims is the verification suite, and its result is read live from the gateway.',
      },
    ],
    evidenceItems: [
      'Every claim on this page is read at request time from the executed verification suite, not from a stored summary.',
      'The result shown is the result of the run, including a failing run.',
    ],
    limitsItems: [
      'A model that does not apply to your soil is shown as not applying to your soil.',
      'Where a value is reported rather than measured, the page says so rather than presenting the two as the same thing.',
    ],
    nextItems: [
      'Read the methodology and the assumptions behind each model.',
      'Check the verification suite, including its failures.',
    ],
  },

  sponsors: {
    region_label: 'Funding disclosure',
    disclosure: 'This section is funded by {sponsor}.',
    policy_title: 'Sponsorship policy',
    policy_intro:
      'Sponsorship means a named supporter is recognised for work this platform does. It is not advertising.',
    no_ads: 'We run no algorithmic advertising. There is no ad network, no third-party ad SDK, no view tracking and no behavioural targeting in this product.',
    no_targeting:
      'A sponsorship response carries no user, device or referrer data, so there is no customisable advertising surface.',
    contextual:
      'A sponsor acknowledgement appears only on the service surface the sponsor funded. It never appears next to a recommendation we give a farmer.',
    no_advisory:
      'There is no sponsor placement on agronomy, payment, settlement or low-bandwidth surfaces.',
    transparency:
      'Every current sponsor is listed on this page, including any that has been suspended or ended, with the reason.',
    green_claims:
      'Every sponsor re-confirms quarterly that its own environmental claims are still documented. A sponsor that does not is suspended.',
    current_sponsors: 'Current sponsors',
    become: 'How sponsorship works',
    none: 'No sponsor is listed at present.',
  },

  manual: {
    back: 'Back to the site list',
    columnNote:
      'Column names are the dataset field names. The interface adds no unit or label the gateway did not return.',
    tableCaption: 'Rows returned from the reference dataset',
    truncated: 'Showing {shown} of {total} rows the gateway reported',
    offline: 'The device is offline; the request never reached the gateway.',
    sites: {
      title: 'Reference climate sites',
      description:
        'Sites registered in the reference dataset, with location, elevation and climate classification. Every column is a field the gateway returns.',
      emptyTitle: 'The site dataset is empty',
      emptyDescription: 'The gateway answered but returned no rows.',
      searchTitle: 'Site search',
      searchLabel: 'Search sites',
      searchPlaceholder: 'Site id, country or province',
      searchSubmit: 'Search',
      searchHint: 'The gateway searches the site_id, country and province fields with one value.',
      searching: 'Search results for “{search}”',
      emptySearch: 'No site matched “{search}”.',
    },
    site: {
      title: 'Site {siteId}',
      description: 'The record the reference dataset holds for this site.',
      back: 'Back to the site list',
      offline: 'The device is offline.',
      related: 'Datasets related to this site',
      relatedNormals: 'Climate normals',
      relatedWeather: 'Daily weather',
    },
    normals: {
      title: 'Climate normals',
      description: 'Long-run averages for this site, over the period the dataset states.',
      emptyTitle: 'No climate normals',
      emptyDescription: 'The gateway answered but returned no rows for this site.',
      backToSite: 'Back to the site',
    },
    weather: {
      title: 'Daily weather',
      description: 'Daily observations for this site, with the station and time of each.',
      emptyTitle: 'No weather observations',
      emptyDescription: 'The gateway answered but returned no rows for this site.',
      backToSite: 'Back to the site',
    },
    crops: {
      title: 'Crop calendar',
      description: 'Sowing and harvest windows per crop and region, from the tables the engine ships.',
      emptyTitle: 'No crop calendar',
      emptyDescription: 'The gateway answered but returned no rows.',
    },
    soil: {
      title: 'Soil regions',
      description: 'The soil regions the manual describes, with the classification each follows.',
      emptyTitle: 'No soil regions',
      emptyDescription: 'The gateway answered but returned no rows.',
    },
    calendar: {
      title: 'Growing calendar',
      description: 'The growing window per crop, as the engine reports it.',
      emptyTitle: 'No growing calendar',
      emptyDescription: 'The gateway answered but returned no rows.',
    },
    status: {
      title: 'Manual status',
      description: 'What the manual service reports about its own content.',
      back: 'Back',
      present: 'Published',
      missing: 'Not yet written',
      missingDescription: 'This section is declared in the catalogue but has no text yet.',
      size: 'Size',
      tables: 'Tables',
      tableCaption: 'The tables the manual holds',
      tableName: 'Table',
      tableRows: 'Rows',
      emptyDescription: 'The gateway answered but returned no rows.',
    },
  },

  surface: {
    back: 'Back',
    unverifiedNote:
      'The gateway reported these values but did not mark them verified. A reported value is not a measured one: the platform shows what the gateway returned and claims nothing further.',
    verifiedNote: 'The gateway marked this pass verified.',
    shapeNote:
      "The published contract for this path declares no fields, so the values below appear exactly as the gateway returned them and under the gateway's own key names. Nothing on this page is translated, rounded or verified.",
    emptyTitle: 'Nothing was returned',
    emptyDescription: 'The gateway answered but had nothing to show with it.',
    dashboards: {
      emptyTitle: 'The gateway returned no dashboard data',
      emptyDescription: 'The dashboard path answered but carried no data field.',
      full: {
        title: 'Full public dashboard',
        description: 'The whole public dashboard response in one answer.',
      },
      projects: { title: 'Carbon projects', description: 'The public list of projects the gateway reports.' },
      carbon: { title: 'Carbon', description: 'The public carbon summary the gateway reports.' },
      analytics: {
        title: 'Platform analytics',
        description: 'The public analytics counters the gateway reports.',
      },
      weather: { title: 'Weather', description: 'The public weather summary the gateway reports.' },
      satellite: { title: 'Satellite', description: 'The public satellite summary the gateway reports.' },
      soil: { title: 'Soil', description: 'The public soil summary the gateway reports.' },
      mrv: {
        title: 'Measurement, reporting and verification',
        description: 'The public MRV summary the gateway reports.',
      },
      simulations: {
        title: 'Simulations',
        description: 'The public simulation summary the gateway reports.',
      },
      tourism: { title: 'Tourism', description: 'The public tourism summary the gateway reports.' },
      test: {
        title: 'Router reachability',
        description:
            'The gateway reports whether this router is serving. It is a reachability check, not a claim about the platform.',
      },
    },
    market: {
      emptyTitle: 'The gateway returned no data',
      emptyDescription: 'The path answered but had nothing to show.',
      stats: {
          title: 'Marketplace statistics',
          description: 'Counters read from the marketplace statistics endpoint.',
      },
      producers: {
          title: 'Producers',
          description: 'The producers the marketplace has registered.',
      },
    },
    content: {
      title: 'Content search',
      description: 'Search the published learning library.',
      searchTitle: 'Search content',
      searchLabel: 'Search content',
      searchPlaceholder: 'A word or phrase',
      searchSubmit: 'Search',
      resultsFor: 'Results for “{search}”',
      noResults: 'Nothing matched “{search}”.',
      emptyDescription: 'The gateway answered but had nothing to show with it.',
    },
  },

  market: {
    escrow: {
      title: 'Escrow',
      escrowStatus: 'The escrow state the gateway reports.',
    amount: 'Amount',
    contractHash: 'Contract hash',
    orderId: 'Order id',
    parties: 'Parties',
    buyer: 'Buyer',
    seller: 'Seller',
    arbitrator: 'Arbitrator',
    platform: 'Platform',
    eventTimeline: 'Event timeline',
    signed: 'Signed',
    notSigned: 'Not signed',
    escrowComplete: 'The escrow is complete.',
    releaseFunds: 'Release funds',
    cancelEscrow: 'Cancel the escrow',
    openDispute: 'Open a dispute',
    dataUnavailable:
    'Live escrow data is unavailable; the current detail shown comes from the demo record.',
    confirmRelease: 'Release the funds?',
    confirmReleaseDesc: 'This action only proceeds after authorisation and a review of the conditions.',
    confirmReleaseButton: 'Confirm release',
    escrowProvenance: 'Source of the escrow',
    released: 'The funds were released',
    cancelled: 'The escrow was cancelled',
    },
  },

  offline: {
    code: 'Connection unavailable',
    title: 'Offline mode',
    description: 'Cached data is available; retry when you want to refresh.',
    retry: 'Try again',
  },
};

/**
 * `offline.*` is not a restored key — it is a live one.
 *
 * `ResourcePage` uses it for the offline state of every one of the 128 generated
 * pages, and it existed only in `en` and `fa`. A reader of `/hi/hydroma/carbon`
 * with no connection therefore got an English sentence inside an otherwise
 * Hindi page, which is the exact failure the fifty-three inline dictionaries
 * caused. Found by looking at the rendered page, not by a gate: the string was
 * valid in the reference catalogue, so `check-message-usage` was satisfied.
 */
export const OFFLINE = {
  fa: {
    code: 'اتصال در دسترس نیست',
    title: 'حالت آفلاین',
    description: 'داده‌های ذخیره‌شده در دسترس هستند؛ برای به‌روزرسانی دوباره تلاش کنید.',
    retry: 'تلاش دوباره',
  },
  ar: {
    code: 'الاتصال غير متاح',
    title: 'وضع عدم الاتصال',
    description: 'البيانات المخزّنة متاحة؛ أعد المحاولة حين تريد التحديث.',
    retry: 'أعد المحاولة',
  },
  ur: {
    code: 'کنکشن دستیاب نہیں',
    title: 'آف لائن موڈ',
    description: 'کیش شدہ ڈیٹا دستیاب ہے؛ تازہ کرنے کے لیے دوبارہ کوشش کریں۔',
    retry: 'دوبارہ کوشش کریں',
  },
  de: {
    code: 'Verbindung nicht verfügbar',
    title: 'Offline-Modus',
    description: 'Zwischengespeicherte Daten sind verfügbar; versuchen Sie es erneut, um zu aktualisieren.',
    retry: 'Erneut versuchen',
  },
  es: {
    code: 'Conexión no disponible',
    title: 'Modo sin conexión',
    description: 'Los datos en caché están disponibles; inténtelo de nuevo cuando quiera actualizar.',
    retry: 'Reintentar',
  },
  fr: {
    code: 'Connexion indisponible',
    title: 'Mode hors ligne',
    description: 'Les données en cache sont disponibles ; réessayez pour actualiser.',
    retry: 'Réessayer',
  },
  hi: {
    code: 'कनेक्शन उपलब्ध नहीं',
    title: 'ऑफ़लाइन मोड',
    description: 'कैश किया गया डेटा उपलब्ध है; ताज़ा करने के लिए पुनः प्रयास करें।',
    retry: 'पुनः प्रयास करें',
  },
  it: {
    code: 'Connessione non disponibile',
    title: 'Modalità offline',
    description: 'I dati in cache sono disponibili; riprova quando vuoi aggiornare.',
    retry: 'Riprova',
  },
  ms: {
    code: 'Sambungan tidak tersedia',
    title: 'Mod luar talian',
    description: 'Data cache tersedia; cuba lagi apabila anda mahu memuat semula.',
    retry: 'Cuba lagi',
  },
  pt: {
    code: 'Ligação indisponível',
    title: 'Modo offline',
    description: 'Os dados em cache estão disponíveis; tente novamente quando quiser atualizar.',
    retry: 'Tentar novamente',
  },
  ru: {
    code: 'Соединение недоступно',
    title: 'Автономный режим',
    description: 'Кэшированные данные доступны; повторите попытку, когда захотите обновить.',
    retry: 'Повторить попытку',
  },
  zh: {
    code: '连接不可用',
    title: '离线模式',
    description: '缓存数据可用；需要刷新时请重试。',
    retry: '重试',
  },
  bn: {
    code: 'সংযোগ অপ্রাপ্য',
    title: 'অফলাইন মোড',
    description: 'ক্যাশ করা ডেটা উপলব্ধ; নতুন করতে চাইলে আবার চেষ্টা করুন।',
    retry: 'আবার চেষ্টা করুন',
  },
};

/** The two `pageMeta` slugs added after HEAD, also lost with the file. */
export const MISSING_PAGE_META = {
  'learning-learn-legal-locale-slug': [
    'Legal text',
    'One legal text in one locale, with the version the record carries.',
  ],
  'learning-learn-legal-locale-slug-versions': [
    'Version history',
    'Every version of a legal text, with the change recorded for each.',
  ],
};

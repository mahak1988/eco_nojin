const fs = require('fs');
const path = require('path');

const file = path.join(__dirname, 'apps/web/src/i18n/messages.json');
const data = JSON.parse(fs.readFileSync(file, 'utf8'));

const namespaces = [
  'projectStory',
  'team',
  'orgStructure',
  'media',
  'mission',
  'vision',
  'dataEthics',
  'transparency',
  'environmental',
  'stakeholderRights',
  'scientificEngine',
  'marketplaceIntro',
  'supervisoryPanel',
  'researchInstitute',
  'education',
  'simplePhoneAccess',
  'mobileApp',
  'systemToSystem',
  'farmer',
  'orchardist',
  'livestock',
  'cooperative',
  'localBazaar',
  'government',
  'investor',
  'privateCompany',
  'ecotourism'
];

const minimalKeys = {
  heroTitle: '',
  heroDesc: '',
  servicesTitle: '',
  learnMore: '',
  solutionsTitle: '',
  viewAll: '',
  explore: '',
  visitors: '',
  toolsTitle: '',
  storiesTitle: '',
  ctaTitle: '',
  ctaDesc: '',
  ctaExplore: '',
  ctaContact: '',
  serv1Title: '', serv1Desc: '', serv1F1: '', serv1F2: '', serv1F3: '',
  serv2Title: '', serv2Desc: '', serv2F1: '', serv2F2: '', serv2F3: '',
  serv3Title: '', serv3Desc: '', serv3F1: '', serv3F2: '', serv3F3: '',
  serv4Title: '', serv4Desc: '', serv4F1: '', serv4F2: '', serv4F3: '',
  serv5Title: '', serv5Desc: '', serv5F1: '', serv5F2: '', serv5F3: '',
  serv6Title: '', serv6Desc: '', serv6F1: '', serv6F2: '', serv6F3: '',
  sol1Name: '', sol1Target: '', sol1Benefit: '', sol1Status: '', sol1Desc: '',
  sol2Name: '', sol2Target: '', sol2Benefit: '', sol2Status: '', sol2Desc: '',
  sol3Name: '', sol3Target: '', sol3Benefit: '', sol3Status: '', sol3Desc: '',
  sol4Name: '', sol4Target: '', sol4Benefit: '', sol4Status: '', sol4Desc: '',
  sol5Name: '', sol5Target: '', sol5Benefit: '', sol5Status: '', sol5Desc: '',
  sol6Name: '', sol6Target: '', sol6Benefit: '', sol6Status: '', sol6Desc: '',
  tool1Title: '', tool1Desc: '', tool1Status: '',
  tool2Title: '', tool2Desc: '', tool2Status: '',
  tool3Title: '', tool3Desc: '', tool3Status: '',
  tool4Title: '', tool4Desc: '', tool4Status: '',
  tool5Title: '', tool5Desc: '', tool5Status: '',
  tool6Title: '', tool6Desc: '', tool6Status: '',
  dest1Name: '', dest1Region: '', dest1Type: '', dest1Visitors: '', dest1Sustainability: '', dest1Desc: '',
  dest2Name: '', dest2Region: '', dest2Type: '', dest2Visitors: '', dest2Sustainability: '', dest2Desc: '',
  dest3Name: '', dest3Region: '', dest3Type: '', dest3Visitors: '', dest3Sustainability: '', dest3Desc: '',
  story1Name: '', story1Region: '', story1Project: '', story1Improvement: '', story1Quote: '',
  story2Name: '', story2Region: '', story2Project: '', story2Improvement: '', story2Quote: '',
  story3Name: '', story3Region: '', story3Project: '', story3Improvement: '', story3Quote: '',
};

function addNamespace(localeObj, ns) {
  if (!localeObj[ns]) {
    localeObj[ns] = {};
    for (const key of Object.keys(minimalKeys)) {
      localeObj[ns][key] = key;
    }
  }
}

for (const locale of ['fa', 'en']) {
  if (!data[locale]) data[locale] = {};
  for (const ns of namespaces) {
    addNamespace(data[locale], ns);
  }
}

fs.writeFileSync(file, JSON.stringify(data, null, 2));
console.log('Added missing namespaces');
# Company Source Discovery Report

## Summary

- generic_html: 14
- login_required: 26
- not_found: 17
- supported_ats: 3

## Suggested Actions

- `supported_ats`: Review and write confirmed `ats_type` / `ats_feed_url` back to `nz_it_company_targets.yaml`.
- `generic_html`: Manually inspect before using for scanning; first version may only support single job pages reliably.
- `login_required`: Keep in manual workflow; use manual login plus `manual-assist`.
- `fetch_failed` / `not_found`: Recheck the career URL or skip for now.

## Results

### ANZ New Zealand

- Status: `login_required`
- Confidence: `medium`
- Checked URL: https://www.anz.co.nz/about-us/careers/
- Suggested ats_type: `none`
- Suggested ats_feed_url: none
- Evidence:
  - Page text or URL suggests login/account registration is required.

### ASB Bank

- Status: `login_required`
- Confidence: `medium`
- Checked URL: https://www.asb.co.nz/
- Suggested ats_type: `none`
- Suggested ats_feed_url: none
- Evidence:
  - Page text or URL suggests login/account registration is required.

### Accenture New Zealand

- Status: `generic_html`
- Confidence: `low`
- Checked URL: https://www.accenture.com/nz-en/careers
- Suggested ats_type: `generic_html`
- Suggested ats_feed_url: https://www.accenture.com/nz-en/careers
- Evidence:
  - Career page contains job-related text but no supported ATS feed was found.

### Amazon Web Services New Zealand

- Status: `generic_html`
- Confidence: `low`
- Checked URL: https://amazon.jobs/content/en/teams/devices-services
- Suggested ats_type: `generic_html`
- Suggested ats_feed_url: https://amazon.jobs/content/en/teams/devices-services
- Evidence:
  - Career page contains job-related text but no supported ATS feed was found.

### Auckland Council

- Status: `login_required`
- Confidence: `medium`
- Checked URL: https://careers.aucklandcouncil.govt.nz/
- Suggested ats_type: `none`
- Suggested ats_feed_url: none
- Evidence:
  - Page text or URL suggests login/account registration is required.

### BNZ

- Status: `generic_html`
- Confidence: `low`
- Checked URL: https://www.bnz.co.nz/
- Suggested ats_type: `generic_html`
- Suggested ats_feed_url: https://www.bnz.co.nz/
- Evidence:
  - Career page contains job-related text but no supported ATS feed was found.

### Datacom

- Status: `not_found`
- Confidence: `none`
- Checked URL: https://datacom.com/nz/en/careers
- Suggested ats_type: `none`
- Suggested ats_feed_url: none
- Evidence:
  - No supported ATS link found in checked pages.
- Error: `HTTP Error 403: Forbidden; HTTP Error 403: Forbidden`

### Department of Internal Affairs

- Status: `generic_html`
- Confidence: `low`
- Checked URL: https://www.dia.govt.nz/Careers
- Suggested ats_type: `generic_html`
- Suggested ats_feed_url: https://www.dia.govt.nz/Careers
- Evidence:
  - Career page contains job-related text but no supported ATS feed was found.

### EROAD

- Status: `not_found`
- Confidence: `none`
- Checked URL: https://www.eroad.co.nz/careers/
- Suggested ats_type: `none`
- Suggested ats_feed_url: none
- Evidence:
  - No supported ATS link found in checked pages.
- Error: `HTTP Error 404: Not Found`

### Fisher & Paykel Healthcare

- Status: `not_found`
- Confidence: `none`
- Checked URL: https://www.fphcare.com/nz/careers/
- Suggested ats_type: `none`
- Suggested ats_feed_url: none
- Evidence:
  - No supported ATS link found in checked pages.

### Gentrack

- Status: `login_required`
- Confidence: `medium`
- Checked URL: https://www.gentrack.com/careers/
- Suggested ats_type: `none`
- Suggested ats_feed_url: none
- Evidence:
  - Page text or URL suggests login/account registration is required.

### Google New Zealand

- Status: `login_required`
- Confidence: `medium`
- Checked URL: https://www.google.com/about/careers/applications/
- Suggested ats_type: `none`
- Suggested ats_feed_url: none
- Evidence:
  - Page text or URL suggests login/account registration is required.

### Health New Zealand Te Whatu Ora

- Status: `login_required`
- Confidence: `medium`
- Checked URL: https://www.tewhatuora.govt.nz/careers/
- Suggested ats_type: `none`
- Suggested ats_feed_url: none
- Evidence:
  - Page text or URL suggests login/account registration is required.

### Inland Revenue

- Status: `login_required`
- Confidence: `medium`
- Checked URL: https://www.ird.govt.nz/about-us/careers
- Suggested ats_type: `none`
- Suggested ats_feed_url: none
- Evidence:
  - Page text or URL suggests login/account registration is required.

### Jade Software

- Status: `login_required`
- Confidence: `medium`
- Checked URL: https://www.jadeworld.com/careers/
- Suggested ats_type: `none`
- Suggested ats_feed_url: none
- Evidence:
  - Page text or URL suggests login/account registration is required.

### Kiwibank

- Status: `login_required`
- Confidence: `medium`
- Checked URL: https://www.kiwibank.co.nz/about-us/careers/
- Suggested ats_type: `none`
- Suggested ats_feed_url: none
- Evidence:
  - Page text or URL suggests login/account registration is required.

### Microsoft New Zealand

- Status: `login_required`
- Confidence: `medium`
- Checked URL: https://jobs.careers.microsoft.com/
- Suggested ats_type: `none`
- Suggested ats_feed_url: none
- Evidence:
  - Page text or URL suggests login/account registration is required.

### Ministry of Business Innovation and Employment

- Status: `not_found`
- Confidence: `none`
- Checked URL: https://www.mbie.govt.nz/about/work-for-us/
- Suggested ats_type: `none`
- Suggested ats_feed_url: none
- Evidence:
  - No supported ATS link found in checked pages.

### New Zealand Transport Agency Waka Kotahi

- Status: `not_found`
- Confidence: `none`
- Checked URL: https://www.nzta.govt.nz/about-us/careers/
- Suggested ats_type: `none`
- Suggested ats_feed_url: none
- Evidence:
  - No supported ATS link found in checked pages.

### One NZ

- Status: `login_required`
- Confidence: `medium`
- Checked URL: https://one.nz/careers/development-benefits/
- Suggested ats_type: `none`
- Suggested ats_feed_url: none
- Evidence:
  - Page text or URL suggests login/account registration is required.

### Orion Health

- Status: `generic_html`
- Confidence: `low`
- Checked URL: https://orionhealth.com/careers/
- Suggested ats_type: `generic_html`
- Suggested ats_feed_url: https://orionhealth.com/careers/
- Evidence:
  - Career page contains job-related text but no supported ATS feed was found.

### Pushpay

- Status: `login_required`
- Confidence: `medium`
- Checked URL: https://pushpay.com/
- Suggested ats_type: `none`
- Suggested ats_feed_url: none
- Evidence:
  - Page text or URL suggests login/account registration is required.

### Qrious

- Status: `not_found`
- Confidence: `none`
- Checked URL: https://www.qrious.co.nz/careers/
- Suggested ats_type: `none`
- Suggested ats_feed_url: none
- Evidence:
  - No supported ATS link found in checked pages.

### Rocket Lab

- Status: `not_found`
- Confidence: `none`
- Checked URL: https://www.rocketlabusa.com/careers/
- Suggested ats_type: `none`
- Suggested ats_feed_url: none
- Evidence:
  - No supported ATS link found in checked pages.

### Serko

- Status: `generic_html`
- Confidence: `low`
- Checked URL: https://www.serko.com/careers
- Suggested ats_type: `generic_html`
- Suggested ats_feed_url: https://www.serko.com/careers
- Evidence:
  - Career page contains job-related text but no supported ATS feed was found.

### Spark New Zealand

- Status: `not_found`
- Confidence: `none`
- Checked URL: https://www.spark.co.nz/online/careers/
- Suggested ats_type: `none`
- Suggested ats_feed_url: none
- Evidence:
  - No supported ATS link found in checked pages.

### Stats NZ

- Status: `not_found`
- Confidence: `none`
- Checked URL: https://www.stats.govt.nz/about-us/careers/
- Suggested ats_type: `none`
- Suggested ats_feed_url: none
- Evidence:
  - No supported ATS link found in checked pages.
- Error: `HTTP Error 404: Not Found`

### Theta

- Status: `not_found`
- Confidence: `none`
- Checked URL: https://www.theta.co.nz/careers/
- Suggested ats_type: `none`
- Suggested ats_feed_url: none
- Evidence:
  - No supported ATS link found in checked pages.

### Trade Me

- Status: `login_required`
- Confidence: `medium`
- Checked URL: https://www.trademe.co.nz/careers
- Suggested ats_type: `none`
- Suggested ats_feed_url: none
- Evidence:
  - Page text or URL suggests login/account registration is required.

### Vista Group

- Status: `not_found`
- Confidence: `none`
- Checked URL: https://www.vistagroup.co.nz/careers/
- Suggested ats_type: `none`
- Suggested ats_feed_url: none
- Evidence:
  - No supported ATS link found in checked pages.
- Error: `HTTP Error 404: Not Found`

### Westpac New Zealand

- Status: `login_required`
- Confidence: `medium`
- Checked URL: https://www.westpac.co.nz/about-us/careers/
- Suggested ats_type: `none`
- Suggested ats_feed_url: none
- Evidence:
  - Page text or URL suggests login/account registration is required.

### Xero

- Status: `generic_html`
- Confidence: `low`
- Checked URL: https://www.xero.com/about/careers/
- Suggested ats_type: `generic_html`
- Suggested ats_feed_url: https://www.xero.com/about/careers/
- Evidence:
  - Career page contains job-related text but no supported ATS feed was found.

### 2degrees

- Status: `login_required`
- Confidence: `medium`
- Checked URL: https://www.2degrees.nz/termsofuse/careers-privacy-policy
- Suggested ats_type: `none`
- Suggested ats_feed_url: none
- Evidence:
  - Page text or URL suggests login/account registration is required.

### AUT

- Status: `generic_html`
- Confidence: `low`
- Checked URL: https://www.aut.ac.nz/about/careers-at-aut
- Suggested ats_type: `generic_html`
- Suggested ats_feed_url: https://www.aut.ac.nz/about/careers-at-aut
- Evidence:
  - Career page contains job-related text but no supported ATS feed was found.

### Air New Zealand

- Status: `not_found`
- Confidence: `none`
- Checked URL: https://careers.airnewzealand.co.nz/
- Suggested ats_type: `none`
- Suggested ats_feed_url: none
- Evidence:
  - No supported ATS link found in checked pages.

### AskNicely

- Status: `login_required`
- Confidence: `medium`
- Checked URL: https://www.asknicely.com/careers
- Suggested ats_type: `none`
- Suggested ats_feed_url: none
- Evidence:
  - Page text or URL suggests login/account registration is required.

### Auckland Airport

- Status: `not_found`
- Confidence: `none`
- Checked URL: https://corporate.aucklandairport.co.nz/careers
- Suggested ats_type: `none`
- Suggested ats_feed_url: none
- Evidence:
  - No supported ATS link found in checked pages.
- Error: `HTTP Error 403: Forbidden; HTTP Error 403: Forbidden`

### Auror

- Status: `login_required`
- Confidence: `medium`
- Checked URL: https://www.auror.co/careers
- Suggested ats_type: `none`
- Suggested ats_feed_url: none
- Evidence:
  - Page text or URL suggests login/account registration is required.

### Capgemini New Zealand

- Status: `generic_html`
- Confidence: `low`
- Checked URL: https://www.capgemini.com/in-en/careers/
- Suggested ats_type: `generic_html`
- Suggested ats_feed_url: https://www.capgemini.com/in-en/careers/
- Evidence:
  - Career page contains job-related text but no supported ATS feed was found.

### Chorus

- Status: `not_found`
- Confidence: `none`
- Checked URL: https://www.chorus.co.nz/careers
- Suggested ats_type: `none`
- Suggested ats_feed_url: none
- Evidence:
  - No supported ATS link found in checked pages.

### Christchurch City Council

- Status: `login_required`
- Confidence: `medium`
- Checked URL: https://www.ccc.govt.nz/
- Suggested ats_type: `none`
- Suggested ats_feed_url: none
- Evidence:
  - Page text or URL suggests login/account registration is required.

### Cin7

- Status: `login_required`
- Confidence: `medium`
- Checked URL: https://www.cin7.com/careers/
- Suggested ats_type: `none`
- Suggested ats_feed_url: none
- Evidence:
  - Page text or URL suggests login/account registration is required.

### ClearPoint

- Status: `supported_ats`
- Confidence: `high`
- Checked URL: https://clearpoint.digital/careers/
- Suggested ats_type: `lever`
- Suggested ats_feed_url: https://api.lever.co/v0/postings/clearpoint?mode=json
- Evidence:
  - Found supported ATS link: https://jobs.lever.co/clearpoint/

### Contact Energy

- Status: `generic_html`
- Confidence: `low`
- Checked URL: https://contact.co.nz/about-us/careers
- Suggested ats_type: `generic_html`
- Suggested ats_feed_url: https://contact.co.nz/about-us/careers
- Evidence:
  - Career page contains job-related text but no supported ATS feed was found.

### Deloitte New Zealand

- Status: `supported_ats`
- Confidence: `high`
- Checked URL: https://www.deloitte.com/nz/en/careers.html
- Suggested ats_type: `smartrecruiters`
- Suggested ats_feed_url: https://api.smartrecruiters.com/v1/companies/DeloitteNZ/postings
- Evidence:
  - Found supported ATS link: https://careers.smartrecruiters.com/DeloitteNZ

### EY New Zealand

- Status: `login_required`
- Confidence: `medium`
- Checked URL: https://www.ey.com/en_nz/careers
- Suggested ats_type: `none`
- Suggested ats_feed_url: none
- Evidence:
  - Page text or URL suggests login/account registration is required.

### Education Perfect

- Status: `login_required`
- Confidence: `medium`
- Checked URL: https://www.educationperfect.com/about-us/careers/
- Suggested ats_type: `none`
- Suggested ats_feed_url: none
- Evidence:
  - Page text or URL suggests login/account registration is required.

### Fonterra

- Status: `login_required`
- Confidence: `medium`
- Checked URL: https://www.fonterra.com/nz/en/careers.html
- Suggested ats_type: `none`
- Suggested ats_feed_url: none
- Evidence:
  - Page text or URL suggests login/account registration is required.

### Foodstuffs North Island

- Status: `not_found`
- Confidence: `none`
- Checked URL: https://www.foodstuffs.co.nz/careers
- Suggested ats_type: `none`
- Suggested ats_feed_url: none
- Evidence:
  - No supported ATS link found in checked pages.
- Error: `HTTP Error 404: Not Found`

### Fronde

- Status: `login_required`
- Confidence: `medium`
- Checked URL: https://www.fronde.com/careers/
- Suggested ats_type: `none`
- Suggested ats_feed_url: none
- Evidence:
  - Page text or URL suggests login/account registration is required.

### Fuel50

- Status: `generic_html`
- Confidence: `low`
- Checked URL: https://fuel50.com/careers/
- Suggested ats_type: `generic_html`
- Suggested ats_feed_url: https://fuel50.com/careers/
- Evidence:
  - Career page contains job-related text but no supported ATS feed was found.

### Gallagher

- Status: `generic_html`
- Confidence: `low`
- Checked URL: https://security.gallagher.com/en/careers
- Suggested ats_type: `generic_html`
- Suggested ats_feed_url: https://security.gallagher.com/en/careers
- Evidence:
  - Career page contains job-related text but no supported ATS feed was found.

### Genesis Energy

- Status: `not_found`
- Confidence: `none`
- Checked URL: https://www.genesisenergy.co.nz/careers
- Suggested ats_type: `none`
- Suggested ats_feed_url: none
- Evidence:
  - No supported ATS link found in checked pages.

### Halter

- Status: `login_required`
- Confidence: `medium`
- Checked URL: https://www.halterhq.com/careers
- Suggested ats_type: `none`
- Suggested ats_feed_url: none
- Evidence:
  - Page text or URL suggests login/account registration is required.

### Heartland Bank

- Status: `login_required`
- Confidence: `medium`
- Checked URL: https://www.heartland.co.nz/careers
- Suggested ats_type: `none`
- Suggested ats_feed_url: none
- Evidence:
  - Page text or URL suggests login/account registration is required.

### IBM New Zealand

- Status: `generic_html`
- Confidence: `low`
- Checked URL: https://www.ibm.com/careers/
- Suggested ats_type: `generic_html`
- Suggested ats_feed_url: https://www.ibm.com/careers/
- Evidence:
  - Career page contains job-related text but no supported ATS feed was found.

### IDEXX New Zealand

- Status: `login_required`
- Confidence: `medium`
- Checked URL: https://www.idexx.com/
- Suggested ats_type: `none`
- Suggested ats_feed_url: none
- Evidence:
  - Page text or URL suggests login/account registration is required.

### Inde Technology

- Status: `generic_html`
- Confidence: `low`
- Checked URL: https://www.inde.nz/careers/
- Suggested ats_type: `generic_html`
- Suggested ats_feed_url: https://www.inde.nz/careers/
- Evidence:
  - Career page contains job-related text but no supported ATS feed was found.

### Intergen

- Status: `not_found`
- Confidence: `none`
- Checked URL: https://www.intergen.co.nz/careers/
- Suggested ats_type: `none`
- Suggested ats_feed_url: none
- Evidence:
  - No supported ATS link found in checked pages.
- Error: `<urlopen error [Errno 11001] getaddrinfo failed>; <urlopen error [Errno 11001] getaddrinfo failed>`

### KPMG New Zealand

- Status: `supported_ats`
- Confidence: `high`
- Checked URL: https://kpmg.com/nz/en/home/careers.html
- Suggested ats_type: `lever`
- Suggested ats_feed_url: https://api.lever.co/v0/postings/kpmgnz?mode=json
- Evidence:
  - Found supported ATS link: https://jobs.lever.co/kpmgnz/83759813-bf72-40fb-a09d-70bcca8f4c23

from seoanalyzer import analyze

# Format seo audit report
def seo_audit(site):
    output = analyze(site, follow_links=False)
    page = output['pages'][0]
    details = {}
    warnings = {}
    for warning in page['warnings']:
        tokenized = [w.strip() for w in warning.split(':', 1)]
        if tokenized[0] in warnings:
            warnings[tokenized[0]]['count'] += 1
            warnings[tokenized[0]]['result'].append(tokenized[1])
        else:
            if len(tokenized) > 1:
                warnings[tokenized[0]] = {}
                warnings[tokenized[0]]['count'] = 1
                warnings[tokenized[0]]['result'] = []
                warnings[tokenized[0]]['result'].append(tokenized[1])
            else:
                warnings[tokenized[0]] = {}
                warnings[tokenized[0]]['count'] = 1
                warnings[tokenized[0]]['result'] = []

    details['url'] = page['url']
    details['title'] = page['title']
    details['description'] = page['description']
    details['word_count'] = page['word_count']
    details['error_count'] = len(page['warnings'])
    details['keywords'] = page['keywords'][:10]
    details['warnings'] = warnings

    return details

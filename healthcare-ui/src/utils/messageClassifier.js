const WARNING_PATTERNS = [
  /more than 24 hours/i,
  /più di 24 ore/i,
  /dati.*non.*aggiornati/i,
  /readings.*outdated/i,
  /old.*readings/i,
];

const ERROR_PATTERNS = [
  /couldn'?t find any information/i,
  /non ho trovato/i,
  /paziente non trovato/i,
  /patient not found/i,
  /nessun risultato/i,
  /no matching patients/i,
  /verifica il codice fiscale/i,
];

export function classifyMessage(content) {
  if (!content) return 'normal';

  for (const pattern of ERROR_PATTERNS) {
    if (pattern.test(content)) return 'error';
  }

  for (const pattern of WARNING_PATTERNS) {
    if (pattern.test(content)) return 'warning';
  }

  return 'normal';
}

export const WARNING_TEXT =
  'Information is based on readings taken more than 24 hours ago.';

export const ERROR_TEXT =
  "Couldn't find any information related to this request in the patient's records. Please check the request or try another query.";

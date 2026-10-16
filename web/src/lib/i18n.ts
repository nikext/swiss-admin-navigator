// UI strings in EN/DE/FR/IT. The answer language follows the question (the agent
// detects it); the switcher only changes the interface and the examples.

import type { Lang, Step } from "@/lib/contract";

export interface Strings {
  tagline: string;
  notice: string;
  noticeLong: string;
  language: string;
  newChat: string;
  logout: string;
  loginTitle: string;
  loginHelp: string;
  accessCode: string;
  enter: string;
  wrongCode: string;
  tooManyAttempts: string;
  askPlaceholder: string;
  send: string;
  examplesTitle: string;
  examples: string[];
  steps: Record<Step, string>;
  thinking: string;
  slowHint: string;
  sources: string;
  asOf: string;
  paragraph: string;
  letter: string;
  openArticle: string;
  quoteRemoved: string;
  cantonal: string;
  clarify: string;
  followUps: string;
  outOfScope: string;
  confidence: Record<"high" | "medium" | "low", string>;
  verification: Record<"passed" | "passed_after_retry" | "degraded" | "unavailable", string>;
  helpful: string;
  notHelpful: string;
  thanks: string;
  quotaLeft: (n: number, of: number) => string;
  quotaUser: string;
  quotaGlobal: string;
  errorGeneric: string;
  errorNetwork: string;
  close: string;
  authoritative: string;
  unofficialTranslation: string;
  machineTranslation: string;
  onFedlex: string;
  repealed: string;
  loading: string;
  articleError: string;
  fallback: string;
  you: string;
  assistant: string;
}

const en: Strings = {
  tagline: "Questions about Swiss federal law, answered with quoted articles.",
  notice: "Unofficial. Not legal advice.",
  noticeLong:
    "Unofficial tool. Not legal advice. Sources: Fedlex (fedlex.admin.ch). For decisions, contact the competent authority or a lawyer.",
  language: "Language",
  newChat: "New conversation",
  logout: "Sign out",
  loginTitle: "Enter access code",
  loginHelp: "This demo is invite-only to keep its costs bounded.",
  accessCode: "Access code",
  enter: "Continue",
  wrongCode: "That code is not valid.",
  tooManyAttempts: "Too many attempts. Please wait a few minutes.",
  askPlaceholder: "Ask about residence, work, social insurance, housing, tax or mobility…",
  send: "Ask",
  examplesTitle: "Try one of these",
  examples: [
    "How much rent deposit can my landlord ask for?",
    "What is the notice period during probation?",
    "Can I be dismissed while I am ill?",
    "How long do I have to take out health insurance after moving to Switzerland?",
    "How many years of residence do I need to apply for Swiss citizenship?",
    "Until when can I drive with my foreign driving licence?",
  ],
  steps: {
    search: "Searching the law",
    resolve: "Checking a citation",
    read: "Reading",
    browse: "Browsing the act",
    check: "Re-checking the quotes",
  },
  thinking: "Working on it…",
  slowHint: "Answers usually take 30–90 seconds: every quote is checked against the law text.",
  sources: "Sources",
  asOf: "as of",
  paragraph: "para.",
  letter: "let.",
  openArticle: "Show article text",
  quoteRemoved: "Quote removed: it could not be verified against the law text.",
  cantonal: "Cantonal and communal rules",
  clarify: "To answer precisely, I need to know",
  followUps: "You could also ask",
  outOfScope: "Outside what this tool can answer",
  confidence: { high: "High confidence", medium: "Medium confidence", low: "Low confidence" },
  verification: {
    passed: "All quotes verified",
    passed_after_retry: "Quotes verified after a correction",
    degraded: "Some quotes could not be verified and were removed",
    unavailable: "Quotes could not be checked",
  },
  helpful: "Helpful",
  notHelpful: "Not helpful",
  thanks: "Thanks for the feedback.",
  quotaLeft: (n, of) => `${n} of ${of} questions left today`,
  quotaUser: "You have reached today's question limit. Please come back tomorrow.",
  quotaGlobal: "The demo has reached its daily limit. Please come back tomorrow.",
  errorGeneric: "The assistant could not finish this answer. Please try again.",
  errorNetwork: "The connection was interrupted. Please try again.",
  close: "Close",
  authoritative: "authoritative",
  unofficialTranslation: "unofficial translation",
  machineTranslation: "Machine translation (unofficial)",
  onFedlex: "Open on Fedlex",
  repealed: "Not in force",
  loading: "Loading…",
  articleError: "The article could not be loaded.",
  fallback: "Not available in this language; showing German.",
  you: "You",
  assistant: "Navigator",
};

const de: Strings = {
  tagline: "Fragen zum Schweizer Bundesrecht, beantwortet mit zitierten Artikeln.",
  notice: "Inoffiziell. Keine Rechtsberatung.",
  noticeLong:
    "Inoffizielles Werkzeug. Keine Rechtsberatung. Quellen: Fedlex (fedlex.admin.ch). Für Entscheide wenden Sie sich an die zuständige Behörde oder eine Anwältin bzw. einen Anwalt.",
  language: "Sprache",
  newChat: "Neues Gespräch",
  logout: "Abmelden",
  loginTitle: "Zugangscode eingeben",
  loginHelp: "Diese Demo ist nur auf Einladung zugänglich, damit die Kosten begrenzt bleiben.",
  accessCode: "Zugangscode",
  enter: "Weiter",
  wrongCode: "Dieser Code ist ungültig.",
  tooManyAttempts: "Zu viele Versuche. Bitte warten Sie einige Minuten.",
  askPlaceholder: "Fragen zu Aufenthalt, Arbeit, Sozialversicherung, Wohnen, Steuern oder Verkehr…",
  send: "Fragen",
  examplesTitle: "Beispiele",
  examples: [
    "Wie hoch darf das Mietzinsdepot höchstens sein?",
    "Welche Kündigungsfrist gilt während der Probezeit?",
    "Darf mir während einer Krankheit gekündigt werden?",
    "Bis wann muss ich mich nach dem Zuzug in die Schweiz krankenversichern?",
    "Wie viele Jahre Aufenthalt brauche ich für die Einbürgerung?",
    "Wie lange darf ich mit meinem ausländischen Führerausweis fahren?",
  ],
  steps: {
    search: "Suche im Gesetz",
    resolve: "Prüfe ein Zitat",
    read: "Lese",
    browse: "Blättere im Erlass",
    check: "Prüfe die Zitate erneut",
  },
  thinking: "In Arbeit…",
  slowHint: "Antworten dauern meist 30–90 Sekunden: Jedes Zitat wird am Gesetzestext überprüft.",
  sources: "Quellen",
  asOf: "Stand",
  paragraph: "Abs.",
  letter: "Bst.",
  openArticle: "Artikeltext anzeigen",
  quoteRemoved: "Zitat entfernt: Es liess sich nicht am Gesetzestext überprüfen.",
  cantonal: "Kantonale und kommunale Regeln",
  clarify: "Für eine genaue Antwort muss ich wissen",
  followUps: "Sie könnten auch fragen",
  outOfScope: "Ausserhalb dessen, was dieses Werkzeug beantworten kann",
  confidence: { high: "Hohe Sicherheit", medium: "Mittlere Sicherheit", low: "Geringe Sicherheit" },
  verification: {
    passed: "Alle Zitate überprüft",
    passed_after_retry: "Zitate nach einer Korrektur überprüft",
    degraded: "Einige Zitate liessen sich nicht überprüfen und wurden entfernt",
    unavailable: "Zitate konnten nicht geprüft werden",
  },
  helpful: "Hilfreich",
  notHelpful: "Nicht hilfreich",
  thanks: "Danke für die Rückmeldung.",
  quotaLeft: (n, of) => `Heute noch ${n} von ${of} Fragen`,
  quotaUser: "Sie haben das heutige Fragenlimit erreicht. Bitte kommen Sie morgen wieder.",
  quotaGlobal: "Die Demo hat ihr Tageslimit erreicht. Bitte kommen Sie morgen wieder.",
  errorGeneric: "Die Antwort konnte nicht fertiggestellt werden. Bitte versuchen Sie es erneut.",
  errorNetwork: "Die Verbindung wurde unterbrochen. Bitte versuchen Sie es erneut.",
  close: "Schliessen",
  authoritative: "massgebend",
  unofficialTranslation: "inoffizielle Übersetzung",
  machineTranslation: "Maschinelle Übersetzung (inoffiziell)",
  onFedlex: "Auf Fedlex öffnen",
  repealed: "Nicht in Kraft",
  loading: "Wird geladen…",
  articleError: "Der Artikel konnte nicht geladen werden.",
  fallback: "In dieser Sprache nicht verfügbar; angezeigt wird Deutsch.",
  you: "Sie",
  assistant: "Navigator",
};

const fr: Strings = {
  tagline: "Questions sur le droit fédéral suisse, avec réponses fondées sur des articles cités.",
  notice: "Non officiel. Pas un conseil juridique.",
  noticeLong:
    "Outil non officiel. Pas un conseil juridique. Sources : Fedlex (fedlex.admin.ch). Pour toute décision, adressez-vous à l'autorité compétente ou à un avocat.",
  language: "Langue",
  newChat: "Nouvelle conversation",
  logout: "Se déconnecter",
  loginTitle: "Saisir le code d'accès",
  loginHelp: "Cette démo est accessible sur invitation afin d'en limiter les coûts.",
  accessCode: "Code d'accès",
  enter: "Continuer",
  wrongCode: "Ce code n'est pas valable.",
  tooManyAttempts: "Trop de tentatives. Veuillez patienter quelques minutes.",
  askPlaceholder:
    "Questions sur le séjour, le travail, les assurances sociales, le logement, les impôts ou la circulation…",
  send: "Demander",
  examplesTitle: "Exemples",
  examples: [
    "Quel montant de garantie de loyer le bailleur peut-il exiger ?",
    "Quel est le délai de congé pendant le temps d'essai ?",
    "Puis-je être licencié pendant une maladie ?",
    "Dans quel délai dois-je m'assurer pour les soins après mon arrivée en Suisse ?",
    "Combien d'années de séjour faut-il pour demander la naturalisation ?",
    "Combien de temps puis-je conduire avec mon permis étranger ?",
  ],
  steps: {
    search: "Recherche dans la loi",
    resolve: "Vérification d'une référence",
    read: "Lecture de",
    browse: "Parcours de l'acte",
    check: "Nouvelle vérification des citations",
  },
  thinking: "En cours…",
  slowHint:
    "Une réponse prend en général 30 à 90 secondes : chaque citation est vérifiée dans le texte de loi.",
  sources: "Sources",
  asOf: "état au",
  paragraph: "al.",
  letter: "let.",
  openArticle: "Afficher le texte de l'article",
  quoteRemoved: "Citation retirée : elle n'a pas pu être vérifiée dans le texte de loi.",
  cantonal: "Règles cantonales et communales",
  clarify: "Pour répondre précisément, j'ai besoin de savoir",
  followUps: "Vous pourriez aussi demander",
  outOfScope: "Hors du champ de cet outil",
  confidence: { high: "Confiance élevée", medium: "Confiance moyenne", low: "Confiance faible" },
  verification: {
    passed: "Toutes les citations vérifiées",
    passed_after_retry: "Citations vérifiées après une correction",
    degraded: "Certaines citations n'ont pas pu être vérifiées et ont été retirées",
    unavailable: "Les citations n'ont pas pu être vérifiées",
  },
  helpful: "Utile",
  notHelpful: "Pas utile",
  thanks: "Merci pour votre retour.",
  quotaLeft: (n, of) => `Encore ${n} questions sur ${of} aujourd'hui`,
  quotaUser: "Vous avez atteint la limite de questions du jour. Revenez demain.",
  quotaGlobal: "La démo a atteint sa limite du jour. Revenez demain.",
  errorGeneric: "La réponse n'a pas pu être terminée. Veuillez réessayer.",
  errorNetwork: "La connexion a été interrompue. Veuillez réessayer.",
  close: "Fermer",
  authoritative: "fait foi",
  unofficialTranslation: "traduction non officielle",
  machineTranslation: "Traduction automatique (non officielle)",
  onFedlex: "Ouvrir sur Fedlex",
  repealed: "Pas en vigueur",
  loading: "Chargement…",
  articleError: "L'article n'a pas pu être chargé.",
  fallback: "Pas disponible dans cette langue ; affichage en allemand.",
  you: "Vous",
  assistant: "Navigator",
};

const it: Strings = {
  tagline: "Domande sul diritto federale svizzero, con risposte basate su articoli citati.",
  notice: "Non ufficiale. Non è una consulenza legale.",
  noticeLong:
    "Strumento non ufficiale. Non è una consulenza legale. Fonti: Fedlex (fedlex.admin.ch). Per le decisioni rivolgersi all'autorità competente o a un avvocato.",
  language: "Lingua",
  newChat: "Nuova conversazione",
  logout: "Esci",
  loginTitle: "Inserire il codice d'accesso",
  loginHelp: "Questa demo è accessibile solo su invito, per contenerne i costi.",
  accessCode: "Codice d'accesso",
  enter: "Continua",
  wrongCode: "Questo codice non è valido.",
  tooManyAttempts: "Troppi tentativi. Attendere qualche minuto.",
  askPlaceholder:
    "Domande su soggiorno, lavoro, assicurazioni sociali, alloggio, imposte o circolazione…",
  send: "Chiedi",
  examplesTitle: "Esempi",
  examples: [
    "A quanto può ammontare al massimo la garanzia per la pigione?",
    "Qual è il termine di disdetta durante il periodo di prova?",
    "Posso essere licenziato mentre sono malato?",
    "Entro quando devo assicurarmi contro le malattie dopo essermi trasferito in Svizzera?",
    "Quanti anni di residenza servono per chiedere la naturalizzazione?",
    "Per quanto tempo posso guidare con la mia licenza di condurre estera?",
  ],
  steps: {
    search: "Ricerca nella legge",
    resolve: "Verifica di un riferimento",
    read: "Lettura di",
    browse: "Consultazione dell'atto",
    check: "Nuova verifica delle citazioni",
  },
  thinking: "In corso…",
  slowHint:
    "Una risposta richiede di solito 30–90 secondi: ogni citazione viene verificata nel testo di legge.",
  sources: "Fonti",
  asOf: "stato al",
  paragraph: "cpv.",
  letter: "lett.",
  openArticle: "Mostra il testo dell'articolo",
  quoteRemoved: "Citazione rimossa: non è stato possibile verificarla nel testo di legge.",
  cantonal: "Norme cantonali e comunali",
  clarify: "Per rispondere con precisione devo sapere",
  followUps: "Potrebbe anche chiedere",
  outOfScope: "Al di fuori di ciò a cui questo strumento può rispondere",
  confidence: {
    high: "Affidabilità alta",
    medium: "Affidabilità media",
    low: "Affidabilità bassa",
  },
  verification: {
    passed: "Tutte le citazioni verificate",
    passed_after_retry: "Citazioni verificate dopo una correzione",
    degraded: "Alcune citazioni non sono state verificate e sono state rimosse",
    unavailable: "Non è stato possibile verificare le citazioni",
  },
  helpful: "Utile",
  notHelpful: "Non utile",
  thanks: "Grazie per il riscontro.",
  quotaLeft: (n, of) => `Ancora ${n} domande su ${of} oggi`,
  quotaUser: "Ha raggiunto il limite di domande di oggi. Torni domani.",
  quotaGlobal: "La demo ha raggiunto il limite giornaliero. Torni domani.",
  errorGeneric: "Non è stato possibile completare la risposta. Riprovi.",
  errorNetwork: "La connessione si è interrotta. Riprovi.",
  close: "Chiudi",
  authoritative: "fa fede",
  unofficialTranslation: "traduzione non ufficiale",
  machineTranslation: "Traduzione automatica (non ufficiale)",
  onFedlex: "Apri su Fedlex",
  repealed: "Non in vigore",
  loading: "Caricamento…",
  articleError: "Non è stato possibile caricare l'articolo.",
  fallback: "Non disponibile in questa lingua; viene mostrato il tedesco.",
  you: "Lei",
  assistant: "Navigator",
};

export const STRINGS: Record<Lang, Strings> = { en, de, fr, it };

export const LANG_NAMES: Record<Lang, string> = {
  en: "English",
  de: "Deutsch",
  fr: "Français",
  it: "Italiano",
};

/** The UI language from a saved choice, else the browser's Accept-Language. */
export function pickLang(saved: string | undefined, acceptLanguage: string | null): Lang {
  if (saved === "en" || saved === "de" || saved === "fr" || saved === "it") return saved;
  for (const part of (acceptLanguage ?? "").split(",")) {
    const code = part.trim().slice(0, 2).toLowerCase();
    if (code === "en" || code === "de" || code === "fr" || code === "it") return code;
  }
  return "en";
}

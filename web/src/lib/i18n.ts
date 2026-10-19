// UI strings in EN/DE/FR/IT. The answer language follows the question (the agent
// detects it); the switcher only changes the interface and the examples.

import type { Lang, Step } from "@/lib/contract";

/** The legal domain an example question belongs to (its tag on the card). */
export type Domain = "housing" | "work" | "social" | "residence" | "mobility" | "tax";

export interface Strings {
  tagline: string;
  notice: string;
  noticeSources: string;
  details: string;
  language: string;
  account: string;
  more: string;
  newChat: string;
  logout: string;
  loginTitle: string;
  loginHelp: string;
  accessCode: string;
  enter: string;
  checking: string;
  wrongCode: string;
  tooManyAttempts: string;
  whatThisIs: string;
  points: { title: string; body: string }[];
  heroTitle: string;
  heroSub: string;
  examplesTitle: string;
  examples: { domain: Domain; q: string }[];
  domains: Record<Domain, string>;
  yourQuestion: string;
  askPlaceholder: string;
  followUpPlaceholder: string;
  waitPlaceholder: string;
  quotaPlaceholder: string;
  send: string;
  toSend: string;
  newLine: string;
  workTitle: string;
  workSub: string;
  researchSteps: string;
  steps: Record<Step, string>;
  stepWriting: string;
  elapsed: (seconds: number) => string;
  slowHint: string;
  trail: (articles: number, seconds: number, corrections: number) => string;
  answer: string;
  sources: string;
  asOf: string;
  seal: (verified: number, total: number) => string;
  sealPartial: (verified: number, total: number, removed: number) => string;
  verified: string;
  paragraph: string;
  letter: string;
  source: (ref: string, label: string) => string;
  openArticle: string;
  showMore: string;
  showMoreTranslation: string;
  showLess: string;
  quoteRemoved: string;
  quoteRemovedHint: string;
  cantonal: string;
  clarify: string;
  replyBelow: string;
  followUps: string;
  outOfScope: string;
  confidence: Record<"high" | "medium" | "low", string>;
  verification: Record<"passed" | "passed_after_retry" | "degraded" | "unavailable", string>;
  helpful: string;
  notHelpful: string;
  thanks: string;
  quotaLeft: (n: number, of: number) => string;
  quotaTitle: string;
  quotaUser: string;
  quotaGlobal: string;
  errorTitle: string;
  networkTitle: string;
  errorGeneric: string;
  errorNetwork: string;
  tryAgain: string;
  close: string;
  closeArticle: string;
  citedAs: (ref: string) => string;
  citedInAnswer: (ref: string) => string;
  lawTextLang: string;
  positionInAct: string;
  showPath: string;
  authoritative: string;
  authoritativeTitle: string;
  unofficialTranslation: string;
  unofficialTitle: string;
  onlyAuthoritative: string;
  englishNote: string;
  machineTranslation: string;
  onFedlex: string;
  newTab: string;
  repealed: string;
  loading: string;
  articleError: string;
  fallback: string;
  you: string;
  assistant: string;
  memory: string;
  memoryOn: string;
  memoryOff: string;
  memoryIntro: string;
  memorySwitch: string;
  memoryRestart: string;
  rememberTitle: string;
  rememberEmpty: string;
  rememberDelay: string;
  keepTitle: string;
  keepList: string[];
  neverTitle: string;
  neverList: string[];
  memoryExpiry: string;
  forget: string;
  forgetConfirm: string;
  forgotten: string;
  deleting: string;
  cancel: string;
  done: string;
  memoryError: string;
}

const en: Strings = {
  tagline: "Questions about Swiss federal law, answered with quoted articles.",
  notice: "Unofficial. Not legal advice.",
  noticeSources:
    "Sources: Fedlex (fedlex.admin.ch). For decisions, contact the competent authority or a lawyer.",
  details: "Details",
  language: "Language",
  account: "Account",
  more: "More",
  newChat: "New conversation",
  logout: "Sign out",
  loginTitle: "Enter access code",
  loginHelp: "This demo is invite-only to keep its costs bounded.",
  accessCode: "Access code",
  enter: "Continue",
  checking: "Checking…",
  wrongCode: "That code is not valid.",
  tooManyAttempts: "Too many attempts. Please wait a few minutes.",
  whatThisIs: "What this is",
  points: [
    {
      title: "Every quote is checked against the law text",
      body: "Quotes that can't be verified are removed before you see the answer.",
    },
    {
      title: "Ask in English, Deutsch, Français or Italiano",
      body: "Answers come back in your language; quotes stay in the original.",
    },
    {
      title: "23 federal acts from Fedlex",
      body: "Residence, work, social insurance, housing, tax and mobility.",
    },
  ],
  heroTitle: "What would you like to know about Swiss federal law?",
  heroSub:
    "Every answer quotes the articles it relies on. Each quote is checked against the law text before you see it.",
  examplesTitle: "Try one of these",
  examples: [
    { domain: "housing", q: "How much rent deposit can my landlord ask for?" },
    { domain: "work", q: "What is the notice period during probation?" },
    { domain: "work", q: "Can I be dismissed while I am ill?" },
    {
      domain: "social",
      q: "How long do I have to take out health insurance after moving to Switzerland?",
    },
    {
      domain: "residence",
      q: "How many years of residence do I need to apply for Swiss citizenship?",
    },
    { domain: "mobility", q: "Until when can I drive with my foreign driving licence?" },
  ],
  domains: {
    housing: "Housing",
    work: "Work",
    social: "Social insurance",
    residence: "Residence",
    mobility: "Mobility",
    tax: "Tax",
  },
  yourQuestion: "Your question",
  askPlaceholder: "Ask about residence, work, social insurance, housing, tax or mobility…",
  followUpPlaceholder: "Ask a follow-up…",
  waitPlaceholder: "Wait for the current answer…",
  quotaPlaceholder: "Available again tomorrow",
  send: "Ask",
  toSend: "to send",
  newLine: "new line",
  workTitle: "Researching your question",
  workSub: "Finding the articles, then checking every quote",
  researchSteps: "Research steps",
  steps: {
    search: "Searching the law",
    resolve: "Checking a citation",
    read: "Reading",
    browse: "Browsing the act",
    check: "Re-checking the quotes",
  },
  stepWriting: "Writing the answer and checking every quote",
  elapsed: (n) => `${n} seconds elapsed`,
  slowHint: "Answers usually take 30–90 seconds: every quote is checked against the law text.",
  trail: (a, s, c) =>
    `${a ? `Checked ${a} article${a === 1 ? "" : "s"} in ${s} s` : `Answered in ${s} s`}${
      c ? ` · ${c} correction${c === 1 ? "" : "s"}` : ""
    }`,
  answer: "Answer",
  sources: "Sources",
  asOf: "as of",
  seal: (v, t) => `${v} of ${t} quote${t === 1 ? "" : "s"} checked against the law text`,
  sealPartial: (v, t, r) => `${v} of ${t} quotes verified · ${r} removed`,
  verified: "Verified",
  paragraph: "para.",
  letter: "let.",
  source: (ref, label) => `Source ${ref}: ${label}`,
  openArticle: "Open article",
  showMore: "Show more",
  showMoreTranslation: "Show more and translation",
  showLess: "Show less",
  quoteRemoved: "Quote removed: it could not be verified against the law text.",
  quoteRemovedHint: "Open the article to read it yourself.",
  cantonal: "Cantonal and communal rules",
  clarify: "To answer precisely, I need to know",
  replyBelow: "Reply in the box below.",
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
  quotaTitle: "Daily limit reached",
  quotaUser: "You have reached today's question limit. Please come back tomorrow.",
  quotaGlobal: "The demo has reached its daily limit. Please come back tomorrow.",
  errorTitle: "Answer not finished",
  networkTitle: "Connection lost",
  errorGeneric: "The assistant could not finish this answer. Please try again.",
  errorNetwork: "The connection was interrupted. Please try again.",
  tryAgain: "Try again",
  close: "Close",
  closeArticle: "Close article",
  citedAs: (ref) => `Cited as [${ref}]`,
  citedInAnswer: (ref) => `Cited in the answer [${ref}]`,
  lawTextLang: "Language of the law text",
  positionInAct: "Position in the act",
  showPath: "Show full path",
  authoritative: "authoritative",
  authoritativeTitle: "Authoritative",
  unofficialTranslation: "unofficial translation",
  unofficialTitle: "Unofficial translation",
  onlyAuthoritative: "Only DE, FR and IT are authoritative.",
  englishNote: "English versions are unofficial translations and don't exist for every act.",
  machineTranslation: "Machine translation (unofficial)",
  onFedlex: "Open on Fedlex",
  newTab: "(opens in a new tab)",
  repealed: "Not in force",
  loading: "Loading…",
  articleError: "The article could not be loaded.",
  fallback: "Not available in this language; showing German.",
  you: "You",
  assistant: "Navigator",
  memory: "Memory",
  memoryOn: "on",
  memoryOff: "off",
  memoryIntro:
    "If you turn memory on, the assistant remembers a few facts about your situation between conversations, so it doesn't have to ask again.",
  memorySwitch: "Remember facts about my situation",
  memoryRestart: "Changing this starts a new conversation.",
  rememberTitle: "What I remember",
  rememberEmpty: "Nothing yet.",
  rememberDelay: "New facts can take a minute to appear.",
  keepTitle: "What it may keep",
  keepList: [
    "Canton and municipality",
    "Preferred language",
    "Nationality group (Swiss, EU/EFTA, other)",
    "Permit (L, B, C, Ci, G)",
    "Work status, civil status, children",
  ],
  neverTitle: "What it never keeps",
  neverList: [
    "Health",
    "Criminal matters",
    "Money or bank details",
    "Religion",
    "Names, addresses or contact details",
  ],
  memoryExpiry: "Memories expire after 30 days. Signing out deletes them.",
  forget: "Forget me",
  forgetConfirm: "Delete everything remembered about you and end your conversations?",
  forgotten: "Done. Nothing about you is remembered.",
  deleting: "Deleting…",
  cancel: "Cancel",
  done: "Done",
  memoryError: "Memory is not available right now. Please try again.",
};

const de: Strings = {
  tagline: "Fragen zum Schweizer Bundesrecht, beantwortet mit zitierten Artikeln.",
  notice: "Inoffiziell. Keine Rechtsberatung.",
  noticeSources:
    "Quellen: Fedlex (fedlex.admin.ch). Für Entscheide wenden Sie sich an die zuständige Behörde oder eine Anwältin bzw. einen Anwalt.",
  details: "Details",
  language: "Sprache",
  account: "Konto",
  more: "Mehr",
  newChat: "Neues Gespräch",
  logout: "Abmelden",
  loginTitle: "Zugangscode eingeben",
  loginHelp: "Diese Demo ist nur auf Einladung zugänglich, damit die Kosten begrenzt bleiben.",
  accessCode: "Zugangscode",
  enter: "Weiter",
  checking: "Wird geprüft…",
  wrongCode: "Dieser Code ist ungültig.",
  tooManyAttempts: "Zu viele Versuche. Bitte warten Sie einige Minuten.",
  whatThisIs: "Worum es geht",
  points: [
    {
      title: "Jedes Zitat wird am Gesetzestext geprüft",
      body: "Zitate, die sich nicht überprüfen lassen, werden entfernt, bevor Sie die Antwort sehen.",
    },
    {
      title: "Fragen auf English, Deutsch, Français oder Italiano",
      body: "Die Antwort kommt in Ihrer Sprache; Zitate bleiben im Original.",
    },
    {
      title: "23 Bundeserlasse aus Fedlex",
      body: "Aufenthalt, Arbeit, Sozialversicherungen, Wohnen, Steuern und Verkehr.",
    },
  ],
  heroTitle: "Was möchten Sie über das Schweizer Bundesrecht wissen?",
  heroSub:
    "Jede Antwort zitiert die Artikel, auf die sie sich stützt. Jedes Zitat wird am Gesetzestext geprüft, bevor Sie es sehen.",
  examplesTitle: "Probieren Sie eine dieser Fragen",
  examples: [
    { domain: "housing", q: "Wie hoch darf das Mietzinsdepot höchstens sein?" },
    { domain: "work", q: "Welche Kündigungsfrist gilt während der Probezeit?" },
    { domain: "work", q: "Darf mir während einer Krankheit gekündigt werden?" },
    {
      domain: "social",
      q: "Bis wann muss ich mich nach dem Zuzug in die Schweiz krankenversichern?",
    },
    { domain: "residence", q: "Wie viele Jahre Aufenthalt brauche ich für die Einbürgerung?" },
    {
      domain: "mobility",
      q: "Wie lange darf ich mit meinem ausländischen Führerausweis fahren?",
    },
  ],
  domains: {
    housing: "Wohnen",
    work: "Arbeit",
    social: "Sozialversicherungen",
    residence: "Aufenthalt",
    mobility: "Verkehr",
    tax: "Steuern",
  },
  yourQuestion: "Ihre Frage",
  askPlaceholder: "Fragen zu Aufenthalt, Arbeit, Sozialversicherung, Wohnen, Steuern oder Verkehr…",
  followUpPlaceholder: "Nachfrage stellen…",
  waitPlaceholder: "Warten Sie auf die aktuelle Antwort…",
  quotaPlaceholder: "Morgen wieder verfügbar",
  send: "Fragen",
  toSend: "zum Senden",
  newLine: "neue Zeile",
  workTitle: "Ihre Frage wird recherchiert",
  workSub: "Artikel finden, dann jedes Zitat prüfen",
  researchSteps: "Rechercheschritte",
  steps: {
    search: "Suche im Gesetz",
    resolve: "Prüfe ein Zitat",
    read: "Lese",
    browse: "Blättere im Erlass",
    check: "Prüfe die Zitate erneut",
  },
  stepWriting: "Antwort schreiben und jedes Zitat prüfen",
  elapsed: (n) => `${n} Sekunden vergangen`,
  slowHint: "Antworten dauern meist 30–90 Sekunden: Jedes Zitat wird am Gesetzestext überprüft.",
  trail: (a, s, c) =>
    `${a ? `${a} Artikel in ${s} s geprüft` : `In ${s} s beantwortet`}${
      c ? ` · ${c} Korrektur${c === 1 ? "" : "en"}` : ""
    }`,
  answer: "Antwort",
  sources: "Quellen",
  asOf: "Stand",
  seal: (v, t) => `${v} von ${t} ${t === 1 ? "Zitat" : "Zitaten"} am Gesetzestext geprüft`,
  sealPartial: (v, t, r) => `${v} von ${t} Zitaten geprüft · ${r} entfernt`,
  verified: "Geprüft",
  paragraph: "Abs.",
  letter: "Bst.",
  source: (ref, label) => `Quelle ${ref}: ${label}`,
  openArticle: "Artikel öffnen",
  showMore: "Mehr anzeigen",
  showMoreTranslation: "Mehr und Übersetzung anzeigen",
  showLess: "Weniger anzeigen",
  quoteRemoved: "Zitat entfernt: Es liess sich nicht am Gesetzestext überprüfen.",
  quoteRemovedHint: "Öffnen Sie den Artikel, um ihn selbst zu lesen.",
  cantonal: "Kantonale und kommunale Regeln",
  clarify: "Für eine genaue Antwort muss ich wissen",
  replyBelow: "Antworten Sie im Feld unten.",
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
  quotaTitle: "Tageslimit erreicht",
  quotaUser: "Sie haben das heutige Fragenlimit erreicht. Bitte kommen Sie morgen wieder.",
  quotaGlobal: "Die Demo hat ihr Tageslimit erreicht. Bitte kommen Sie morgen wieder.",
  errorTitle: "Antwort nicht fertig",
  networkTitle: "Verbindung unterbrochen",
  errorGeneric: "Die Antwort konnte nicht fertiggestellt werden. Bitte versuchen Sie es erneut.",
  errorNetwork: "Die Verbindung wurde unterbrochen. Bitte versuchen Sie es erneut.",
  tryAgain: "Erneut versuchen",
  close: "Schliessen",
  closeArticle: "Artikel schliessen",
  citedAs: (ref) => `Zitiert als [${ref}]`,
  citedInAnswer: (ref) => `In der Antwort zitiert [${ref}]`,
  lawTextLang: "Sprache des Gesetzestexts",
  positionInAct: "Stelle im Erlass",
  showPath: "Ganzen Pfad anzeigen",
  authoritative: "massgebend",
  authoritativeTitle: "Massgebend",
  unofficialTranslation: "inoffizielle Übersetzung",
  unofficialTitle: "Inoffizielle Übersetzung",
  onlyAuthoritative: "Massgebend sind nur DE, FR und IT.",
  englishNote:
    "Englische Fassungen sind inoffizielle Übersetzungen und gibt es nicht für jeden Erlass.",
  machineTranslation: "Maschinelle Übersetzung (inoffiziell)",
  onFedlex: "Auf Fedlex öffnen",
  newTab: "(öffnet in neuem Tab)",
  repealed: "Nicht in Kraft",
  loading: "Wird geladen…",
  articleError: "Der Artikel konnte nicht geladen werden.",
  fallback: "In dieser Sprache nicht verfügbar; angezeigt wird Deutsch.",
  you: "Sie",
  assistant: "Navigator",
  memory: "Gedächtnis",
  memoryOn: "an",
  memoryOff: "aus",
  memoryIntro:
    "Wenn Sie das Gedächtnis einschalten, merkt sich der Assistent einige Angaben zu Ihrer Situation über Gespräche hinweg und muss nicht erneut fragen.",
  memorySwitch: "Angaben zu meiner Situation merken",
  memoryRestart: "Eine Änderung startet ein neues Gespräch.",
  rememberTitle: "Was ich mir merke",
  rememberEmpty: "Noch nichts.",
  rememberDelay: "Neue Angaben können eine Minute brauchen, bis sie erscheinen.",
  keepTitle: "Was gespeichert werden darf",
  keepList: [
    "Kanton und Gemeinde",
    "Bevorzugte Sprache",
    "Staatsangehörigkeit als Gruppe (Schweiz, EU/EFTA, Drittstaat)",
    "Bewilligung (L, B, C, Ci, G)",
    "Erwerbsstatus, Zivilstand, Kinder",
  ],
  neverTitle: "Was nie gespeichert wird",
  neverList: [
    "Gesundheit",
    "Strafsachen",
    "Geld oder Bankangaben",
    "Religion",
    "Namen, Adressen oder Kontaktdaten",
  ],
  memoryExpiry: "Gespeichertes verfällt nach 30 Tagen. Abmelden löscht es.",
  forget: "Alles vergessen",
  forgetConfirm: "Alles über Sie Gespeicherte löschen und Ihre Gespräche beenden?",
  forgotten: "Erledigt. Über Sie ist nichts mehr gespeichert.",
  deleting: "Wird gelöscht…",
  cancel: "Abbrechen",
  done: "Fertig",
  memoryError: "Das Gedächtnis ist gerade nicht verfügbar. Bitte versuchen Sie es erneut.",
};

const fr: Strings = {
  tagline: "Questions sur le droit fédéral suisse, avec réponses fondées sur des articles cités.",
  notice: "Non officiel. Pas un conseil juridique.",
  noticeSources:
    "Sources : Fedlex (fedlex.admin.ch). Pour toute décision, adressez-vous à l'autorité compétente ou à un avocat.",
  details: "Détails",
  language: "Langue",
  account: "Compte",
  more: "Plus",
  newChat: "Nouvelle conversation",
  logout: "Se déconnecter",
  loginTitle: "Saisir le code d'accès",
  loginHelp: "Cette démo est accessible sur invitation afin d'en limiter les coûts.",
  accessCode: "Code d'accès",
  enter: "Continuer",
  checking: "Vérification…",
  wrongCode: "Ce code n'est pas valable.",
  tooManyAttempts: "Trop de tentatives. Veuillez patienter quelques minutes.",
  whatThisIs: "De quoi il s'agit",
  points: [
    {
      title: "Chaque citation est vérifiée dans le texte de loi",
      body: "Les citations qui ne peuvent pas être vérifiées sont retirées avant que vous ne voyiez la réponse.",
    },
    {
      title: "Posez vos questions en English, Deutsch, Français ou Italiano",
      body: "La réponse arrive dans votre langue ; les citations restent dans l'original.",
    },
    {
      title: "23 actes fédéraux issus de Fedlex",
      body: "Séjour, travail, assurances sociales, logement, impôts et mobilité.",
    },
  ],
  heroTitle: "Que voulez-vous savoir sur le droit fédéral suisse ?",
  heroSub:
    "Chaque réponse cite les articles sur lesquels elle s'appuie. Chaque citation est vérifiée dans le texte de loi avant de vous être montrée.",
  examplesTitle: "Essayez l'une de ces questions",
  examples: [
    { domain: "housing", q: "Quel montant de garantie de loyer le bailleur peut-il exiger ?" },
    { domain: "work", q: "Quel est le délai de congé pendant le temps d'essai ?" },
    { domain: "work", q: "Puis-je être licencié pendant une maladie ?" },
    {
      domain: "social",
      q: "Dans quel délai dois-je m'assurer pour les soins après mon arrivée en Suisse ?",
    },
    {
      domain: "residence",
      q: "Combien d'années de séjour faut-il pour demander la naturalisation ?",
    },
    { domain: "mobility", q: "Combien de temps puis-je conduire avec mon permis étranger ?" },
  ],
  domains: {
    housing: "Logement",
    work: "Travail",
    social: "Assurances sociales",
    residence: "Séjour",
    mobility: "Mobilité",
    tax: "Impôts",
  },
  yourQuestion: "Votre question",
  askPlaceholder:
    "Questions sur le séjour, le travail, les assurances sociales, le logement, les impôts ou la circulation…",
  followUpPlaceholder: "Poser une question de suivi…",
  waitPlaceholder: "Attendez la réponse en cours…",
  quotaPlaceholder: "De nouveau disponible demain",
  send: "Demander",
  toSend: "pour envoyer",
  newLine: "nouvelle ligne",
  workTitle: "Recherche en cours",
  workSub: "Trouver les articles, puis vérifier chaque citation",
  researchSteps: "Étapes de recherche",
  steps: {
    search: "Recherche dans la loi",
    resolve: "Vérification d'une référence",
    read: "Lecture de",
    browse: "Parcours de l'acte",
    check: "Nouvelle vérification des citations",
  },
  stepWriting: "Rédaction de la réponse et vérification de chaque citation",
  elapsed: (n) => `${n} secondes écoulées`,
  slowHint:
    "Une réponse prend en général 30 à 90 secondes : chaque citation est vérifiée dans le texte de loi.",
  trail: (a, s, c) =>
    `${a ? `${a} article${a === 1 ? "" : "s"} vérifié${a === 1 ? "" : "s"} en ${s} s` : `Réponse en ${s} s`}${
      c ? ` · ${c} correction${c === 1 ? "" : "s"}` : ""
    }`,
  answer: "Réponse",
  sources: "Sources",
  asOf: "état au",
  seal: (v, t) =>
    `${v} citation${v === 1 ? "" : "s"} sur ${t} vérifiée${v === 1 ? "" : "s"} dans le texte de loi`,
  sealPartial: (v, t, r) =>
    `${v} citation${v === 1 ? "" : "s"} sur ${t} vérifiée${v === 1 ? "" : "s"} · ${r} retirée${r === 1 ? "" : "s"}`,
  verified: "Vérifiée",
  paragraph: "al.",
  letter: "let.",
  source: (ref, label) => `Source ${ref} : ${label}`,
  openArticle: "Ouvrir l'article",
  showMore: "Afficher plus",
  showMoreTranslation: "Afficher plus et la traduction",
  showLess: "Afficher moins",
  quoteRemoved: "Citation retirée : elle n'a pas pu être vérifiée dans le texte de loi.",
  quoteRemovedHint: "Ouvrez l'article pour le lire vous-même.",
  cantonal: "Règles cantonales et communales",
  clarify: "Pour répondre précisément, j'ai besoin de savoir",
  replyBelow: "Répondez dans le champ ci-dessous.",
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
  quotaTitle: "Limite du jour atteinte",
  quotaUser: "Vous avez atteint la limite de questions du jour. Revenez demain.",
  quotaGlobal: "La démo a atteint sa limite du jour. Revenez demain.",
  errorTitle: "Réponse inachevée",
  networkTitle: "Connexion perdue",
  errorGeneric: "La réponse n'a pas pu être terminée. Veuillez réessayer.",
  errorNetwork: "La connexion a été interrompue. Veuillez réessayer.",
  tryAgain: "Réessayer",
  close: "Fermer",
  closeArticle: "Fermer l'article",
  citedAs: (ref) => `Cité en [${ref}]`,
  citedInAnswer: (ref) => `Cité dans la réponse [${ref}]`,
  lawTextLang: "Langue du texte de loi",
  positionInAct: "Position dans l'acte",
  showPath: "Afficher le chemin complet",
  authoritative: "fait foi",
  authoritativeTitle: "Fait foi",
  unofficialTranslation: "traduction non officielle",
  unofficialTitle: "Traduction non officielle",
  onlyAuthoritative: "Seuls le DE, le FR et l'IT font foi.",
  englishNote:
    "Les versions anglaises sont des traductions non officielles et n'existent pas pour chaque acte.",
  machineTranslation: "Traduction automatique (non officielle)",
  onFedlex: "Ouvrir sur Fedlex",
  newTab: "(s'ouvre dans un nouvel onglet)",
  repealed: "Pas en vigueur",
  loading: "Chargement…",
  articleError: "L'article n'a pas pu être chargé.",
  fallback: "Pas disponible dans cette langue ; affichage en allemand.",
  you: "Vous",
  assistant: "Navigator",
  memory: "Mémoire",
  memoryOn: "activée",
  memoryOff: "désactivée",
  memoryIntro:
    "Si vous activez la mémoire, l'assistant retient quelques éléments de votre situation d'une conversation à l'autre et n'a pas besoin de vous les redemander.",
  memorySwitch: "Retenir des éléments de ma situation",
  memoryRestart: "Un changement démarre une nouvelle conversation.",
  rememberTitle: "Ce que je retiens",
  rememberEmpty: "Rien pour l'instant.",
  rememberDelay: "Les nouveaux éléments peuvent mettre une minute à apparaître.",
  keepTitle: "Ce qu'il peut retenir",
  keepList: [
    "Canton et commune",
    "Langue préférée",
    "Groupe de nationalité (Suisse, UE/AELE, État tiers)",
    "Permis (L, B, C, Ci, G)",
    "Situation professionnelle, état civil, enfants",
  ],
  neverTitle: "Ce qu'il ne retient jamais",
  neverList: [
    "Santé",
    "Affaires pénales",
    "Argent ou données bancaires",
    "Religion",
    "Noms, adresses ou coordonnées",
  ],
  memoryExpiry: "Les données expirent après 30 jours. La déconnexion les supprime.",
  forget: "Tout oublier",
  forgetConfirm:
    "Supprimer tout ce qui est retenu à votre sujet et mettre fin à vos conversations ?",
  forgotten: "C'est fait. Plus rien n'est retenu à votre sujet.",
  deleting: "Suppression…",
  cancel: "Annuler",
  done: "Terminé",
  memoryError: "La mémoire n'est pas disponible pour le moment. Veuillez réessayer.",
};

const it: Strings = {
  tagline: "Domande sul diritto federale svizzero, con risposte basate su articoli citati.",
  notice: "Non ufficiale. Non è una consulenza legale.",
  noticeSources:
    "Fonti: Fedlex (fedlex.admin.ch). Per le decisioni rivolgersi all'autorità competente o a un avvocato.",
  details: "Dettagli",
  language: "Lingua",
  account: "Account",
  more: "Altro",
  newChat: "Nuova conversazione",
  logout: "Esci",
  loginTitle: "Inserire il codice d'accesso",
  loginHelp: "Questa demo è accessibile solo su invito, per contenerne i costi.",
  accessCode: "Codice d'accesso",
  enter: "Continua",
  checking: "Verifica…",
  wrongCode: "Questo codice non è valido.",
  tooManyAttempts: "Troppi tentativi. Attendere qualche minuto.",
  whatThisIs: "Di che cosa si tratta",
  points: [
    {
      title: "Ogni citazione è verificata nel testo di legge",
      body: "Le citazioni che non si possono verificare vengono rimosse prima che lei veda la risposta.",
    },
    {
      title: "Chieda in English, Deutsch, Français o Italiano",
      body: "La risposta arriva nella sua lingua; le citazioni restano nell'originale.",
    },
    {
      title: "23 atti federali da Fedlex",
      body: "Soggiorno, lavoro, assicurazioni sociali, alloggio, imposte e mobilità.",
    },
  ],
  heroTitle: "Che cosa vuole sapere sul diritto federale svizzero?",
  heroSub:
    "Ogni risposta cita gli articoli su cui si basa. Ogni citazione viene verificata nel testo di legge prima che lei la veda.",
  examplesTitle: "Provi una di queste domande",
  examples: [
    { domain: "housing", q: "A quanto può ammontare al massimo la garanzia per la pigione?" },
    { domain: "work", q: "Qual è il termine di disdetta durante il periodo di prova?" },
    { domain: "work", q: "Posso essere licenziato mentre sono malato?" },
    {
      domain: "social",
      q: "Entro quando devo assicurarmi contro le malattie dopo essermi trasferito in Svizzera?",
    },
    {
      domain: "residence",
      q: "Quanti anni di residenza servono per chiedere la naturalizzazione?",
    },
    {
      domain: "mobility",
      q: "Per quanto tempo posso guidare con la mia licenza di condurre estera?",
    },
  ],
  domains: {
    housing: "Alloggio",
    work: "Lavoro",
    social: "Assicurazioni sociali",
    residence: "Soggiorno",
    mobility: "Mobilità",
    tax: "Imposte",
  },
  yourQuestion: "La sua domanda",
  askPlaceholder:
    "Domande su soggiorno, lavoro, assicurazioni sociali, alloggio, imposte o circolazione…",
  followUpPlaceholder: "Fare una domanda di seguito…",
  waitPlaceholder: "Attenda la risposta in corso…",
  quotaPlaceholder: "Di nuovo disponibile domani",
  send: "Chiedi",
  toSend: "per inviare",
  newLine: "nuova riga",
  workTitle: "Ricerca in corso",
  workSub: "Trovare gli articoli, poi verificare ogni citazione",
  researchSteps: "Passi della ricerca",
  steps: {
    search: "Ricerca nella legge",
    resolve: "Verifica di un riferimento",
    read: "Lettura di",
    browse: "Consultazione dell'atto",
    check: "Nuova verifica delle citazioni",
  },
  stepWriting: "Stesura della risposta e verifica di ogni citazione",
  elapsed: (n) => `${n} secondi trascorsi`,
  slowHint:
    "Una risposta richiede di solito 30–90 secondi: ogni citazione viene verificata nel testo di legge.",
  trail: (a, s, c) =>
    `${a ? `${a} articol${a === 1 ? "o verificato" : "i verificati"} in ${s} s` : `Risposta in ${s} s`}${
      c ? ` · ${c} correzion${c === 1 ? "e" : "i"}` : ""
    }`,
  answer: "Risposta",
  sources: "Fonti",
  asOf: "stato al",
  seal: (v, t) =>
    `${v} citazion${v === 1 ? "e" : "i"} su ${t} verificat${v === 1 ? "a" : "e"} nel testo di legge`,
  sealPartial: (v, t, r) =>
    `${v} citazion${v === 1 ? "e" : "i"} su ${t} verificat${v === 1 ? "a" : "e"} · ${r} rimoss${r === 1 ? "a" : "e"}`,
  verified: "Verificata",
  paragraph: "cpv.",
  letter: "lett.",
  source: (ref, label) => `Fonte ${ref}: ${label}`,
  openArticle: "Apri l'articolo",
  showMore: "Mostra di più",
  showMoreTranslation: "Mostra di più e la traduzione",
  showLess: "Mostra di meno",
  quoteRemoved: "Citazione rimossa: non è stato possibile verificarla nel testo di legge.",
  quoteRemovedHint: "Apra l'articolo per leggerlo di persona.",
  cantonal: "Norme cantonali e comunali",
  clarify: "Per rispondere con precisione devo sapere",
  replyBelow: "Risponda nel campo qui sotto.",
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
  quotaTitle: "Limite giornaliero raggiunto",
  quotaUser: "Ha raggiunto il limite di domande di oggi. Torni domani.",
  quotaGlobal: "La demo ha raggiunto il limite giornaliero. Torni domani.",
  errorTitle: "Risposta non completata",
  networkTitle: "Connessione interrotta",
  errorGeneric: "Non è stato possibile completare la risposta. Riprovi.",
  errorNetwork: "La connessione si è interrotta. Riprovi.",
  tryAgain: "Riprova",
  close: "Chiudi",
  closeArticle: "Chiudi l'articolo",
  citedAs: (ref) => `Citato come [${ref}]`,
  citedInAnswer: (ref) => `Citato nella risposta [${ref}]`,
  lawTextLang: "Lingua del testo di legge",
  positionInAct: "Posizione nell'atto",
  showPath: "Mostra il percorso completo",
  authoritative: "fa fede",
  authoritativeTitle: "Fa fede",
  unofficialTranslation: "traduzione non ufficiale",
  unofficialTitle: "Traduzione non ufficiale",
  onlyAuthoritative: "Fanno fede solo DE, FR e IT.",
  englishNote: "Le versioni inglesi sono traduzioni non ufficiali e non esistono per ogni atto.",
  machineTranslation: "Traduzione automatica (non ufficiale)",
  onFedlex: "Apri su Fedlex",
  newTab: "(si apre in una nuova scheda)",
  repealed: "Non in vigore",
  loading: "Caricamento…",
  articleError: "Non è stato possibile caricare l'articolo.",
  fallback: "Non disponibile in questa lingua; viene mostrato il tedesco.",
  you: "Lei",
  assistant: "Navigator",
  memory: "Memoria",
  memoryOn: "attiva",
  memoryOff: "disattiva",
  memoryIntro:
    "Se attiva la memoria, l'assistente ricorda alcuni dati sulla sua situazione da una conversazione all'altra e non deve chiederli di nuovo.",
  memorySwitch: "Ricorda dati sulla mia situazione",
  memoryRestart: "Una modifica avvia una nuova conversazione.",
  rememberTitle: "Cosa ricordo",
  rememberEmpty: "Ancora niente.",
  rememberDelay: "I nuovi dati possono impiegare un minuto ad apparire.",
  keepTitle: "Cosa può ricordare",
  keepList: [
    "Cantone e comune",
    "Lingua preferita",
    "Gruppo di nazionalità (Svizzera, UE/AELS, Stato terzo)",
    "Permesso (L, B, C, Ci, G)",
    "Situazione lavorativa, stato civile, figli",
  ],
  neverTitle: "Cosa non ricorda mai",
  neverList: [
    "Salute",
    "Questioni penali",
    "Denaro o dati bancari",
    "Religione",
    "Nomi, indirizzi o recapiti",
  ],
  memoryExpiry: "I dati scadono dopo 30 giorni. Uscire li cancella.",
  forget: "Dimentica tutto",
  forgetConfirm:
    "Cancellare tutto ciò che è memorizzato su di lei e chiudere le sue conversazioni?",
  forgotten: "Fatto. Non è memorizzato più nulla su di lei.",
  deleting: "Cancellazione…",
  cancel: "Annulla",
  done: "Fatto",
  memoryError: "La memoria non è disponibile al momento. Riprovi.",
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

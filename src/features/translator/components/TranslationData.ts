export type Language =
  | "English"
  | "French"
  | "German"
  | "Spanish"
  | "Italian"
  | "Hindi";

export const languageCodes: Record<Language, string> = {
  English: "en",
  French: "fr",
  German: "de",
  Spanish: "es",
  Italian: "it",
  Hindi: "hi",
};

export const languages = Object.keys(languageCodes) as Language[];

export const fallbackTranslations: Record<Language, string> = {
  English: "Excuse me, where is the nearest metro station?",
  French: "Excusez-moi, où est la station de métro la plus proche ?",
  German: "Entschuldigung, wo ist die nächste U-Bahn-Station?",
  Spanish: "Disculpe, ¿dónde está la estación de metro más cercana?",
  Italian: "Mi scusi, dov'è la stazione della metro più vicina?",
  Hindi: "Maaf kijiye, sabse nazdeek metro station kahan hai?",
};

export const touristPhrasebook: Record<Language, string>[] = [
  {
    English: "Where is the nearest metro station?",
    French: "Où est la station de métro la plus proche ?",
    German: "Wo ist die nächste U-Bahn-Station?",
    Spanish: "¿Dónde está la estación de metro más cercana?",
    Italian: "Dov'è la stazione della metro più vicina?",
    Hindi: "Sabse nazdeek metro station kahan hai?",
  },
  {
    English: "How much does this cost?",
    French: "Combien ça coûte ?",
    German: "Wie viel kostet das?",
    Spanish: "¿Cuánto cuesta esto?",
    Italian: "Quanto costa questo?",
    Hindi: "Yeh kitne ka hai?",
  },
  {
    English: "Can you help me?",
    French: "Pouvez-vous m'aider ?",
    German: "Können Sie mir helfen?",
    Spanish: "¿Puede ayudarme?",
    Italian: "Può aiutarmi?",
    Hindi: "Kya aap meri madad kar sakte hain?",
  },
  {
    English: "I need directions to my hotel.",
    French: "J'ai besoin d'indications pour mon hôtel.",
    German: "Ich brauche eine Wegbeschreibung zu meinem Hotel.",
    Spanish: "Necesito indicaciones para llegar a mi hotel.",
    Italian: "Ho bisogno di indicazioni per il mio hotel.",
    Hindi: "Mujhe apne hotel ka raasta chahiye.",
  },
  {
    English: "Where is the airport?",
    French: "Où est l'aéroport ?",
    German: "Wo ist der Flughafen?",
    Spanish: "¿Dónde está el aeropuerto?",
    Italian: "Dov'è l'aeroporto?",
    Hindi: "Airport kahan hai?",
  },
  {
    English: "I would like to order food.",
    French: "Je voudrais commander à manger.",
    German: "Ich möchte Essen bestellen.",
    Spanish: "Me gustaría pedir comida.",
    Italian: "Vorrei ordinare del cibo.",
    Hindi: "Main khana order karna chahta hoon.",
  },
];